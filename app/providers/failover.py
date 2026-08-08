from fastapi import HTTPException
from app.providers.base import LLMProvider
from app.providers.exceptions import ProviderError
from app.providers.openai_provider import OpenAIProvider
from app.schemas.chat import Request, Response
from app.logging_config import logger
from app.providers.circuit_breaker import is_available, update_circuit


async def call_with_failover(primary: LLMProvider, fallback: LLMProvider, request: Request,
                             result_info: dict[str, LLMProvider]) -> Response:

    providers = [primary, fallback]

    for provider in providers:
        
        name = "openai" if isinstance(provider, OpenAIProvider) else "anthropic"
        if not is_available(name):
            logger.info("circuit open, skipping provider", provider=name)
            continue

        
        try:
            response = await provider.chat_completion(request)
            update_circuit(name, success=True)
            result_info["provider"] = provider   # record who succeeded
            return response       
        except ProviderError as e:
            update_circuit(name, success=False)
            logger.error("provider failed, trying next",
                            provider=type(provider).__name__,
                            error=str(e))
            continue

    logger.error("all providers exhausted")
    raise HTTPException(status_code=503, detail="All providers unavailable")
            