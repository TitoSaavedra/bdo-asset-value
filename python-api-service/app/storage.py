import json
from json import JSONDecodeError
from pymongo import MongoClient, ASCENDING

from app.config import DATA_FILE, MONGODB_URL, DATABASE_NAME
from app.models import AppState, RecordItem, WarehouseSnapshot
from app.utils.time import now_iso


class JSONStorage:
    """JSON historical storage used only for migration scripts."""

    def read_state(self) -> AppState:
        if not DATA_FILE.exists():
            state = AppState()
            self.write_state(state)
            return state

        content = DATA_FILE.read_text(encoding='utf-8')

        try:
            raw = json.loads(content)
        except JSONDecodeError as exc:
            if exc.msg == 'Extra data':
                decoder = json.JSONDecoder()
                raw, end_index = decoder.raw_decode(content)
                trailing = content[end_index:].strip()
                if trailing:
                    DATA_FILE.write_text(
                        json.dumps(raw, ensure_ascii=False, indent=2),
                        encoding='utf-8'
                    )
            else:
                raise

        return AppState(**raw)

    def write_state(self, state: AppState) -> None:
        DATA_FILE.write_text(state.model_dump_json(indent=2), encoding='utf-8')


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