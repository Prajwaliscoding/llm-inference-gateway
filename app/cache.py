# Cache key and Cache value for key-value pair in Redis
# cache_key = hashed key to check for every request
# cache_value = the response made by our provider(OpenAI or Claude)

import hashlib
import json

from app.redis_client import redis_client
from app.schemas.chat import Request, Response


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


async def save_cache_value(cache_key:str, cache_value:Response, ttl:int=3600):
    serialized = cache_value.model_dump_json()
    await redis_client.set(cache_key, serialized, ex=ttl)

async def find_cache_key(cache_key: str):
    cache = await redis_client.get(cache_key)

    if cache is None:
        return None
    return json.loads(cache)

