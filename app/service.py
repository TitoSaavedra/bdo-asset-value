from datetime import datetime
from typing import Optional
from app.models import AppState, RecordItem, WarehouseSnapshot
from app.storage import storage


def now_iso() -> str:
    return datetime.now().isoformat(timespec='seconds')


class AssetService:
    def get_state(self) -> AppState:
        return storage.read_state()

    def get_warehouse_totals(self, state: AppState) -> dict[str, int]:
        latest = {}
        for item in state.warehouse_snapshots:
            latest[item.warehouse] = item.market_silver
        return latest

    def warehouses_total(self, state: AppState) -> int:
        return sum(self.get_warehouse_totals(state).values())

    def latest_inventory(self, state: AppState) -> int:
        for item in reversed(state.records):
            if item.inventory_silver is not None:
                return item.inventory_silver
        return 0

    def latest_market(self, state: AppState) -> int:
        for item in reversed(state.records):
            if item.market_silver is not None:
                return item.market_silver
        return 0

    def latest_preorder(self, state: AppState) -> int:
        for item in reversed(state.records):
            return item.preorder_silver
        return 0

    def append_record(self, state: AppState, market_silver: Optional[int], inventory_silver: Optional[int], preorder_silver: int, source: str, details: dict) -> RecordItem:
        warehouses_total = self.warehouses_total(state)
        total_without_warehouses = (market_silver or self.latest_market(state)) + (inventory_silver if inventory_silver is not None else self.latest_inventory(state)) + preorder_silver
        total_with_warehouses = total_without_warehouses + warehouses_total
        record = RecordItem(
            captured_at=now_iso(),
            market_silver=market_silver,
            inventory_silver=inventory_silver,
            preorder_silver=preorder_silver,
            warehouses_total=warehouses_total,
            total_with_warehouses=total_with_warehouses,
            total_without_warehouses=total_without_warehouses,
            source=source,
            details=details,
        )
        state.records.append(record)
        storage.write_state(state)
        return record

    def add_manual_record(self, market_silver: Optional[int], inventory_silver: Optional[int], preorder_silver: int) -> RecordItem:
        state = self.get_state()
        return self.append_record(state, market_silver, inventory_silver, preorder_silver, 'manual', {})

    def add_inventory_capture(self, inventory_silver: int) -> RecordItem:
        state = self.get_state()
        preorder_silver = self.latest_preorder(state)
        market_silver = self.latest_market(state)
        return self.append_record(state, market_silver, inventory_silver, preorder_silver, 'ocr-inventory', {})

    def add_preorder(self, preorder_silver: int, source: str) -> RecordItem:
        state = self.get_state()
        return self.append_record(state, self.latest_market(state), self.latest_inventory(state), preorder_silver, source, {})

    def add_storage_capture(self, warehouse: str, market_silver: int) -> tuple[WarehouseSnapshot, Optional[RecordItem]]:
        state = self.get_state()
        previous_name = state.warehouse_snapshots[-1].warehouse if state.warehouse_snapshots else None
        changed = previous_name != warehouse
        snapshot = WarehouseSnapshot(captured_at=now_iso(), warehouse=warehouse, market_silver=market_silver)
        state.warehouse_snapshots.append(snapshot)
        storage.write_state(state)
        record = None
        if changed:
            record = self.append_record(state, self.latest_market(state), self.latest_inventory(state), self.latest_preorder(state), 'ocr-storage', {'warehouse': warehouse})
        return snapshot, record

    def dashboard(self) -> dict:
        state = self.get_state()
        latest = state.records[-1] if state.records else None
        return {
            'latest': latest.model_dump() if latest else None,
            'records': [r.model_dump() for r in state.records[-50:]],  # Last 50 records
            'settings': state.settings,
        }