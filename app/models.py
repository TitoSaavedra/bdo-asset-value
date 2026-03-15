from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ManualRecordIn(BaseModel):
    market_silver: Optional[int] = None
    inventory_silver: Optional[int] = None
    preorder_silver: Optional[int] = 0


class StorageCaptureIn(BaseModel):
    warehouse: str
    market_silver: int


class InventoryCaptureIn(BaseModel):
    inventory_silver: int


class PreorderIn(BaseModel):
    preorder_silver: int
    source: Optional[str] = 'browser-extension'


class WarehouseSnapshot(BaseModel):
    captured_at: str
    warehouse: str
    market_silver: int


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


class AppState(BaseModel):
    records: List[RecordItem] = Field(default_factory=list)
    warehouse_snapshots: List[WarehouseSnapshot] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=lambda: {
        'include_warehouses_in_total': True
    })