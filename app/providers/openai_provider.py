import httpx
from fastapi import HTTPException

from app.config import settings
from app.logging_config import logger
from app.providers.base import LLMProvider
from app.providers.exceptions import (
    ProviderConnectionError,
    ProviderServerError,
    ProviderTimeoutError,
)
from app.schemas.chat import Request, Response


class OpenAIProvider(LLMProvider):

    def __init__(self)->None:
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.api_key = settings.openai_api_key


    async def chat_completion(self, request: Request) -> Response:
        model = request.model if not request.model.startswith("claude") else "gpt-4o-mini"
        payload = request.model_dump()
        payload["model"] = model
        
        try:
            async with httpx.AsyncClient() as client:
                logger.info("provider called", provider ="openai")
                response = await client.post(self.base_url, 
                                  json=request.model_dump(),
                                  headers={"Authorization": f"Bearer {self.api_key}" },
                                  timeout=30.0)

        except httpx.TimeoutException as e:
            logger.error("provider timeout error", provider="openai")
            raise ProviderTimeoutError(str(e)) from e
        except httpx.RequestError as e:
            logger.error("provider unreachable", provider="openai")
            raise ProviderConnectionError(str(e)) from e
        
        if response.status_code >= 500:
            logger.error("provider server error", provider="openai", status_code=response.status_code)
            raise ProviderServerError(response.status_code, "OpenAI server failed")

        if response.status_code in (401, 403, 429):
            error_body = response.json()
            logger.error("provider auth/rate-limit error", provider="openai", status_code=response.status_code, body=error_body)
            raise ProviderServerError(response.status_code, str(error_body))

        if response.status_code >= 400:
            error_body = response.json()
            logger.error("provider client error", provider="openai", status_code=response.status_code, body=error_body)
            raise HTTPException(status_code=response.status_code, detail=error_body)

        data = response.json()

        return Response(**data)

        