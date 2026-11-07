from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.models.job import Job
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.job import JobCreate, JobDetailOut, JobOut
from app.services.workflow_service import dispatch_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_EXPENSIVE)
def create_job(
    request: Request,
    data: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not data.workflow_id and not data.prompt:
        raise HTTPException(status_code=400, detail="Provide either workflow_id or prompt")

    workflow = None
    if data.workflow_id:
        workflow = db.query(Workflow).filter(
            Workflow.id == data.workflow_id, Workflow.owner_id == user.id
        ).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

    resolved_prompt = data.prompt or (workflow.original_prompt if workflow else None)
    job = Job(
        owner_id=user.id,
        workflow_id=workflow.id if workflow else None,
        prompt=resolved_prompt,
        architecture=data.architecture,
        processing_paradigm=data.processing_paradigm,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    dispatch_job(
        background_tasks,
        job=job,
        workflow=workflow,
        prompt=resolved_prompt,
    )
    return job


@router.get("", response_model=List[JobOut])
def list_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Job).filter(Job.owner_id == user.id).order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobDetailOut)
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/restart", response_model=JobOut)
def restart_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    workflow = None
    if job.workflow_id:
        workflow = db.query(Workflow).filter(Workflow.id == job.workflow_id).first()

    prompt = job.prompt
    if not prompt and workflow:
        prompt = workflow.original_prompt

    # Legacy fallback: inspect previous intent_agent log if prompt wasn't stored
    if not prompt:
        import re
        from app.models.job_log import JobLog
        intent_log = (
            db.query(JobLog)
            .filter(JobLog.job_id == job.id, JobLog.agent_name == "intent_agent")
            .order_by(JobLog.id.asc())
            .first()
        )
        if intent_log and "Parsing intent from prompt: '" in intent_log.message:
            m = re.search(r"Parsing intent from prompt:\s*'([^']+)'", intent_log.message)
            if m:
                prompt = m.group(1)
                job.prompt = prompt

    if not prompt and not workflow:
        raise HTTPException(status_code=400, detail="Cannot restart job: prompt or workflow definition is missing")

    # Release any existing assigned node back to idle
    if job.node_id:
        from app.models.cluster_node import ClusterNode
        from app.services import cluster_service
        node = db.query(ClusterNode).filter(ClusterNode.id == job.node_id).first()
        if node:
            cluster_service.mark_node_idle(db, node)
        job.node_id = None

    # Clear previous logs, result, and resource samples for clean re-execution
    from app.models.job_log import JobLog
    from app.models.resource_usage import ResourceUsageSample
    from app.models.result import Result

    db.query(Result).filter(Result.job_id == job.id).delete()
    db.query(JobLog).filter(JobLog.job_id == job.id).delete()
    db.query(ResourceUsageSample).filter(ResourceUsageSample.job_id == job.id).delete()

    # Reset job execution state
    from app.models.job import JobStatus
    job.status = JobStatus.PENDING
    job.progress = 0
    job.error_message = None
    job.started_at = None
    job.finished_at = None
    db.commit()
    db.refresh(job)

    dispatch_job(
        background_tasks,
        job=job,
        workflow=workflow,
        prompt=prompt,
    )
    return job
