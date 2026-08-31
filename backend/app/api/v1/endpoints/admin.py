from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.job import Job
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return db.query(User).all()


@router.get("/stats")
def platform_stats(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return {
        "total_users": db.query(User).count(),
        "total_workflows": db.query(Workflow).count(),
        "total_jobs": db.query(Job).count(),
    }
