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
	return name.lower()


async def upsert_storage_name(name: str) -> None:
	"""Insert or update a storage name document."""
	normalized_name = normalize_storage_name(name)
	last_order_doc = await storage_names_collection.find_one(
		{},
		{'_id': 0, 'order': 1},
		sort=[('order', DESCENDING)],
	)
	next_order = (last_order_doc['order'] if last_order_doc else 0) + 1

	now = now_iso()
	await storage_names_collection.update_one(
		{'normalized_name': normalized_name},
		{
			'$setOnInsert': {
				'created_at': now,
				'order': next_order,
			},
			'$set': {
				'name': name,
				'normalized_name': normalized_name,
				'updated_at': now,
			},
		},
		upsert=True,
	)


async def list_storage_names() -> list[str]:
	"""Return storage names ordered by explicit DB order field."""
	cursor = storage_names_collection.find({}, {'_id': 0, 'name': 1}).sort([
		('order', ASCENDING),
		('name', ASCENDING),
	])
	items = await cursor.to_list(length=None)
	return [item['name'] for item in items]


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

	await storage_names_collection.create_index([
		('order', ASCENDING),
		('name', ASCENDING),
	], name='idx_storage_names_order_name')