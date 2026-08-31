import os
from typing import List

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.dataset import Dataset


def scan_and_register_datasets(db: Session) -> List[Dataset]:
    """
    Walk settings.DATASET_DIR for CSV files and (re)register them in the
    datasets table, refreshing column/row metadata each time.
    """
    registered = []
    dataset_dir = settings.DATASET_DIR
    if not os.path.isdir(dataset_dir):
        return registered

    for fname in sorted(os.listdir(dataset_dir)):
        if not fname.endswith(".csv"):
            continue
        path = os.path.join(dataset_dir, fname)
        name = os.path.splitext(fname)[0]

        df = pd.read_csv(path, nrows=5000)  # sample for schema inference
        columns = [{"name": c, "dtype": str(df[c].dtype)} for c in df.columns]
        row_count = sum(1 for _ in open(path)) - 1  # minus header

        ds = db.query(Dataset).filter(Dataset.name == name).first()
        if ds is None:
            ds = Dataset(name=name, file_path=path)
            db.add(ds)
        ds.file_path = path
        ds.columns = columns
        ds.row_count = max(row_count, 0)
        registered.append(ds)

    db.commit()
    for ds in registered:
        db.refresh(ds)
    return registered


def load_dataset_df(dataset: Dataset) -> pd.DataFrame:
    return pd.read_csv(dataset.file_path)
