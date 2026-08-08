from fastapi import HTTPException
from app.providers.base import LLMProvider
from app.providers.exceptions import ProviderError
from app.schemas.chat import Request, Response
from app.logging_config import logger

from collections import deque
import time

FAILURE_WINDOW_SECONDS = 60
FAILURE_THRESHOLD = 0.5
COOLDOWN_SECONDS = 30

circuit_state = {
    "openai": {"state": "closed", "outcomes": deque(), "opened_at": None},
    "anthropic": {"state": "closed", "outcomes": deque(), "opened_at": None},
}


def record_outcome(provider_name: str, success: bool) -> None:
    circuit_state[provider_name]["outcomes"].append((time.time(), success))

def get_failure_rate(provider_name: str) -> float:
    now = time.time()
    outcomes = circuit_state[provider_name]["outcomes"]
    
    while outcomes and now - outcomes[0][0] > FAILURE_WINDOW_SECONDS:
        outcomes.popleft()
    
    if not outcomes:
        return 0.0
    
    failures = 0
    for timestamp, success in outcomes:
        if not success:
            failures += 1
    
    return failures / len(outcomes)





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
            