from typing import Any, Dict, Optional

from app.models import AppState, RecordItem, WarehouseSnapshot
from app.services.record_merge import has_same_totals, is_same_hour_window
from app.services.time_utils import now_iso


class AssetServiceRecordsMixin:
    """Record and warehouse mutation methods."""

    def append_record(
        self,
        state: AppState,
        market_silver: Optional[int],
        inventory_silver: Optional[int],
        preorder_silver: int,
        source: str,
        details: Dict[str, Any],
    ) -> RecordItem:
        captured_at = now_iso()
        warehouses_total = self.warehouses_total(state)
        effective_market = market_silver if market_silver is not None else self.latest_market(state)
        effective_inventory = inventory_silver if inventory_silver is not None else self.latest_inventory(state)

        total_without_warehouses = effective_market + effective_inventory + preorder_silver
        total_with_warehouses = total_without_warehouses + warehouses_total

        if state.records:
            last = state.records[-1]
            same_hour_window = is_same_hour_window(last.captured_at, captured_at)

            same_silver = has_same_totals(
                previous_total_without_warehouses=last.total_without_warehouses,
                previous_total_with_warehouses=last.total_with_warehouses,
                previous_preorder_silver=last.preorder_silver,
                previous_warehouses_total=last.warehouses_total,
                current_total_without_warehouses=total_without_warehouses,
                current_total_with_warehouses=total_with_warehouses,
                current_preorder_silver=preorder_silver,
                current_warehouses_total=warehouses_total,
            )

            if same_hour_window and same_silver:
                merged_count = int(last.details.get('merged_count', 1)) + 1
                merged_sources = list(last.details.get('merged_sources', []))
                if source not in merged_sources:
                    merged_sources.append(source)

                last.captured_at = captured_at
                last.details = {
                    **last.details,
                    'merged_count': merged_count,
                    'merged_sources': merged_sources,
                }
                self._write_state(state)
                self._register_action(
                    action_type='record-merged',
                    source=source,
                    details={
                        'captured_at': captured_at,
                        'total_with_warehouses': total_with_warehouses,
                        'total_without_warehouses': total_without_warehouses,
                    },
                )

                self._broadcast_update('asset_history_updated', {
                    'dashboard': self.dashboard()
                })

                return last

        record = RecordItem(
            captured_at=captured_at,
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
        self._write_state(state)
        self._register_action(
            action_type='record-added',
            source=source,
            details={
                'captured_at': captured_at,
                'total_with_warehouses': total_with_warehouses,
                'total_without_warehouses': total_without_warehouses,
            },
        )

        self._broadcast_update('asset_history_updated', {
            'dashboard': self.dashboard()
        })

        return record

    def add_manual_record(
        self,
        market_silver: Optional[int],
        inventory_silver: Optional[int],
        preorder_silver: int,
    ) -> RecordItem:
        state = self.get_state()
        return self.append_record(state, market_silver, inventory_silver, preorder_silver, 'manual', {})

    def add_inventory_capture(self, inventory_silver: int) -> RecordItem:
        state = self.get_state()
        preorder_silver = self.latest_preorder(state)
        market_silver = self.latest_market(state)
        return self.append_record(state, market_silver, inventory_silver, preorder_silver, 'ocr-inventory', {})

    def add_market_inventory_capture(
        self,
        market_silver: Optional[int],
        inventory_silver: Optional[int],
    ) -> RecordItem:
        state = self.get_state()
        preorder_silver = self.latest_preorder(state)
        return self.append_record(
            state,
            market_silver,
            inventory_silver,
            preorder_silver,
            'ocr-market-inventory',
            {},
        )

    def add_preorder(self, preorder_silver: int, source: str, details: Optional[Dict[str, Any]] = None) -> RecordItem:
        state = self.get_state()
        return self.append_record(
            state,
            self.latest_market(state),
            self.latest_inventory(state),
            preorder_silver,
            source,
            details or {},
        )

    def add_storage_capture(self, warehouse: str, market_silver: int) -> tuple[WarehouseSnapshot, Optional[RecordItem]]:
        state = self.get_state()
        previous_name = state.warehouse_snapshots[-1].warehouse if state.warehouse_snapshots else None
        changed = previous_name != warehouse
        snapshot = WarehouseSnapshot(captured_at=now_iso(), warehouse=warehouse, market_silver=market_silver)
        state.warehouse_snapshots.append(snapshot)
        self._write_state(state)
        self._register_action(
            action_type='storage-capture',
            source='ocr-storage',
            details={
                'warehouse': warehouse,
                'market_silver': market_silver,
            },
        )

        record = None
        if changed:
            record = self.append_record(
                state,
                self.latest_market(state),
                self.latest_inventory(state),
                self.latest_preorder(state),
                'ocr-storage',
                {'warehouse': warehouse},
            )
        else:
            self._broadcast_update('asset_history_updated', {
                'dashboard': self.dashboard()
            })

        return snapshot, record

    def add_manual_warehouse_value(self, warehouse: str, market_silver: int) -> RecordItem:
        state = self.get_state()

        snapshot = WarehouseSnapshot(
            captured_at=now_iso(),
            warehouse=warehouse,
            market_silver=market_silver,
        )
        state.warehouse_snapshots.append(snapshot)
        self._write_state(state)
        self._register_action(
            action_type='manual-warehouse-change',
            source='manual-storage',
            details={
                'warehouse': warehouse,
                'market_silver': market_silver,
            },
        )

        record = self.append_record(
            state,
            self.latest_market(state),
            self.latest_inventory(state),
            self.latest_preorder(state),
            'manual-storage',
            {
                'warehouse': warehouse,
                'manual': True,
            },
        )

        return record
