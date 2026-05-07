from motor.motor_asyncio import AsyncIOMotorClient
from .redis import get_redis
from app.core.config import get_settings

settings = get_settings()
client: AsyncIOMotorClient | None = None

def get_mongo_client() -> AsyncIOMotorClient:
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.mongodb_uri, uuidRepresentation="standard")
    return client

def get_db():
    return get_mongo_client()[settings.mongodb_db]
