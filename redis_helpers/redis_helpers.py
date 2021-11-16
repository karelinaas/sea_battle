import aioredis


async def set_key(key: str, value: str) -> None:
    redis = await aioredis.create_redis('redis://redis:6379')
    await redis.set(key, value)


async def get_by_key(key: str):
    redis = await aioredis.create_redis('redis://redis:6379')
    return await redis.get(key)
