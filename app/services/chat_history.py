import json
import os

MAX_HISTORY = 50
TTL_SECONDS = 86400  # 24 hours


def _get_redis():
    import redis.asyncio as aioredis

    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return aioredis.from_url(url)


async def get_history(teacher_id: str, scenario_id: str) -> list[dict]:
    try:
        r = _get_redis()
        key = f"chat:{teacher_id}:{scenario_id}"
        data = await r.get(key)
        await r.aclose()
        if data:
            return json.loads(data)
        return []
    except Exception:
        return []


async def save_message(
    teacher_id: str, scenario_id: str, user_msg: str, assistant_msg: str
) -> None:
    try:
        r = _get_redis()
        key = f"chat:{teacher_id}:{scenario_id}"
        history = await get_history(teacher_id, scenario_id)
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]
        await r.setex(key, TTL_SECONDS, json.dumps(history, ensure_ascii=False))
        await r.aclose()
    except Exception:
        pass


async def clear_history(teacher_id: str, scenario_id: str) -> None:
    try:
        r = _get_redis()
        key = f"chat:{teacher_id}:{scenario_id}"
        await r.delete(key)
        await r.aclose()
    except Exception:
        pass
