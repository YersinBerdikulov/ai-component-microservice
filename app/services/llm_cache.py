import hashlib
import os

TTL_SECONDS = 3600  # 1 hour


def _cache_key(provider: str, model: str, system_prompt: str, user_message: str) -> str:
    raw = f"{provider}:{model}:{system_prompt}:{user_message}"
    return "llm:" + hashlib.sha256(raw.encode()).hexdigest()


def _get_redis():
    import redis.asyncio as aioredis
    return aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))


async def get(provider: str, model: str, system_prompt: str, user_message: str) -> str | None:
    try:
        r = _get_redis()
        key = _cache_key(provider, model, system_prompt, user_message)
        value = await r.get(key)
        await r.aclose()
        return value.decode() if value else None
    except Exception:
        return None


async def set(provider: str, model: str, system_prompt: str, user_message: str, response: str) -> None:
    try:
        r = _get_redis()
        key = _cache_key(provider, model, system_prompt, user_message)
        await r.setex(key, TTL_SECONDS, response.encode())
        await r.aclose()
    except Exception:
        pass
