from pymongo import MongoClient, ASCENDING

from app.config import MONGODB_URL, DATABASE_NAME
from app.models import AppState, RecordItem, WarehouseSnapshot
from app.utils.time import now_iso


class MongoDBStorage:
    """Synchronous MongoDB storage compatible with AssetService."""

    def __init__(self) -> None:
        client = MongoClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        self._records = db.records
        self._snapshots = db.warehouse_snapshots
        self._settings = db.settings

        self._records.create_index([('captured_at', ASCENDING)], name='idx_records_captured_at_asc')
        self._snapshots.create_index([('captured_at', ASCENDING)], name='idx_snapshots_captured_at_asc')

    def read_state(self) -> AppState:
        records = [RecordItem(**doc) for doc in self._records.find({}, {'_id': 0}).sort('captured_at', ASCENDING)]
        warehouse_snapshots = [
            WarehouseSnapshot(**doc)
            for doc in self._snapshots.find({}, {'_id': 0}).sort('captured_at', ASCENDING)
        ]
        settings_doc = self._settings.find_one({'_id': 'app_settings'})
        settings = settings_doc.get('settings', {}) if settings_doc else {'include_warehouses_in_total': True}

        return AppState(
            records=records,
            warehouse_snapshots=warehouse_snapshots,
            settings=settings,
        )

    def write_state(self, state: AppState) -> None:
        now = now_iso()
        self._records.delete_many({})
        self._snapshots.delete_many({})

        if state.records:
            self._records.insert_many([item.model_dump() for item in state.records])

        if state.warehouse_snapshots:
            self._snapshots.insert_many([item.model_dump() for item in state.warehouse_snapshots])

        self._settings.update_one(
            {'_id': 'app_settings'},
            {
                '$set': {
                    'settings': state.settings,
                    'updated_at': now,
                },
                '$setOnInsert': {
                    'created_at': now,
                },
            },
            upsert=True,
        )


storage = MongoDBStorage()