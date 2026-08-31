from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Workflow(Base):
    """A saved, reusable pipeline definition (sequence of agent steps)."""

    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Ordered list of step definitions, e.g.
    # [{"agent": "data", "action": "load_dataset", "params": {...}}, ...]
    definition = Column(JSON, nullable=False, default=list)

    original_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="workflows")
    jobs = relationship("Job", back_populates="workflow", cascade="all, delete-orphan")
