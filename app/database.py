# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

_client = None
_db = None


async def connect_to_mongo():
    global _client, _db
    _client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        maxPoolSize=50,
        minPoolSize=10,
        maxIdleTimeMS=60000,
        connectTimeoutMS=10000,
        serverSelectionTimeoutMS=10000,
        retryWrites=True,
        retryReads=True
    )
    _db = _client[settings.MONGODB_DB]

    # 测试连接
    try:
        await _client.admin.command('ping')
        print("✅ MongoDB Atlas 连接成功")
    except Exception as e:
        print(f"❌ MongoDB 连接失败: {e}")
        raise

    return _db


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()


def get_db():
    return _db