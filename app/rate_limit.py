import time
import redis.asyncio as redis
from fastapi import HTTPException
from app.config import REDIS_URL, RATE_LIMIT_PER_MINUTE

_redis = redis.from_url(REDIS_URL, decode_responses=True)


async def check_rate_limit(api_key: str):
    """
    Fixed-window counter keyed by api_key + current minute.

    Simple and good enough for a demo. A production version would use a
    sliding window or token bucket so a burst right at a minute boundary
    can't double the effective limit.
    """
    window = int(time.time() // 60)
    key = f"ratelimit:{api_key}:{window}"

    count = await _redis.incr(key)
    if count == 1:
        await _redis.expire(key, 60)

    if count > RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded, try again shortly")
