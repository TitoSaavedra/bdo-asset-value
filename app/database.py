from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL, DATABASE_NAME

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
records_collection = db.records
warehouse_snapshots_collection = db.warehouse_snapshots
settings_collection = db.settings