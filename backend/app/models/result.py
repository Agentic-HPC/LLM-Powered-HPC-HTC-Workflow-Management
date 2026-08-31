from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Result(Base):
    """Output of a completed job: metrics, charts data, and the generated report."""

    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), unique=True, nullable=False)

    metrics = Column(JSON, nullable=True)       # e.g. {"rows": 500, "mean_salary": 71234.5}
    chart_data = Column(JSON, nullable=True)     # data shaped for frontend Recharts components
    report_markdown = Column(Text, nullable=True)  # ReportingAgent's narrative summary
    engine_metadata = Column(JSON, nullable=True)   # partition count, MapReduce/Spark stage timings, node info

    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="result")
