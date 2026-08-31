from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.cluster_service import cluster_snapshot

router = APIRouter(prefix="/cluster", tags=["cluster"])


@router.get("/nodes")
def list_nodes(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Simulated HPC/HTC cluster node inventory and current (idle/busy) status."""
    return cluster_snapshot(db)
