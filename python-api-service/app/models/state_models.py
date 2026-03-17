from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.models.domain_models import RecordItem, WarehouseSnapshot


class AppState(BaseModel):
    records: List[RecordItem] = Field(default_factory=list)
    warehouse_snapshots: List[WarehouseSnapshot] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=lambda: {
        'include_warehouses_in_total': True
    })
