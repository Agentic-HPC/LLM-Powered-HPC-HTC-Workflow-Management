from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.job import JobArchitecture, JobStatus, ProcessingParadigm


class JobCreate(BaseModel):
    workflow_id: Optional[int] = None
    prompt: Optional[str] = None  # ad-hoc: parse + run in one shot
    architecture: JobArchitecture = JobArchitecture.MULTI_AGENT
    processing_paradigm: ProcessingParadigm = ProcessingParadigm.PANDAS


class JobLogOut(BaseModel):
    agent_name: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResourceSampleOut(BaseModel):
    elapsed_seconds: float
    cpu_percent: float
    gpu_percent: float
    memory_percent: float
    stage: Optional[str] = None

    model_config = {"from_attributes": True}


class ResultOut(BaseModel):
    metrics: Optional[Dict[str, Any]] = None
    chart_data: Optional[Dict[str, Any]] = None
    report_markdown: Optional[str] = None
    engine_metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: int
    status: JobStatus
    progress: int
    error_message: Optional[str] = None
    architecture: JobArchitecture
    processing_paradigm: ProcessingParadigm
    node_id: Optional[int] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    workflow_id: Optional[int] = None

    model_config = {"from_attributes": True}


class JobDetailOut(JobOut):
    logs: List[JobLogOut] = []
    result: Optional[ResultOut] = None
    resource_samples: List[ResourceSampleOut] = []
    node_name: Optional[str] = None
