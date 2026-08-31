from typing import Any, Dict, List

import pandas as pd


def describe_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Return summary statistics safe to JSON-serialize."""
    numeric_summary = df.describe(include="number").round(3).to_dict()
    return {
        "row_count": len(df),
        "columns": list(df.columns),
        "numeric_summary": numeric_summary,
        "null_counts": df.isnull().sum().to_dict(),
    }


def groupby_aggregate(df: pd.DataFrame, group_col: str, value_col: str, agg: str = "mean") -> List[Dict[str, Any]]:
    grouped = df.groupby(group_col)[value_col].agg(agg).reset_index()
    grouped.columns = [group_col, value_col]
    return grouped.round(3).to_dict(orient="records")


def time_series(df: pd.DataFrame, date_col: str, value_col: str, freq: str = "M") -> List[Dict[str, Any]]:
    tmp = df.copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col])
    resampled = tmp.set_index(date_col)[value_col].resample(freq).mean().reset_index()
    resampled[date_col] = resampled[date_col].dt.strftime("%Y-%m-%d")
    return resampled.round(3).to_dict(orient="records")


def correlation_matrix(df: pd.DataFrame) -> Dict[str, Any]:
    numeric_df = df.select_dtypes(include="number")
    return numeric_df.corr().round(3).to_dict()
