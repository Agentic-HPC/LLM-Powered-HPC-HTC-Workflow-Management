"""
DataAgent: loads the dataset selected by the plan into a pandas DataFrame
and does light validation/cleaning (drop fully-empty rows, normalize
column names) before handing off to the AnalyticsAgent. If the job's
processing paradigm is mapreduce/spark, it also partitions the DataFrame
into simulated chunks for distributed-style processing.
"""
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.models.dataset import Dataset
from app.services.dataset_service import load_dataset_df
from app.services.partition_service import partition_dataframe


class DataAgent(BaseAgent):
    name = "data_agent"

    def __init__(self, db: Session, log_callback=None):
        super().__init__(log_callback=log_callback)
        self.db = db

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        step_params = context["current_step"]["params"]
        dataset_name = step_params.get("dataset")

        self.log(f"Loading dataset: {dataset_name}")
        dataset = self.db.query(Dataset).filter(Dataset.name == dataset_name).first()
        if dataset is None:
            raise ValueError(f"Dataset '{dataset_name}' not found. Run generate_datasets.py / dataset scan first.")

        df = load_dataset_df(dataset)
        df = df.dropna(how="all")
        df.columns = [c.strip() for c in df.columns]

        self.log(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        context["dataframe"] = df
        context["dataset_name"] = dataset_name

        paradigm = context.get("processing_paradigm", "pandas")
        if paradigm == "mapreduce":
            # Real multiprocessing MapReduceAgent partitions the pandas
            # DataFrame itself and ships each chunk to a worker process.
            n_partitions = step_params.get("n_partitions", 4)
            partitions = partition_dataframe(df, n_partitions=n_partitions)
            self.log(f"Partitioned dataset into {len(partitions)} chunks for real multiprocess MapReduce")
            context["partitions"] = partitions
        elif paradigm == "spark":
            # SparkAgent converts the whole DataFrame into a real Spark
            # DataFrame and lets Spark's own scheduler partition it.
            self.log("Handing full DataFrame to real Spark engine (Spark manages its own partitioning)")

        return context
