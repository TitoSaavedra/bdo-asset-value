import asyncio
import json
from collections import deque
from datetime import datetime, timedelta
from threading import Lock
from time import perf_counter
from typing import Optional, Dict, Any, List, Tuple
from app.models import AppState, RecordItem, WarehouseSnapshot
from app.ocr.config.storages import KNOWN_STORAGES
from app.storage import storage
from app.config import DASHBOARD_CACHE_TTL_SECONDS, HISTORY_RETENTION_DAYS


def now_iso() -> str:
    """Get current timestamp in ISO format.

    Returns:
        str: Current timestamp in ISO format with seconds precision.
    """
    return datetime.now().isoformat(timespec='seconds')


def parse_iso(value: str) -> Optional[datetime]:
    """Parse ISO timestamps safely.

    Args:
        value: ISO timestamp string.

    Returns:
        Parsed datetime when valid, otherwise None.
    """
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (TypeError, ValueError, AttributeError):
        return None


class AssetService:
    """Service class for managing Black Desert Online asset tracking operations."""

    def __init__(self) -> None:
        self._cache_lock = Lock()
        self._dashboard_cache: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self._metrics_lock = Lock()
        self._dashboard_render_ms_last: float = 0.0
        self._dashboard_render_ms_avg: float = 0.0
        self._dashboard_payload_bytes_last: int = 0
        self._dashboard_calls: int = 0
        self._writes_total: int = 0
        self._write_timestamps: deque[datetime] = deque(maxlen=5000)

    def _invalidate_dashboard_cache(self) -> None:
        with self._cache_lock:
            self._dashboard_cache.clear()

    def _register_write(self) -> None:
        with self._metrics_lock:
            self._writes_total += 1
            self._write_timestamps.append(datetime.now())

    def _write_state(self, state: AppState) -> None:
        storage.write_state(state)
        self._register_write()
        self._invalidate_dashboard_cache()

    def _filter_records_by_range(self, records: List[RecordItem], range_name: str) -> List[RecordItem]:
        if range_name == 'all':
            return records

        now = datetime.now()
        if range_name == 'today':
            threshold = datetime(now.year, now.month, now.day)
        elif range_name == '7d':
            threshold = now - timedelta(days=7)
        elif range_name == '30d':
            threshold = now - timedelta(days=30)
        else:
            return records

        filtered: List[RecordItem] = []
        for item in records:
            parsed = parse_iso(item.captured_at)
            if parsed and parsed >= threshold:
                filtered.append(item)
        return filtered

    def _compute_warehouse_status(self, state: AppState) -> Tuple[List[Dict[str, Any]], List[str]]:
        latest_snapshot_by_warehouse: Dict[str, WarehouseSnapshot] = {}
        for snapshot in state.warehouse_snapshots:
            latest_snapshot_by_warehouse[snapshot.warehouse] = snapshot

        warehouse_status_list: List[Dict[str, Any]] = []
        missing_warehouses: List[str] = []

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

        return warehouse_status_list, missing_warehouses

    def _build_dashboard_payload(
        self,
        state: AppState,
        history_limit: int,
        snapshots_limit: int,
    ) -> Dict[str, Any]:
        latest = state.records[-1] if state.records else None
        warehouse_totals = self.get_warehouse_totals(state)
        warehouse_status_list, missing_warehouses = self._compute_warehouse_status(state)

        return {
            'latest': latest.model_dump() if latest else None,
            'records': [r.model_dump() for r in state.records[-history_limit:]],
            'warehouse_totals': warehouse_totals,
            'warehouse_list': [
                {'warehouse': warehouse, 'market_silver': value}
                for warehouse, value in warehouse_totals.items()
            ],
            'warehouse_snapshots': [s.model_dump() for s in state.warehouse_snapshots[-snapshots_limit:]],
            'warehouse_status_list': warehouse_status_list,
            'missing_warehouses': missing_warehouses,
            'settings': state.settings,
        }

    def _record_dashboard_metrics(self, started_at: float, payload: Dict[str, Any]) -> None:
        elapsed_ms = (perf_counter() - started_at) * 1000
        payload_bytes = len(json.dumps(payload, ensure_ascii=False))

        with self._metrics_lock:
            self._dashboard_calls += 1
            self._dashboard_render_ms_last = elapsed_ms
            self._dashboard_payload_bytes_last = payload_bytes
            if self._dashboard_calls == 1:
                self._dashboard_render_ms_avg = elapsed_ms
            else:
                prev = self._dashboard_render_ms_avg
                count = self._dashboard_calls
                self._dashboard_render_ms_avg = prev + (elapsed_ms - prev) / count

    def get_history_page(self, limit: int, offset: int, range_name: str = 'all') -> Dict[str, Any]:
        """Return paginated history records.

        Args:
            limit: Number of items per page.
            offset: Pagination offset.
            range_name: Time range filter (all, today, 7d, 30d).

        Returns:
            Dictionary with paginated records and total count.
        """
        state = self.get_state()
        records = self._filter_records_by_range(state.records, range_name)
        records_desc = list(reversed(records))

        safe_limit = max(1, min(limit, 200))
        safe_offset = max(0, offset)

        paginated = records_desc[safe_offset:safe_offset + safe_limit]
        return {
            'items': [item.model_dump() for item in paginated],
            'total': len(records_desc),
            'limit': safe_limit,
            'offset': safe_offset,
            'range': range_name,
        }

    def get_snapshots_page(self, limit: int, offset: int) -> Dict[str, Any]:
        """Return paginated warehouse snapshots in descending date order."""
        state = self.get_state()
        snapshots_desc = list(reversed(state.warehouse_snapshots))

        safe_limit = max(1, min(limit, 200))
        safe_offset = max(0, offset)
        paginated = snapshots_desc[safe_offset:safe_offset + safe_limit]

        return {
            'items': [item.model_dump() for item in paginated],
            'total': len(snapshots_desc),
            'limit': safe_limit,
            'offset': safe_offset,
        }

    def compact_history(self, retention_days: Optional[int] = None) -> Dict[str, int]:
        """Compact history by merging duplicates per hour and pruning old records.

        Args:
            retention_days: Days to keep; <= 0 disables pruning.

        Returns:
            Summary dictionary of compaction effects.
        """
        state = self.get_state()
        original_len = len(state.records)
        if original_len == 0:
            return {'before': 0, 'after': 0, 'merged': 0, 'pruned': 0}

        effective_retention = HISTORY_RETENTION_DAYS if retention_days is None else retention_days
        cutoff: Optional[datetime] = None
        if effective_retention and effective_retention > 0:
            cutoff = datetime.now() - timedelta(days=effective_retention)

        compacted: List[RecordItem] = []
        merged_count = 0

        for record in state.records:
            parsed = parse_iso(record.captured_at)
            if cutoff and parsed and parsed < cutoff:
                continue

            if not compacted:
                compacted.append(record)
                continue

            previous = compacted[-1]
            prev_dt = parse_iso(previous.captured_at)
            curr_dt = parse_iso(record.captured_at)
            same_hour = bool(
                prev_dt and curr_dt and
                prev_dt.year == curr_dt.year and
                prev_dt.month == curr_dt.month and
                prev_dt.day == curr_dt.day and
                prev_dt.hour == curr_dt.hour
            )
            same_silver = (
                previous.total_without_warehouses == record.total_without_warehouses and
                previous.total_with_warehouses == record.total_with_warehouses and
                previous.preorder_silver == record.preorder_silver and
                previous.warehouses_total == record.warehouses_total
            )

            if same_hour and same_silver:
                merged_count += 1
                merged_sources = list(previous.details.get('merged_sources', []))
                if previous.source not in merged_sources:
                    merged_sources.append(previous.source)
                if record.source not in merged_sources:
                    merged_sources.append(record.source)

                previous.captured_at = record.captured_at
                previous.details = {
                    **previous.details,
                    'merged_count': int(previous.details.get('merged_count', 1)) + 1,
                    'merged_sources': merged_sources,
                }
            else:
                compacted.append(record)

        state.records = compacted
        after_len = len(compacted)
        pruned_count = max(0, original_len - after_len - merged_count)

        if after_len != original_len:
            self._write_state(state)

        return {
            'before': original_len,
            'after': after_len,
            'merged': merged_count,
            'pruned': pruned_count,
        }

    def metrics(self) -> Dict[str, Any]:
        """Return basic service runtime metrics for diagnostics."""
        now = datetime.now()
        with self._metrics_lock:
            one_minute_ago = now - timedelta(minutes=1)
            writes_last_minute = sum(1 for ts in self._write_timestamps if ts >= one_minute_ago)

            return {
                'dashboard_render_ms_last': round(self._dashboard_render_ms_last, 2),
                'dashboard_render_ms_avg': round(self._dashboard_render_ms_avg, 2),
                'dashboard_payload_bytes_last': self._dashboard_payload_bytes_last,
                'dashboard_calls': self._dashboard_calls,
                'writes_total': self._writes_total,
                'writes_per_minute': writes_last_minute,
            }

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
        captured_at = now_iso()
        warehouses_total = self.warehouses_total(state)
        effective_market = market_silver if market_silver is not None else self.latest_market(state)
        effective_inventory = inventory_silver if inventory_silver is not None else self.latest_inventory(state)

        total_without_warehouses = effective_market + \
                                   effective_inventory + \
                                   preorder_silver
        total_with_warehouses = total_without_warehouses + warehouses_total

        if state.records:
            last = state.records[-1]
            last_dt = parse_iso(last.captured_at)
            current_dt = parse_iso(captured_at)

            same_hour_window = bool(
                last_dt and current_dt and
                last_dt.year == current_dt.year and
                last_dt.month == current_dt.month and
                last_dt.day == current_dt.day and
                last_dt.hour == current_dt.hour
            )

            same_silver = (
                last.total_without_warehouses == total_without_warehouses and
                last.total_with_warehouses == total_with_warehouses and
                last.preorder_silver == preorder_silver and
                last.warehouses_total == warehouses_total
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
        self._write_state(state)

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
        self._write_state(state)

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

    def dashboard(self, history_limit: int = 50, snapshots_limit: int = 200) -> Dict[str, Any]:
        """Get dashboard data with short-lived cache.

        Args:
            history_limit: Number of history records to include.
            snapshots_limit: Number of snapshot rows to include.

        Returns:
            Dictionary containing latest records, warehouses, and settings.
        """
        safe_history_limit = max(1, min(history_limit, 300))
        safe_snapshots_limit = max(1, min(snapshots_limit, 500))
        cache_key = (safe_history_limit, safe_snapshots_limit)
        now = datetime.now()

        with self._cache_lock:
            cached = self._dashboard_cache.get(cache_key)
            if cached and cached['expires_at'] > now:
                return cached['payload']

        started_at = perf_counter()
        state = self.get_state()
        payload = self._build_dashboard_payload(state, safe_history_limit, safe_snapshots_limit)

        self._record_dashboard_metrics(started_at, payload)

        with self._cache_lock:
            self._dashboard_cache[cache_key] = {
                'expires_at': now + timedelta(seconds=DASHBOARD_CACHE_TTL_SECONDS),
                'payload': payload,
            }

        return payload

    def toggle_include_warehouses(self, include: bool) -> AppState:
        """Toggle whether warehouses are included in total calculations.

        Args:
            include: Whether to include warehouses in totals.

        Returns:
            Updated application state.
        """
        state = self.get_state()
        state.settings['include_warehouses_in_total'] = include
        self._write_state(state)
        self._broadcast_update('asset_history_updated', {
            'dashboard': self.dashboard()
        })
        return state