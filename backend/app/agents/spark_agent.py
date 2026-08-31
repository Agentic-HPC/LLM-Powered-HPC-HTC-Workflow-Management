"""
SparkAgent: runs the "summary" / "groupby_aggregate" analysis on a REAL
Apache Spark engine (via app/services/spark_service.py), not a simulation.

The incoming pandas DataFrame (already loaded by DataAgent) is converted to
a genuine Spark DataFrame, processed with real Spark SQL operations
(groupBy/agg, or column-wise aggregate functions), and the result is
collected back to the driver. Stage timings are wall-clock measurements
around real Spark actions (Spark's execution is lazy, so timing collect()
captures the actual DAG execution, not a fabricated number).

In local mode (the default, SPARK_MASTER_URL=local[*]) this uses real
task-level parallelism across every CPU core on the machine. Pointing
SPARK_MASTER_URL at a real standalone/YARN/K8s cluster makes this run on
genuine multi-node hardware without any code change here.
"""
import time
from typing import Any, Dict

import pandas as pd
from pyspark.sql import functions as F

from app.agents.base_agent import BaseAgent
from app.services.spark_service import get_spark_session


class SparkAgent(BaseAgent):
    name = "spark_agent"

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        step = context["current_step"]
        action = step["action"]
        params = step["params"]
        df: pd.DataFrame = context["dataframe"]
        n_partitions = step["params"].get("n_partitions", 4)

        spark = get_spark_session()
        stage_timings: Dict[str, float] = {}

        # Stage: parallelize - convert the pandas DataFrame into a real
        # Spark DataFrame, explicitly repartitioned into n_partitions.
        t0 = time.perf_counter()
        self.log(f"Stage [parallelize]: creating Spark DataFrame, repartitioning into {n_partitions}")
        clean_df = df.copy()
        # Spark's Arrow-based pandas conversion is strict about mixed/NaN
        # object columns; coerce object columns to string defensively.
        for col in clean_df.columns:
            if clean_df[col].dtype == object:
                clean_df[col] = clean_df[col].astype(str)
        sdf = spark.createDataFrame(clean_df).repartition(n_partitions)
        actual_partitions = sdf.rdd.getNumPartitions()
        stage_timings["parallelize"] = round(time.perf_counter() - t0, 4)

        # Stage: transform + action. Spark is lazy, so real execution (the
        # scheduler splitting this into tasks across partitions, shuffling
        # for the groupBy, and running on executors) happens at .collect().
        t0 = time.perf_counter()
        if action == "groupby_aggregate":
            group_col, value_col = params["group_col"], params["value_col"]
            self.log(f"Stage [groupBy+agg]: real Spark groupBy('{group_col}').avg('{value_col}')")
            result_sdf = (
                sdf.groupBy(group_col)
                .agg(F.avg(F.col(value_col).cast("double")).alias("value"))
                .orderBy(F.desc("value"))
            )
            rows = result_sdf.collect()
            result = [{"group": r[group_col], "value": round(r["value"], 3) if r["value"] is not None else 0} for r in rows]
        else:
            self.log("Stage [agg]: real Spark column-wise summary (mean/count/min/max)")
            numeric_cols = [c for c, t in sdf.dtypes if t in ("int", "bigint", "double", "float")]
            agg_exprs = []
            for c in numeric_cols:
                agg_exprs += [
                    F.avg(c).alias(f"{c}__mean"),
                    F.count(c).alias(f"{c}__count"),
                    F.min(c).alias(f"{c}__min"),
                    F.max(c).alias(f"{c}__max"),
                ]
            row = sdf.agg(*agg_exprs).collect()[0].asDict() if agg_exprs else {}
            result = {}
            for c in numeric_cols:
                result[c] = {
                    "mean": round(row[f"{c}__mean"], 3) if row.get(f"{c}__mean") is not None else 0,
                    "count": int(row[f"{c}__count"]) if row.get(f"{c}__count") is not None else 0,
                    "min": round(row[f"{c}__min"], 3) if row.get(f"{c}__min") is not None else None,
                    "max": round(row[f"{c}__max"], 3) if row.get(f"{c}__max") is not None else None,
                }
        stage_timings["transform_and_collect"] = round(time.perf_counter() - t0, 4)

        self.log(f"Spark job complete: {actual_partitions} real partitions, spark version {spark.version}")

        context["analytics_result"] = result
        context["analytics_action"] = action
        context["engine_metadata"] = {
            "engine": "spark",
            "spark_version": spark.version,
            "spark_master": spark.sparkContext.master,
            "partitions": actual_partitions,
            "stage_timings": stage_timings,
            "simulated": False,
        }
        return context
