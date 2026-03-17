from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from app.config import MONGODB_URL, DATABASE_NAME
from app.utils.time import now_iso

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
records_collection = db.records
warehouse_snapshots_collection = db.warehouse_snapshots
settings_collection = db.settings
storage_names_collection = db.storage_names


def normalize_storage_name(name: str) -> str:
	"""Normalize storage name for case-insensitive uniqueness."""
	return name.strip().lower()


async def upsert_storage_name(name: str) -> None:
	"""Insert or update a storage name document."""
	clean_name = name.strip()
	if not clean_name:
		return

	now = now_iso()
	await storage_names_collection.update_one(
		{'normalized_name': normalize_storage_name(clean_name)},
		{
			'$setOnInsert': {
				'created_at': now,
			},
			'$set': {
				'name': clean_name,
				'normalized_name': normalize_storage_name(clean_name),
				'updated_at': now,
			},
		},
		upsert=True,
	)


async def list_storage_names() -> list[str]:
	"""Return storage names ordered alphabetically."""
	cursor = storage_names_collection.find({}, {'_id': 0, 'name': 1}).sort('name', ASCENDING)
	items = await cursor.to_list(length=None)
	return [item.get('name', '').strip() for item in items if item.get('name')]


async def ensure_indexes() -> None:
	"""Ensure MongoDB indexes used by history and snapshot queries.

	This function is safe to call multiple times. MongoDB will reuse
	existing indexes if they are already present.
	"""
	await records_collection.create_index([
		('captured_at', DESCENDING),
	], name='idx_records_captured_at_desc')

	await records_collection.create_index([
		('source', ASCENDING),
		('captured_at', DESCENDING),
	], name='idx_records_source_captured_at')

	await warehouse_snapshots_collection.create_index([
		('captured_at', DESCENDING),
	], name='idx_snapshots_captured_at_desc')

	await warehouse_snapshots_collection.create_index([
		('warehouse', ASCENDING),
		('captured_at', DESCENDING),
	], name='idx_snapshots_warehouse_captured_at')

	await storage_names_collection.create_index([
		('normalized_name', ASCENDING),
	], name='idx_storage_names_normalized_unique', unique=True)

	await storage_names_collection.create_index([
		('name', ASCENDING),
	], name='idx_storage_names_name')