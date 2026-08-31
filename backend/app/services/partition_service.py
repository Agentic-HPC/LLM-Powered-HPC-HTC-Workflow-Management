"""
Simulates the data-partitioning step every real distributed engine
(Hadoop MapReduce, Spark) performs before processing: splitting a dataset
into N chunks that would, in a real cluster, be sent to different worker
nodes. Uses the same balanced-split approach as numpy.array_split so every
row is included exactly once, even when len(df) doesn't divide evenly by
n_partitions (the first `remainder` chunks get one extra row rather than
silently dropping rows off the end).
"""
from typing import List

import pandas as pd


def partition_dataframe(df: pd.DataFrame, n_partitions: int = 4) -> List[pd.DataFrame]:
    if len(df) == 0:
        return [df]

    n_partitions = max(1, min(n_partitions, len(df)))
    base_size, remainder = divmod(len(df), n_partitions)

    chunks = []
    start = 0
    for i in range(n_partitions):
        size = base_size + (1 if i < remainder else 0)
        chunks.append(df.iloc[start:start + size].reset_index(drop=True))
        start += size

    return chunks
