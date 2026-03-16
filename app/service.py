import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any
from app.models import AppState, RecordItem, WarehouseSnapshot
from app.ocr.config.storages import KNOWN_STORAGES
from app.storage import storage


def now_iso() -> str:
    """Get current timestamp in ISO format.

    Returns:
        str: Current timestamp in ISO format with seconds precision.
    """
    return datetime.now().isoformat(timespec='seconds')


class AssetService:
    """Service class for managing Black Desert Online asset tracking operations."""

    def _broadcast_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast updates to all connected WebSocket clients.

        Args:
            event_type: Type of update event.
            data: Additional data related to the update.
        """
        try:
            from app.main import manager
        except Exception:
            return

        payload = json.dumps({
            'type': event_type,
            'timestamp': now_iso(),
            'data': data,
        })

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(manager.broadcast(payload))
        except RuntimeError:
            asyncio.run(manager.broadcast(payload))

    def get_state(self) -> AppState:
        """Retrieve the current application state.

        Returns:
            AppState: Current application state containing records and settings.
        """
        return storage.read_state()

    def get_warehouse_totals(self, state: AppState) -> Dict[str, int]:
        """Calculate total silver values for each warehouse.

        Args:
            state: Current application state.

        Returns:
            Dict mapping warehouse names to their total silver values.
        """
        latest: Dict[str, int] = {}
        for item in state.warehouse_snapshots:
            latest[item.warehouse] = item.market_silver
        return latest

    def warehouses_total(self, state: AppState) -> int:
        """Calculate total silver across all warehouses.

        Args:
            state: Current application state.

        Returns:
            Total silver value across all warehouses.
        """
        return sum(self.get_warehouse_totals(state).values())

    def latest_inventory(self, state: AppState) -> int:
        """Get the most recent inventory silver value.

        Args:
            state: Current application state.

        Returns:
            Most recent inventory silver value, or 0 if none found.
        """
        for item in reversed(state.records):
            if item.inventory_silver is not None:
                return item.inventory_silver
        return 0

    def latest_market(self, state: AppState) -> int:
        """Get the most recent market silver value.

        Args:
            state: Current application state.

        Returns:
            Most recent market silver value, or 0 if none found.
        """
        for item in reversed(state.records):
            if item.market_silver is not None:
                return item.market_silver
        return 0

    def latest_preorder(self, state: AppState) -> int:
        """Get the most recent preorder silver value.

        Args:
            state: Current application state.

        Returns:
            Most recent preorder silver value, or 0 if none found.
        """
        for item in reversed(state.records):
            return item.preorder_silver
        return 0

    def append_record(
        self,
        state: AppState,
        market_silver: Optional[int],
        inventory_silver: Optional[int],
        preorder_silver: int,
        source: str,
        details: Dict[str, Any]
    ) -> RecordItem:
        """Append a new asset record to the state.

        Args:
            state: Current application state.
            market_silver: Market silver value (optional).
            inventory_silver: Inventory silver value (optional).
            preorder_silver: Preorder silver value.
            source: Source of the record (e.g., 'ocr', 'manual').
            details: Additional details about the record.

        Returns:
            The newly created record item.
        """
        warehouses_total = self.warehouses_total(state)
        total_without_warehouses = (market_silver or self.latest_market(state)) + \
                                   (inventory_silver if inventory_silver is not None else self.latest_inventory(state)) + \
                                   preorder_silver
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

        self._broadcast_update('asset_history_updated', {
            'dashboard': self.dashboard()
        })

        return record

    def add_manual_record(self, market_silver: Optional[int], inventory_silver: Optional[int], preorder_silver: int) -> RecordItem:
        """Add a manual asset record.

        Args:
            market_silver: Market silver value (optional).
            inventory_silver: Inventory silver value (optional).
            preorder_silver: Preorder silver value.

        Returns:
            The created record item.
        """
        state = self.get_state()
        return self.append_record(state, market_silver, inventory_silver, preorder_silver, 'manual', {})

    def add_inventory_capture(self, inventory_silver: int) -> RecordItem:
        """Add an inventory capture record from OCR.

        Args:
            inventory_silver: Detected inventory silver value.

        Returns:
            The created record item.
        """
        state = self.get_state()
        preorder_silver = self.latest_preorder(state)
        market_silver = self.latest_market(state)
        return self.append_record(state, market_silver, inventory_silver, preorder_silver, 'ocr-inventory', {})

    def add_market_inventory_capture(
        self,
        market_silver: Optional[int],
        inventory_silver: Optional[int]
    ) -> RecordItem:
        """Add a combined market and inventory capture record from OCR.

        Args:
            market_silver: Detected market silver value.
            inventory_silver: Detected inventory silver value.

        Returns:
            The created record item.
        """
        state = self.get_state()
        preorder_silver = self.latest_preorder(state)
        return self.append_record(
            state,
            market_silver,
            inventory_silver,
            preorder_silver,
            'ocr-market-inventory',
            {}
        )

    def add_preorder(self, preorder_silver: int, source: str, details: Optional[Dict[str, Any]] = None) -> RecordItem:
        """Add a preorder record.

        Args:
            preorder_silver: Preorder silver value.
            source: Source identifier for the preorder.
            details: Additional preorder metadata.

        Returns:
            The created record item.
        """
        state = self.get_state()
        return self.append_record(
            state,
            self.latest_market(state),
            self.latest_inventory(state),
            preorder_silver,
            source,
            details or {}
        )

    def add_storage_capture(self, warehouse: str, market_silver: int) -> tuple[WarehouseSnapshot, Optional[RecordItem]]:
        """Add a warehouse storage capture record.

        Args:
            warehouse: Warehouse name.
            market_silver: Detected market silver value for the warehouse.

        Returns:
            Tuple of (warehouse snapshot, optional record if warehouse changed).
        """
        state = self.get_state()
        previous_name = state.warehouse_snapshots[-1].warehouse if state.warehouse_snapshots else None
        changed = previous_name != warehouse
        snapshot = WarehouseSnapshot(captured_at=now_iso(), warehouse=warehouse, market_silver=market_silver)
        state.warehouse_snapshots.append(snapshot)
        storage.write_state(state)

        self._broadcast_update('asset_history_updated', {
            'dashboard': self.dashboard()
        })

        record = None
        if changed:
            record = self.append_record(
                state,
                self.latest_market(state),
                self.latest_inventory(state),
                self.latest_preorder(state),
                'ocr-storage',
                {'warehouse': warehouse}
            )
        return snapshot, record

    def add_manual_warehouse_value(self, warehouse: str, market_silver: int) -> RecordItem:
        """Add a manual warehouse value correction.

        Args:
            warehouse: Warehouse name.
            market_silver: Manual warehouse silver value.

        Returns:
            The created record item.
        """
        state = self.get_state()

        snapshot = WarehouseSnapshot(
            captured_at=now_iso(),
            warehouse=warehouse,
            market_silver=market_silver,
        )
        state.warehouse_snapshots.append(snapshot)
        storage.write_state(state)

        record = self.append_record(
            state,
            self.latest_market(state),
            self.latest_inventory(state),
            self.latest_preorder(state),
            'manual-storage',
            {
                'warehouse': warehouse,
                'manual': True,
            }
        )

        return record

    def dashboard(self) -> Dict[str, Any]:
        """Get dashboard data for the frontend.

        Returns:
            Dictionary containing latest record, records, warehouses, and settings.
        """
        state = self.get_state()
        latest = state.records[-1] if state.records else None
        warehouse_totals = self.get_warehouse_totals(state)
        latest_snapshot_by_warehouse: Dict[str, WarehouseSnapshot] = {}

        for snapshot in state.warehouse_snapshots:
            latest_snapshot_by_warehouse[snapshot.warehouse] = snapshot

        warehouse_status_list = []
        missing_warehouses = []

        for warehouse in KNOWN_STORAGES:
            snapshot = latest_snapshot_by_warehouse.get(warehouse)

            if snapshot is None:
                warehouse_status_list.append(
                    {
                        'warehouse': warehouse,
                        'market_silver': None,
                        'last_captured_at': None,
                        'updated': False,
                    }
                )
                missing_warehouses.append(warehouse)
            else:
                warehouse_status_list.append(
                    {
                        'warehouse': warehouse,
                        'market_silver': snapshot.market_silver,
                        'last_captured_at': snapshot.captured_at,
                        'updated': True,
                    }
                )

        return {
            'latest': latest.model_dump() if latest else None,
            'records': [r.model_dump() for r in state.records[-50:]],  # Last 50 records
            'warehouse_totals': warehouse_totals,
            'warehouse_list': [
                {'warehouse': warehouse, 'market_silver': value}
                for warehouse, value in warehouse_totals.items()
            ],
            'warehouse_snapshots': [s.model_dump() for s in state.warehouse_snapshots[-200:]],
            'warehouse_status_list': warehouse_status_list,
            'missing_warehouses': missing_warehouses,
            'settings': state.settings,
        }

    def toggle_include_warehouses(self, include: bool) -> AppState:
        """Toggle whether warehouses are included in total calculations.

        Args:
            include: Whether to include warehouses in totals.

        Returns:
            Updated application state.
        """
        state = self.get_state()
        state.settings['include_warehouses_in_total'] = include
        storage.write_state(state)
        self._broadcast_update('asset_history_updated', {
            'dashboard': self.dashboard()
        })
        return state