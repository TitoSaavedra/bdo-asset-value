from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from app.config import MONGODB_URL, DATABASE_NAME

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
records_collection = db.records
warehouse_snapshots_collection = db.warehouse_snapshots
settings_collection = db.settings


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