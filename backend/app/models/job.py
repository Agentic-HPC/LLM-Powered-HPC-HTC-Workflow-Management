import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobArchitecture(str, enum.Enum):
    MULTI_AGENT = "multi_agent"
    SINGLE_AGENT = "single_agent"


class ProcessingParadigm(str, enum.Enum):
    PANDAS = "pandas"           # in-memory, single-partition (default HPC-style)
    MAPREDUCE = "mapreduce"     # simulated Hadoop MapReduce (HTC/Big Data)
    SPARK = "spark"             # simulated Spark RDD stages (HTC/Big Data)


class Job(Base):
    """A single execution of a workflow (or an ad-hoc prompt-driven run)."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=True)

    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)

    architecture = Column(Enum(JobArchitecture), default=JobArchitecture.MULTI_AGENT, nullable=False)
    processing_paradigm = Column(Enum(ProcessingParadigm), default=ProcessingParadigm.PANDAS, nullable=False)
    node_id = Column(Integer, ForeignKey("cluster_nodes.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="jobs")
    workflow = relationship("Workflow", back_populates="jobs")
    result = relationship("Result", back_populates="job", uselist=False, cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    node = relationship("ClusterNode")
    resource_samples = relationship(
        "ResourceUsageSample", cascade="all, delete-orphan",
        primaryjoin="Job.id == ResourceUsageSample.job_id",
        order_by="ResourceUsageSample.elapsed_seconds",
    )

    @property
    def node_name(self) -> str | None:
        return self.node.name if self.node else None
