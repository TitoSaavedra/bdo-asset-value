from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.config import HISTORY_RETENTION_DAYS
from app.models import RecordItem
from app.services.time_utils import parse_iso


class AssetServiceCompactionMixin:
    """History compaction and retention logic."""

    def compact_history(self, retention_days: Optional[int] = None) -> Dict[str, int]:
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

        if merged_count > 0 or pruned_count > 0:
            self._register_action(
                action_type='history-compaction',
                source='system-compactor',
                details={
                    'before': original_len,
                    'after': after_len,
                    'merged': merged_count,
                    'pruned': pruned_count,
                },
            )

        return {
            'before': original_len,
            'after': after_len,
            'merged': merged_count,
            'pruned': pruned_count,
        }
