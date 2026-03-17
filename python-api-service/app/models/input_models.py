from typing import Any, Dict, Optional

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


class MarketInventoryCaptureIn(BaseModel):
    market_silver: Optional[int] = None
    inventory_silver: Optional[int] = None


class ManualWarehouseValueIn(BaseModel):
    warehouse: str
    market_silver: int


class PreorderIn(BaseModel):
    preorder_silver: int
    source: Optional[str] = 'browser-extension'
    details: Dict[str, Any] = Field(default_factory=dict)
