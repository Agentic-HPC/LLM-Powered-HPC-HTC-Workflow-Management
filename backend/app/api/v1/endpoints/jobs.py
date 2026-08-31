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

    job = Job(
        owner_id=user.id,
        workflow_id=workflow.id if workflow else None,
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
        prompt=data.prompt or (workflow.original_prompt if workflow else None),
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
