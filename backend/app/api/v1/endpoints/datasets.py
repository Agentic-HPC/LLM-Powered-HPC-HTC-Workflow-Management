from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import DatasetOut
from app.services.dataset_service import scan_and_register_datasets

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=List[DatasetOut])
def list_datasets(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(Dataset).all()


@router.post("/rescan", response_model=List[DatasetOut])
def rescan_datasets(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Re-scan the data/ directory for CSV files and (re)register them."""
    return scan_and_register_datasets(db)
