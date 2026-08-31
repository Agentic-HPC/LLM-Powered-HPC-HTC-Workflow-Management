from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClusterNode(Base):
    """
    A simulated compute node in the HPC/HTC cluster. Not a real scheduler -
    this models node capacity (CPU cores, GPUs, memory) so jobs can be
    'assigned' to a node and their resource consumption can be simulated
    and charted, per the project's HPC/HTC resource-utilization requirement.
    """

    __tablename__ = "cluster_nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    node_type = Column(String(50), nullable=False, default="cpu")  # cpu | gpu | hybrid
    cpu_cores = Column(Integer, nullable=False, default=8)
    gpu_count = Column(Integer, nullable=False, default=0)
    memory_gb = Column(Integer, nullable=False, default=32)
    status = Column(String(20), nullable=False, default="idle")  # idle | busy
    created_at = Column(DateTime, default=datetime.utcnow)

    usage_samples = relationship("ResourceUsageSample", back_populates="node")
