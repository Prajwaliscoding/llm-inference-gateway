import hashlib
import json

from app.redis_client import redis_client
from app.schemas.chat import Request

def build_cache_key(request: Request) -> str:
    messages_list = []
    for m in request.messages:
        messages_list.append({"role": m.role, "content": m.content})

    payload = {
        "model": request.model,
        "messages": messages_list    
    }

    serialized = json.dumps(payload, sort_keys=True)

    return "cache:" + hashlib.sha256(serialized.encode()).hexdigest()

async def find_cache_in_redis(cache_key: str):
    cache = await redis_client.get(cache_key)

    if cache is None:
        return None
    return json.loads(cache)
