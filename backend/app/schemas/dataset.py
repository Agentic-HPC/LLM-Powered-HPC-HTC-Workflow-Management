from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DatasetOut(BaseModel):
    id: int
    name: str
    file_path: str
    columns: Optional[List[Dict[str, Any]]] = None
    row_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
