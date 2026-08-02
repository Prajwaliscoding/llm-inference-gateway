from app.providers.base import LLMProvider
from app.config import settings
from app.schemas.chat import Request, Response
import httpx
from fastapi import HTTPException
from app.logging_config import logger

class OpenAIProvider(LLMProvider):

    def __init__(self)->None:
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.api_key = settings.openai_api_key


    async def chat_completion(self, request: Request) -> Response:
        try:
            async with httpx.AsyncClient() as client:
                logger.info("provider called", provider ="openai")
                response = await client.post(self.base_url, 
                                  json=request.model_dump(),
                                  headers={"Authorization": f"Bearer {self.api_key}" },
                                  timeout=30.0)
        except httpx.RequestError:
            logger.error("provider unreachable", provider="openai")
            raise HTTPException(status_code=502, detail="Failed to reach OpenAI")
        
        if response.status_code >= 500:
            logger.error("provider server error", provider="openai", status_code=response.status_code)
            raise HTTPException(status_code=502, detail="OpenAI server failed")

        data = response.json()
            
        return Response(**data)

        