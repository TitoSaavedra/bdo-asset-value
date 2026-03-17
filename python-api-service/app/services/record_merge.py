from app.models import RecordItem
from app.utils.time import parse_iso


def is_same_hour_window(previous_captured_at: str, current_captured_at: str) -> bool:
    """Return True when both timestamps are in the same year/month/day/hour."""
    previous_dt = parse_iso(previous_captured_at)
    current_dt = parse_iso(current_captured_at)
    return bool(
        previous_dt and current_dt
        and previous_dt.year == current_dt.year
        and previous_dt.month == current_dt.month
        and previous_dt.day == current_dt.day
        and previous_dt.hour == current_dt.hour
    )


def has_same_totals(
    previous_total_without_warehouses: int,
    previous_total_with_warehouses: int,
    previous_preorder_silver: int,
    previous_warehouses_total: int,
    current_total_without_warehouses: int,
    current_total_with_warehouses: int,
    current_preorder_silver: int,
    current_warehouses_total: int,
) -> bool:
    """Return True when aggregate values are equal for merge purposes."""
    return (
        previous_total_without_warehouses == current_total_without_warehouses
        and previous_total_with_warehouses == current_total_with_warehouses
        and previous_preorder_silver == current_preorder_silver
        and previous_warehouses_total == current_warehouses_total
    )


def should_merge_record(previous: RecordItem, current: RecordItem) -> bool:
    """Return True when two records are merge-compatible."""
    return is_same_hour_window(previous.captured_at, current.captured_at) and has_same_totals(
        previous_total_without_warehouses=previous.total_without_warehouses,
        previous_total_with_warehouses=previous.total_with_warehouses,
        previous_preorder_silver=previous.preorder_silver,
        previous_warehouses_total=previous.warehouses_total,
        current_total_without_warehouses=current.total_without_warehouses,
        current_total_with_warehouses=current.total_with_warehouses,
        current_preorder_silver=current.preorder_silver,
        current_warehouses_total=current.warehouses_total,
    )