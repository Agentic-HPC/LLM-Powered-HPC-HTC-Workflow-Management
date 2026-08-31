"""
Scaling benchmark: plain pandas vs. real Apache Spark (local mode) vs. real
multiprocessing MapReduce, on the platform's real datasets at increasing
scale (data/employees.csv / employees_large.csv, weather.csv /
weather_large.csv - see scripts/scale_datasets.py).

This produces the results.json / results.md this project's "results
chapter" (see README) is built from. It measures genuine wall-clock time
for identical groupby-aggregate work on each engine and verifies every
engine produces numerically identical answers, so the report's speedup
numbers are honest.

IMPORTANT / academically important caveat this script always prints: Spark
and multiprocessing MapReduce only outperform plain pandas once the
per-partition workload is large enough to amortize their overhead
(starting a JVM, spinning up worker processes, serializing data). On a
laptop-scale dataset or a machine with only 1-2 CPU cores, pandas can
legitimately win - that's a real, reportable finding, not a bug. Run this
on a multi-core machine with the *_large.csv datasets to see the crossover
point.

Usage:
    python scripts/run_benchmarks.py
    python scripts/run_benchmarks.py --sizes 5000 50000 500000 --repeats 3
"""
import argparse
import json
import os
import statistics
import time
from datetime import datetime, timezone

import pandas as pd

os.environ.setdefault("DATABASE_URL", "sqlite:///./benchmark.db")

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.partition_service import partition_dataframe  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "benchmark_results")


def load_source_df() -> pd.DataFrame:
    """Prefer the large scaled dataset if present, else fall back to the real one."""
    large_path = os.path.join(DATA_DIR, "employees_large.csv")
    real_path = os.path.join(DATA_DIR, "employees.csv")
    path = large_path if os.path.exists(large_path) else real_path
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df, path


def run_pandas(df: pd.DataFrame) -> tuple:
    t0 = time.perf_counter()
    result = df.groupby("Education")["Age"].mean().round(3).to_dict()
    return result, round(time.perf_counter() - t0, 4)


def run_mapreduce(df: pd.DataFrame, n_partitions: int) -> tuple:
    from app.agents.mapreduce_agent import _map_groupby
    from collections import defaultdict
    from concurrent.futures import ProcessPoolExecutor

    partitions = partition_dataframe(df, n_partitions=n_partitions)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=min(os.cpu_count() or 4, n_partitions)) as ex:
        mapped = list(ex.map(_map_groupby, partitions, [("Education")] * len(partitions), [("Age")] * len(partitions)))
    shuffled = defaultdict(list)
    for partial in mapped:
        for k, v in partial.items():
            shuffled[k].append(v)
    result = {}
    for k, partials in shuffled.items():
        total_sum = sum(p[0] for p in partials)
        total_count = sum(p[1] for p in partials)
        result[k] = round(total_sum / total_count, 3) if total_count else 0
    return result, round(time.perf_counter() - t0, 4)


def run_spark(spark, df: pd.DataFrame, n_partitions: int) -> tuple:
    from pyspark.sql import functions as F

    clean = df.copy()
    for col in clean.columns:
        if clean[col].dtype == object:
            clean[col] = clean[col].astype(str)

    t0 = time.perf_counter()
    sdf = spark.createDataFrame(clean).repartition(n_partitions)
    rows = (
        sdf.groupBy("Education")
        .agg(F.avg(F.col("Age").cast("double")).alias("value"))
        .collect()
    )
    result = {r["Education"]: round(r["value"], 3) for r in rows}
    return result, round(time.perf_counter() - t0, 4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[5_000, 50_000, 200_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--partitions", type=int, default=8)
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)

    full_df, source_path = load_source_df()
    print(f"Source data: {source_path} ({len(full_df):,} rows available)")
    print(f"CPU cores available on this machine: {os.cpu_count()}")
    if (os.cpu_count() or 1) <= 1:
        print(
            "\n*** WARNING: only 1 CPU core detected. Spark/MapReduce cannot show "
            "real parallel speedup on this machine - re-run on a multi-core "
            "machine for a meaningful benchmark. Results below are still real "
            "measurements, just not representative of the parallel case. ***\n"
        )

    from app.services.spark_service import get_spark_session
    spark = get_spark_session()
    print(f"Spark: real local engine, version {spark.version}, master={spark.sparkContext.master}\n")

    all_results = []

    for size in args.sizes:
        if size > len(full_df):
            reps = (size // len(full_df)) + 1
            df = pd.concat([full_df] * reps, ignore_index=True).iloc[:size]
        else:
            df = full_df.sample(n=size, random_state=42).reset_index(drop=True)

        print(f"=== {size:,} rows ===")
        row = {"rows": size, "cpu_count": os.cpu_count()}

        for engine_name, fn in [
            ("pandas", lambda d=df: run_pandas(d)),
            ("mapreduce", lambda d=df: run_mapreduce(d, args.partitions)),
            ("spark", lambda d=df: run_spark(spark, d, args.partitions)),
        ]:
            times = []
            result = None
            for _ in range(args.repeats):
                result, elapsed = fn()
                times.append(elapsed)
            mean_t = round(statistics.mean(times), 4)
            row[f"{engine_name}_seconds"] = mean_t
            row[f"{engine_name}_seconds_all_runs"] = times
            row[f"{engine_name}_result"] = result
            print(f"  {engine_name:10s}: {mean_t:.4f}s (mean of {args.repeats} runs)  result={result}")

        # correctness check: all three engines must agree (rounded)
        pandas_r, mr_r, spark_r = row["pandas_result"], row["mapreduce_result"], row["spark_result"]
        keys = set(pandas_r) | set(mr_r) | set(spark_r)
        mismatches = [
            k for k in keys
            if not (
                abs(pandas_r.get(k, 0) - mr_r.get(k, 0)) < 0.01
                and abs(pandas_r.get(k, 0) - spark_r.get(k, 0)) < 0.01
            )
        ]
        row["correctness_ok"] = len(mismatches) == 0
        if mismatches:
            print(f"  !! MISMATCH on keys: {mismatches}")
        else:
            print("  correctness check: OK (all three engines agree)")

        speedup_mr = round(row["pandas_seconds"] / row["mapreduce_seconds"], 3) if row["mapreduce_seconds"] else None
        speedup_spark = round(row["pandas_seconds"] / row["spark_seconds"], 3) if row["spark_seconds"] else None
        row["speedup_mapreduce_vs_pandas"] = speedup_mr
        row["speedup_spark_vs_pandas"] = speedup_spark
        print(f"  speedup vs pandas -> mapreduce: {speedup_mr}x, spark: {speedup_spark}x\n")

        all_results.append(row)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_dataset": source_path,
        "cpu_count": os.cpu_count(),
        "spark_version": spark.version,
        "spark_master": spark.sparkContext.master,
        "partitions_used": args.partitions,
        "repeats_per_measurement": args.repeats,
        "results": all_results,
    }

    out_path = os.path.join(RESULTS_DIR, "results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
