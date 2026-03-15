import asyncio
from app.storage import JSONStorage
from app.database import records_collection, warehouse_snapshots_collection, settings_collection


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

    # Insert records
    if state.records:
        records_data = [record.model_dump() for record in state.records]
        await records_collection.insert_many(records_data)
        print(f"✓ Migrated {len(records_data)} records")

    # Insert warehouse snapshots
    if state.warehouse_snapshots:
        snapshots_data = [snapshot.model_dump() for snapshot in state.warehouse_snapshots]
        await warehouse_snapshots_collection.insert_many(snapshots_data)
        print(f"✓ Migrated {len(snapshots_data)} warehouse snapshots")

    # Insert settings
    await settings_collection.insert_one({
        '_id': 'app_settings',
        'settings': state.settings
    })
    print("✓ Migrated settings")

    print("Migration completed successfully!")


if __name__ == '__main__':
    asyncio.run(migrate_to_mongodb())