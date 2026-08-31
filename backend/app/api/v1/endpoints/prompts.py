from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.workflow import PromptParseRequest
from app.services.llm_service import llm_service
from app.services.workflow_service import parse_prompt_to_workflow

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/parse")
@limiter.limit(settings.RATE_LIMIT_EXPENSIVE)
async def parse_prompt(
    request: Request,
    data: PromptParseRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Run Intent + Planning agents on a raw prompt and return the proposed
    plan for the user to review/edit before saving it as a Workflow.

    Rate-limited (see RATE_LIMIT_EXPENSIVE) because every call makes a real
    LLM request - unbounded calls here mean unbounded API cost/abuse."""
    return await parse_prompt_to_workflow(db, data.prompt)


@router.get("/llm-health")
async def llm_health():
    """Check whether the configured LLM provider is available."""
    return await llm_service.health_check()
