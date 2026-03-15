import json
from typing import List, Dict, Any
from app.config import DATA_FILE
from app.models import AppState, RecordItem, WarehouseSnapshot
from app.database import records_collection, warehouse_snapshots_collection, settings_collection


class JSONStorage:
    """Legacy JSON-based storage for backward compatibility"""

    def read_state(self) -> AppState:
        if not DATA_FILE.exists():
            state = AppState()
            self.write_state(state)
            return state
        raw = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        return AppState(**raw)

    def write_state(self, state: AppState) -> None:
        DATA_FILE.write_text(state.model_dump_json(indent=2), encoding='utf-8')


class MongoDBStorage:
    """MongoDB-based storage for production use"""

    async def read_state(self) -> AppState:
        # Get all records
        records_cursor = records_collection.find().sort('captured_at', -1)
        records = [RecordItem(**doc) async for doc in records_cursor]

        # Get all warehouse snapshots
        snapshots_cursor = warehouse_snapshots_collection.find().sort('captured_at', -1)
        warehouse_snapshots = [WarehouseSnapshot(**doc) async for doc in snapshots_cursor]

        # Get settings
        settings_doc = await settings_collection.find_one({'_id': 'app_settings'})
        settings = settings_doc.get('settings', {}) if settings_doc else {'include_warehouses_in_total': True}

        return AppState(
            records=records,
            warehouse_snapshots=warehouse_snapshots,
            settings=settings
        )

    async def write_record(self, record: RecordItem) -> None:
        await records_collection.insert_one(record.model_dump())

    async def write_warehouse_snapshot(self, snapshot: WarehouseSnapshot) -> None:
        await warehouse_snapshots_collection.insert_one(snapshot.model_dump())

    async def update_settings(self, settings: Dict[str, Any]) -> None:
        await settings_collection.update_one(
            {'_id': 'app_settings'},
            {'$set': {'settings': settings}},
            upsert=True
        )

    async def get_latest_records(self, limit: int = 50) -> List[RecordItem]:
        cursor = records_collection.find().sort('captured_at', -1).limit(limit)
        return [RecordItem(**doc) async for doc in cursor]

    async def get_warehouse_snapshots(self, warehouse: str = None) -> List[WarehouseSnapshot]:
        query = {'warehouse': warehouse} if warehouse else {}
        cursor = warehouse_snapshots_collection.find(query).sort('captured_at', -1)
        return [WarehouseSnapshot(**doc) async for doc in cursor]


# Default storage instance - change to MongoDBStorage() when ready to migrate
storage = JSONStorage()

# For async operations, use:
# storage = MongoDBStorage()