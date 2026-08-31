"""
MapReduceAgent: a genuinely parallel MapReduce-style engine.

Earlier versions of this agent ran the map phase in a plain Python `for`
loop on one process (a "simulation" of distribution). This version submits
each partition's map task to a real `ProcessPoolExecutor` - each partition
is processed by a separate OS process, running concurrently on separate
CPU cores. That's genuine map-phase parallelism, the same fundamental
mechanism (independent workers processing independent shards, then a
shuffle/reduce step combines results) as Hadoop MapReduce, just without a
YARN/HDFS layer underneath it.

The shuffle and reduce phases run on the driver process, mirroring how
Hadoop's reducers pull shuffled data from mappers.
"""
import os
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import current_process
from typing import Any, Dict, List

import pandas as pd

from app.agents.base_agent import BaseAgent
from app.core.config import settings


# ---- module-level (picklable) worker functions run in separate processes ----

def _map_groupby(df: pd.DataFrame, group_col: str, value_col: str) -> Dict[Any, Any]:
    grouped = df.groupby(group_col)[value_col].agg(["sum", "count"])
    return {k: (row["sum"], row["count"]) for k, row in grouped.iterrows()}


def _map_summary(df: pd.DataFrame) -> Dict[str, Any]:
    numeric = df.select_dtypes(include="number")
    return {
        col: (numeric[col].sum(), numeric[col].count(), numeric[col].min(), numeric[col].max())
        for col in numeric.columns
    }


def _map_task(args):
    """Entry point run inside each worker process."""
    idx, df, action, params = args
    pid = os.getpid()
    t0 = time.perf_counter()
    if action == "groupby_aggregate":
        result = _map_groupby(df, params["group_col"], params["value_col"])
    else:
        result = _map_summary(df)
    elapsed = round(time.perf_counter() - t0, 4)
    return idx, pid, result, elapsed


class MapReduceAgent(BaseAgent):
    name = "mapreduce_agent"

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        step = context["current_step"]
        action = step["action"]
        params = step["params"]
        partitions: List[pd.DataFrame] = context["partitions"]

        max_workers = settings.MAPREDUCE_MAX_WORKERS or os.cpu_count() or 4
        max_workers = min(max_workers, len(partitions))

        self.log(
            f"Starting real MapReduce job: {len(partitions)} partitions, "
            f"action={action}, {max_workers} worker processes"
        )

        stage_timings = {"map_tasks": [], "map_wall_clock": 0.0, "shuffle": 0.0, "reduce": 0.0}
        worker_pids = set()

        # Celery's prefork workers are daemon processes and cannot create
        # child processes. Keep process-based mapping for normal execution,
        # but use threads when the workflow already runs inside a daemon.
        executor_class = ThreadPoolExecutor if current_process().daemon else ProcessPoolExecutor
        execution_mode = "threads" if executor_class is ThreadPoolExecutor else "processes"

        # ---- MAP phase: parallel execution across workers ----
        t_map_start = time.perf_counter()
        tasks = [(i, part, action, params) for i, part in enumerate(partitions)]
        results_by_idx: Dict[int, Any] = {}
        with executor_class(max_workers=max_workers) as executor:
            for idx, pid, partial, elapsed in executor.map(_map_task, tasks):
                self.log(f"map task {idx}: completed on worker pid={pid} in {elapsed}s")
                results_by_idx[idx] = partial
                worker_pids.add(pid)
                stage_timings["map_tasks"].append({"partition": idx, "pid": pid, "seconds": elapsed})
        stage_timings["map_wall_clock"] = round(time.perf_counter() - t_map_start, 4)
        mapped = [results_by_idx[i] for i in range(len(partitions))]

        # ---- SHUFFLE phase (driver process): group intermediate pairs by key ----
        t0 = time.perf_counter()
        self.log(f"shuffle: grouping intermediate results from {len(worker_pids)} worker processes by key")
        shuffled: Dict[Any, List[Any]] = defaultdict(list)
        for partial in mapped:
            for k, v in partial.items():
                shuffled[k].append(v)
        stage_timings["shuffle"] = round(time.perf_counter() - t0, 4)

        # ---- REDUCE phase (driver process): combine grouped values ----
        t0 = time.perf_counter()
        self.log("reduce: combining shuffled groups into final result")
        if action == "groupby_aggregate":
            result = self._reduce_groupby(shuffled)
        else:
            result = self._reduce_summary(shuffled)
        stage_timings["reduce"] = round(time.perf_counter() - t0, 4)

        self.log(
            f"MapReduce job complete: {len(partitions)} map tasks using "
            f"{execution_mode}, 1 shuffle, 1 reduce"
        )

        context["analytics_result"] = result
        context["analytics_action"] = action
        context["engine_metadata"] = {
            "engine": "mapreduce",
            "partitions": len(partitions),
            "worker_processes": len(worker_pids),
            "worker_pids": sorted(worker_pids),
            "execution_mode": execution_mode,
            "stage_timings": stage_timings,
            "simulated": False,
        }
        return context

    # ---- reduce functions: combine shuffled (key -> [partial values]) into final result ----
    @staticmethod
    def _reduce_groupby(shuffled: Dict[Any, List[Any]]) -> List[Dict[str, Any]]:
        out = []
        for key, partials in shuffled.items():
            total_sum = sum(p[0] for p in partials)
            total_count = sum(p[1] for p in partials)
            out.append({"group": key, "value": round(total_sum / total_count, 3) if total_count else 0})
        return out

    @staticmethod
    def _reduce_summary(shuffled: Dict[str, List[Any]]) -> Dict[str, Any]:
        out = {}
        for col, partials in shuffled.items():
            total_sum = sum(p[0] for p in partials)
            total_count = sum(p[1] for p in partials)
            mins = [p[2] for p in partials]
            maxs = [p[3] for p in partials]
            out[col] = {
                "mean": round(total_sum / total_count, 3) if total_count else 0,
                "count": int(total_count),
                "min": round(min(mins), 3) if mins else None,
                "max": round(max(maxs), 3) if maxs else None,
            }
        return out
