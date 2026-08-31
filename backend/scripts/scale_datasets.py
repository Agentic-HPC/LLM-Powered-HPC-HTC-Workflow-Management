"""
Generates large-scale benchmark versions of the real datasets.

The platform's real datasets (data/employees.csv, data/weather.csv) are
uploaded, real-world data:
  - employees.csv   : 4,653 rows, IBM HR-analytics-style attrition data
  - weather.csv      : 96,453 rows, hourly weather observations

That's fine for correctness, but too small to show any real benefit from
distributed execution (Spark/MapReduce) vs. plain pandas - a modern laptop
processes both instantly in a single thread. To produce a *meaningful*
scaling benchmark (see scripts/run_benchmarks.py), this script builds larger
derived datasets by bootstrap-resampling the real rows with small jitter
added to numeric columns (so the statistical shape of the data is
preserved, but rows aren't exact duplicates).

This is standard practice for scale/load-testing with real seed data. It is
NOT used to fabricate "real" results - the benchmark report explicitly
labels these as "real data, scaled by resampling" and the correctness
checks (mapreduce/spark producing identical answers to pandas) are run
against the true, unscaled files.

Usage:
    python scripts/scale_datasets.py --employees 500000 --weather 2000000
"""
import argparse
import os

import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def scale_dataframe(df: pd.DataFrame, target_rows: int, jitter_cols: list, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_repeats = (target_rows // len(df)) + 1
    scaled = pd.concat([df] * n_repeats, ignore_index=True).iloc[:target_rows].copy()

    # Add small gaussian jitter to numeric columns so scaled rows aren't
    # exact duplicates of the original (preserves distribution, avoids
    # trivially-compressible/duplicate data skewing the benchmark).
    for col in jitter_cols:
        if col not in scaled.columns:
            continue
        std = df[col].std()
        if pd.isna(std) or std == 0:
            continue
        noise = rng.normal(loc=0.0, scale=std * 0.03, size=len(scaled))
        scaled[col] = scaled[col] + noise

    return scaled.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--employees", type=int, default=500_000)
    parser.add_argument("--weather", type=int, default=2_000_000)
    args = parser.parse_args()

    emp_path = os.path.join(DATA_DIR, "employees.csv")
    weather_path = os.path.join(DATA_DIR, "weather.csv")

    print(f"Loading real datasets from {DATA_DIR} ...")
    employees = pd.read_csv(emp_path)
    weather = pd.read_csv(weather_path)
    print(f"  employees.csv : {len(employees):,} real rows")
    print(f"  weather.csv   : {len(weather):,} real rows")

    print(f"\nScaling employees.csv -> {args.employees:,} rows (bootstrap + jitter) ...")
    emp_large = scale_dataframe(
        employees, args.employees,
        jitter_cols=["Age", "PaymentTier", "ExperienceInCurrentDomain"],
    )
    emp_large_path = os.path.join(DATA_DIR, "employees_large.csv")
    emp_large.to_csv(emp_large_path, index=False)
    print(f"  wrote {emp_large_path} ({len(emp_large):,} rows)")

    print(f"\nScaling weather.csv -> {args.weather:,} rows (bootstrap + jitter) ...")
    weather_large = scale_dataframe(
        weather, args.weather,
        jitter_cols=["Temperature (C)", "Apparent Temperature (C)", "Humidity",
                      "Wind Speed (km/h)", "Pressure (millibars)"],
    )
    weather_large_path = os.path.join(DATA_DIR, "weather_large.csv")
    weather_large.to_csv(weather_large_path, index=False)
    print(f"  wrote {weather_large_path} ({len(weather_large):,} rows)")

    print("\nDone. These *_large.csv files are for the distributed-compute "
          "benchmark only; Prompt Studio and correctness tests use the real, "
          "unscaled employees.csv / weather.csv.")


if __name__ == "__main__":
    main()
