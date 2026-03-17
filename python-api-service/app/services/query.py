import json
from datetime import datetime, timedelta
from time import perf_counter
from typing import Any, Dict, List, Tuple

from app.models import AppState, RecordItem, WarehouseSnapshot
from app.services.time_utils import parse_iso


class AssetServiceQueryMixin:
    """Query, dashboard and range/filter related methods."""

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

        known = self.get_known_storages()
        known_keys = {item.lower(): item for item in known}
        snapshot_keys = {item.lower(): item for item in latest_snapshot_by_warehouse.keys()}
        merged_keys = sorted(set(known_keys.keys()) | set(snapshot_keys.keys()))

        warehouse_status_list: List[Dict[str, Any]] = []
        missing_warehouses: List[str] = []

        for key in merged_keys:
            warehouse = known_keys.get(key) or snapshot_keys.get(key) or key
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
        state = self.get_state()
        records = self._filter_records_by_range(state.records, range_name)
        records_desc = list(reversed(records))

        safe_limit = self._sanitize_limit(limit=limit, max_limit=200)
        safe_offset = self._sanitize_offset(offset=offset)

        paginated = records_desc[safe_offset:safe_offset + safe_limit]
        return {
            'items': [item.model_dump() for item in paginated],
            'total': len(records_desc),
            'limit': safe_limit,
            'offset': safe_offset,
            'range': range_name,
        }

    def get_snapshots_page(self, limit: int, offset: int) -> Dict[str, Any]:
        state = self.get_state()
        snapshots_desc = list(reversed(state.warehouse_snapshots))

        safe_limit = self._sanitize_limit(limit=limit, max_limit=200)
        safe_offset = self._sanitize_offset(offset=offset)
        paginated = snapshots_desc[safe_offset:safe_offset + safe_limit]

        return {
            'items': [item.model_dump() for item in paginated],
            'total': len(snapshots_desc),
            'limit': safe_limit,
            'offset': safe_offset,
        }

    def dashboard(self, history_limit: int = 50, snapshots_limit: int = 200) -> Dict[str, Any]:
        safe_history_limit = self._sanitize_limit(limit=history_limit, max_limit=300)
        safe_snapshots_limit = self._sanitize_limit(limit=snapshots_limit, max_limit=500)
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
                'expires_at': now + timedelta(seconds=self._dashboard_cache_ttl_seconds),
                'payload': payload,
            }

        return payload

    def toggle_include_warehouses(self, include: bool) -> AppState:
        state = self.get_state()
        state.settings['include_warehouses_in_total'] = include
        self._write_state(state)
        self._register_action(
            action_type='settings-change',
            source='manual',
            details={
                'include_warehouses_in_total': include,
            },
        )
        self._broadcast_update('asset_history_updated', {
            'dashboard': self.dashboard()
        })
        return state
