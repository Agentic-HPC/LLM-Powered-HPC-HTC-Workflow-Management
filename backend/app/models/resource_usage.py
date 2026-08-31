from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class ResourceUsageSample(Base):
    """A single point-in-time simulated resource reading for a running job."""

    __tablename__ = "resource_usage_samples"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("cluster_nodes.id"), nullable=True)

    elapsed_seconds = Column(Float, nullable=False)
    cpu_percent = Column(Float, nullable=False)
    gpu_percent = Column(Float, nullable=False, default=0.0)
    memory_percent = Column(Float, nullable=False)
    stage = Column(String(100), nullable=True)  # which pipeline stage produced this sample

    created_at = Column(DateTime, default=datetime.utcnow)

    node = relationship("ClusterNode", back_populates="usage_samples")
