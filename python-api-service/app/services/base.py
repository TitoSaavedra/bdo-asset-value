import asyncio
import json
from collections import deque
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Tuple

from app.config import DASHBOARD_CACHE_TTL_SECONDS
from app.models import AppState
from app.storage import storage
from app.services.time_utils import now_iso


class AssetServiceBase:
    """Base state, cache, metrics and shared helpers for asset services."""

    def __init__(self) -> None:
        self._cache_lock = Lock()
        self._known_storages_lock = Lock()
        self._dashboard_cache: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self._known_storages: List[str] = []
        self._metrics_lock = Lock()
        self._actions_lock = Lock()
        self._recent_actions: deque[Dict[str, Any]] = deque(maxlen=300)
        self._dashboard_render_ms_last: float = 0.0
        self._dashboard_render_ms_avg: float = 0.0
        self._dashboard_payload_bytes_last: int = 0
        self._dashboard_calls: int = 0
        self._writes_total: int = 0
        self._write_timestamps: deque[datetime] = deque(maxlen=5000)
        self._dashboard_cache_ttl_seconds: float = DASHBOARD_CACHE_TTL_SECONDS

    def _register_action(self, action_type: str, source: str, details: Dict[str, Any] | None = None) -> None:
        with self._actions_lock:
            self._recent_actions.appendleft(
                {
                    'timestamp': now_iso(),
                    'action_type': action_type,
                    'source': source,
                    'details': details or {},
                }
            )

    def get_recent_actions(self, limit: int = 30) -> Dict[str, Any]:
        safe_limit = max(1, min(limit, 200))
        with self._actions_lock:
            items = list(self._recent_actions)[:safe_limit]
        return {
            'items': items,
            'total': len(items),
            'limit': safe_limit,
        }

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

    def set_known_storages(self, storages: List[str]) -> None:
        normalized: Dict[str, str] = {}
        for item in storages:
            clean = item.strip()
            if clean:
                normalized[clean.lower()] = clean

        with self._known_storages_lock:
            self._known_storages = sorted(normalized.values())

    def add_known_storage(self, storage_name: str) -> None:
        clean = storage_name.strip()
        if not clean:
            return

        with self._known_storages_lock:
            by_key = {item.lower(): item for item in self._known_storages}
            by_key[clean.lower()] = clean
            self._known_storages = sorted(by_key.values())

    def get_known_storages(self) -> List[str]:
        with self._known_storages_lock:
            return list(self._known_storages)

    def _broadcast_update(self, event_type: str, data: Dict[str, Any]) -> None:
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
        return storage.read_state()

    def get_warehouse_totals(self, state: AppState) -> Dict[str, int]:
        latest: Dict[str, int] = {}
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

    def metrics(self) -> Dict[str, Any]:
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
