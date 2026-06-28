# app/utils/redis_client.py
import redis.asyncio as redis
from app.config import settings

_redis_client = None


async def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            db=settings.REDIS_DB,
            decode_responses=False,
            # 连接池配置
            max_connections=10,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
    return _redis_client


async def close_redis_client():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None