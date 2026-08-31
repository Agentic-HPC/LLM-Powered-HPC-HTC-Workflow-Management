from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowOut

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowOut, status_code=status.HTTP_201_CREATED)
def create_workflow(
    data: WorkflowCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    workflow = Workflow(
        name=data.name,
        description=data.description,
        definition=[step.model_dump() for step in data.definition],
        original_prompt=data.original_prompt,
        owner_id=user.id,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


@router.get("", response_model=List[WorkflowOut])
def list_workflows(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Workflow).filter(Workflow.owner_id == user.id).order_by(Workflow.created_at.desc()).all()


@router.get("/{workflow_id}", response_model=WorkflowOut)
def get_workflow(workflow_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workflow = _get_owned_workflow(db, workflow_id, user)
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(workflow_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workflow = _get_owned_workflow(db, workflow_id, user)
    db.delete(workflow)
    db.commit()


def _get_owned_workflow(db: Session, workflow_id: int, user: User) -> Workflow:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.owner_id == user.id).first()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow
