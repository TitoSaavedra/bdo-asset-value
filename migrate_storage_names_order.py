import asyncio
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
API_SERVICE_DIR = BASE_DIR / 'python-api-service'
OCR_WORKER_DIR = BASE_DIR / 'python-ocr-worker'
if str(API_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_DIR))
if str(OCR_WORKER_DIR) not in sys.path:
    sys.path.insert(0, str(OCR_WORKER_DIR))

from app.database import ensure_indexes, normalize_storage_name, storage_names_collection
from app.utils.time import now_iso
from app.ocr.config.storages import KNOWN_STORAGES


async def migrate_storage_names_order() -> None:
    """Rebuild storage_names collection with deterministic order field.

    Steps:
    1) Read all current storage_names records from MongoDB.
    2) Sort current names using OCR KNOWN_STORAGES order.
    3) Delete all storage_names records.
    4) Reinsert same names with explicit incremental order.
    """

    await ensure_indexes()

    existing_docs = await storage_names_collection.find({}, {'_id': 0}).to_list(length=None)
    if not existing_docs:
        print('No documents found in storage_names. Nothing to migrate.')
        return

    existing_by_key: dict[str, dict] = {}
    for document in existing_docs:
        name = str(document.get('name', '')).strip()
        if not name:
            continue
        existing_by_key[normalize_storage_name(name)] = document

    known_order_keys = [normalize_storage_name(name) for name in KNOWN_STORAGES]
    ordered_keys: list[str] = []

    for key in known_order_keys:
        if key in existing_by_key:
            ordered_keys.append(key)

    extra_keys = [key for key in existing_by_key.keys() if key not in set(known_order_keys)]
    extra_keys.sort()
    ordered_keys.extend(extra_keys)

    now = now_iso()
    migrated_docs: list[dict] = []
    for index, key in enumerate(ordered_keys, start=1):
        source_document = existing_by_key[key]
        name = str(source_document.get('name', '')).strip()
        if not name:
            continue

        migrated_docs.append(
            {
                'name': name,
                'normalized_name': key,
                'order': index,
                'created_at': source_document.get('created_at', now),
                'updated_at': now,
            }
        )

    await storage_names_collection.delete_many({})
    if migrated_docs:
        await storage_names_collection.insert_many(migrated_docs)

    print(f'✓ Rebuilt storage_names with order field: {len(migrated_docs)} documents')


if __name__ == '__main__':
    asyncio.run(migrate_storage_names_order())
