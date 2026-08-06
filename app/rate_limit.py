# incr(ratelimit:5)

from fastapi import HTTPException
from app.redis_client import redis_client

RATE_LIMIT = 60
WINDOW_SECONDS = 60


async def check_rate_limit(api_key_id: int) -> None:
    key = f"ratelimit:{api_key_id}"
    count = await redis_client.incr(key)

    if count == 1:
        await redis_client.expire(key, WINDOW_SECONDS)

    if count > RATE_LIMIT:
        ttl = await redis_client.ttl(key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(ttl)}
        )