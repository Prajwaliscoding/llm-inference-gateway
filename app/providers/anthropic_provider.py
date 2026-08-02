from app.providers.base import LLMProvider
from app.config import settings
from app.schemas.chat import Request, Response, Choice, ResponseMessage, Usage
import httpx
from app.logging_config import logger
from fastapi import HTTPException
import time


def _normalize_anthropic_response(data:dict) -> Response:

    content = data["content"][0]["text"]
    finish_reason_map={
        "end_turn": "stop",
        "max_tokens": "length",
        "stop_sequence": "stop"
    }
    finish_reason = finish_reason_map.get(data["stop_reason"],"stop")

    choice = Choice(
        index=0,
        message=ResponseMessage(role= "assistant",content=content),
        finish_reason = finish_reason
    )

    usage = Usage(
        prompt_tokens=data["usage"]["input_tokens"],
        completion_tokens=data["usage"]["output_tokens"],
        total_tokens=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
    )

    return Response(
        id=data["id"],
        object="chat.completion",
        created=int(time.time()),
        model=data["model"],
        choices=[choice],
        usage=usage)

class AnthropicProvider(LLMProvider):

    def __init__(self):
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.api_key = settings.anthropic_api_key


    async def chat_completion(self, request: Request) -> Response:

        messages = []
        system_prompt = None

        for msg in request.messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,

        }

        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient() as client:
            try:
                logger.info("provider called", provider="anthropic")
                response = await client.post(
                    self.base_url,
                    json = payload,
                    headers = {
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    timeout=30.0,
                )
            except httpx.RequestError:
                logger.error("provider unreachable", provider="anthropic")
                raise HTTPException(status_code=502, detail="Failed to reach Anthropic")


            if response.status_code >= 500:
                logger.error("provider server error", provider="anthropic", status_code=response.status_code)
                raise HTTPException(status_code=502, detail="Anthropic server failed")

            data = response.json() 
            return _normalize_anthropic_response(data)

        
