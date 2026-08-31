import asyncio
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agents.intent_agent import IntentAgent
from app.agents.orchestrator import Orchestrator
from app.agents.planning_agent import PlanningAgent
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.dataset import Dataset
from app.models.job import Job
from app.models.workflow import Workflow

logger = logging.getLogger(__name__)


async def parse_prompt_to_workflow(db: Session, prompt: str) -> Dict[str, Any]:
    """Runs Intent + Planning agents standalone (no execution) so the user
    can preview/edit the plan in Prompt Studio before saving it as a Workflow."""
    datasets = db.query(Dataset).all()
    context: Dict[str, Any] = {
        "prompt": prompt,
        "available_datasets": [{"name": d.name, "columns": d.columns} for d in datasets],
    }
    context = await IntentAgent().run(context)
    context = await PlanningAgent().run(context)
    return {
        "intent": context["intent"],
        "plan": context["plan"],
    }


def _run_job_sync(job_id: int, prompt: str = None, workflow_definition: List[Dict[str, Any]] = None):
    """Runs the actual agent pipeline with its own DB session (SQLAlchemy
    sessions aren't thread/process-safe to share across boundaries). Called
    either from a FastAPI BackgroundTasks thread or from inside a real
    Celery worker process - the logic is identical either way."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        orchestrator = Orchestrator(db=db, job=job)
        if workflow_definition is not None:
            asyncio.run(orchestrator.run_workflow_pipeline(workflow_definition, original_prompt=prompt))
        else:
            asyncio.run(orchestrator.run_prompt_pipeline(prompt))
    finally:
        db.close()


@celery_app.task(name="app.services.workflow_service.run_job_task", bind=True)
def run_job_task(self, job_id: int, prompt: Optional[str] = None,
                  workflow_definition: Optional[List[Dict[str, Any]]] = None):
    """Real Celery task. This is what actually executes when a Celery
    worker process (`celery -A app.core.celery_app worker`) picks a job off
    the Redis queue - a genuinely separate OS process from the FastAPI
    server, which can be scaled out to additional worker machines."""
    logger.info(f"[celery worker] running job {job_id}")
    _run_job_sync(job_id, prompt=prompt, workflow_definition=workflow_definition)
    return {"job_id": job_id, "status": "dispatched"}


def _redis_reachable() -> bool:
    try:
        import redis
        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        return client.ping()
    except Exception:
        return False


def dispatch_job(background_tasks, job: Job, workflow: Workflow = None, prompt: str = None) -> None:
    """
    Queue the job for execution.

    Uses a real Celery task (JOB_QUEUE_BACKEND=celery, the default) when
    Redis is reachable - this is genuine distributed job dispatch, not a
    simulation: the task is serialized, pushed onto a Redis queue, and
    picked up by whatever Celery worker process(es) are running, exactly
    like handing a job off to a real job scheduler.

    Falls back to in-process FastAPI BackgroundTasks automatically when
    Redis isn't reachable (e.g. running tests, or a quick local demo
    without starting a worker) so the app never hard-fails just because
    infrastructure isn't up.
    """
    definition = workflow.definition if workflow is not None else None
    use_celery = settings.JOB_QUEUE_BACKEND == "celery" and _redis_reachable()

    if use_celery:
        logger.info(f"dispatching job {job.id} to Celery/Redis queue")
        run_job_task.delay(job.id, prompt, definition)
    else:
        logger.info(f"dispatching job {job.id} via in-process BackgroundTasks (Celery/Redis unavailable)")
        background_tasks.add_task(_run_job_sync, job.id, prompt, definition)
