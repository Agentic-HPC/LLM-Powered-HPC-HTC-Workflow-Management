from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class WorkflowStep(BaseModel):
    agent: str
    action: str
    params: Dict[str, Any] = {}


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    definition: List[WorkflowStep]
    original_prompt: Optional[str] = None


class WorkflowOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    definition: List[Dict[str, Any]]
    original_prompt: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptParseRequest(BaseModel):
    prompt: str


class PromptParseResponse(BaseModel):
    workflow: WorkflowCreate
    reasoning: str
