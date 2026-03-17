from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WarehouseSnapshot(BaseModel):
    captured_at: str
    warehouse: str
    market_silver: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RecordItem(BaseModel):
    captured_at: str
    market_silver: Optional[int] = None
    inventory_silver: Optional[int] = None
    preorder_silver: int = 0
    warehouses_total: int = 0
    total_with_warehouses: int = 0
    total_without_warehouses: int = 0
    source: str = 'manual'
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
