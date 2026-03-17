import asyncio
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
API_SERVICE_DIR = BASE_DIR / 'python-api-service'
if str(API_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_DIR))

from app.storage import JSONStorage
from app.database import (
    records_collection,
    warehouse_snapshots_collection,
    settings_collection,
    storage_names_collection,
    normalize_storage_name,
)
from app.utils.time import now_iso


async def migrate_to_mongodb():
    """Migrate data from JSON to MongoDB"""

    # Read current JSON data
    json_storage = JSONStorage()
    state = json_storage.read_state()

    print(f"Migrating {len(state.records)} records and {len(state.warehouse_snapshots)} warehouse snapshots...")

    # Clear existing MongoDB data (optional, for clean migration)
    await records_collection.delete_many({})
    await warehouse_snapshots_collection.delete_many({})
    await settings_collection.delete_many({})
    await storage_names_collection.delete_many({})

    # Insert records
    if state.records:
        records_data = []
        for record in state.records:
            payload = record.model_dump()
            captured_at = payload.get('captured_at')
            payload['created_at'] = payload.get('created_at') or captured_at or now_iso()
            payload['updated_at'] = payload.get('updated_at') or captured_at or now_iso()
            records_data.append(payload)
        await records_collection.insert_many(records_data)
        print(f"✓ Migrated {len(records_data)} records")

    # Insert warehouse snapshots
    if state.warehouse_snapshots:
        snapshots_data = []
        for snapshot in state.warehouse_snapshots:
            payload = snapshot.model_dump()
            captured_at = payload.get('captured_at')
            payload['created_at'] = payload.get('created_at') or captured_at or now_iso()
            payload['updated_at'] = payload.get('updated_at') or captured_at or now_iso()
            snapshots_data.append(payload)
        await warehouse_snapshots_collection.insert_many(snapshots_data)
        print(f"✓ Migrated {len(snapshots_data)} warehouse snapshots")

    storage_names = sorted({item.warehouse.strip() for item in state.warehouse_snapshots if item.warehouse.strip()})
    if storage_names:
        storage_now = now_iso()
        storage_names_data = [
            {
                'name': name,
                'normalized_name': normalize_storage_name(name),
                'created_at': storage_now,
                'updated_at': storage_now,
            }
            for name in storage_names
        ]
        await storage_names_collection.insert_many(storage_names_data)
        print(f"✓ Migrated {len(storage_names_data)} storage names")

    # Insert settings
    settings_now = now_iso()
    await settings_collection.insert_one({
        '_id': 'app_settings',
        'settings': state.settings,
        'created_at': settings_now,
        'updated_at': settings_now,
    })
    print("✓ Migrated settings")

    print("Migration completed successfully!")


if __name__ == '__main__':
    asyncio.run(migrate_to_mongodb())