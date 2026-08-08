from fastapi import HTTPException
from app.providers.base import LLMProvider
from app.providers.exceptions import ProviderError
from app.schemas.chat import Request, Response
from app.logging_config import logger


async def call_with_failover(primary: LLMProvider, fallback: LLMProvider, request: Request,
                             result_info: dict[str, LLMProvider]) -> Response:

    providers = [primary, fallback]

    for provider in providers:
        try:
            response = await provider.chat_completion(request)
            result_info["provider"] = provider   # record who succeeded
            return response       
        except ProviderError as e:
            logger.error("provider failed, trying next",
                            provider=type(provider).__name__,
                            error=str(e))
            continue

    logger.error("all providers exhausted")
    raise HTTPException(status_code=503, detail="All providers unavailable")
            