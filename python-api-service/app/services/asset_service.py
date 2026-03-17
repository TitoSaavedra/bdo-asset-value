from app.services.base import AssetServiceBase
from app.services.compaction import AssetServiceCompactionMixin
from app.services.query import AssetServiceQueryMixin
from app.services.records import AssetServiceRecordsMixin


class AssetService(
    AssetServiceCompactionMixin,
    AssetServiceQueryMixin,
    AssetServiceRecordsMixin,
    AssetServiceBase,
):
    """Composed service orchestrating all API business logic."""

    pass
