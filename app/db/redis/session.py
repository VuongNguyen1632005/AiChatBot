import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis = None

async def init_redis() -> None:
    global redis_client
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")

async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
        print("🛑 Redis connection closed")

async def get_redis() -> aioredis.Redis:
    return redis_client
