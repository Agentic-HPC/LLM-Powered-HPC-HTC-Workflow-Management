from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Dataset(Base):
    """Registered dataset available to workflows (CSV files on disk)."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    columns = Column(JSON, nullable=True)  # list of {"name": ..., "dtype": ...}
    row_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("JobDataset", back_populates="dataset", cascade="all, delete-orphan")


class JobDataset(Base):
    """Association table: which datasets a job used."""

    __tablename__ = "job_datasets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    dataset = relationship("Dataset", back_populates="jobs")
