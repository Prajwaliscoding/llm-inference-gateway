from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import LLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.schemas.chat import Request


def get_provider(model:str) -> LLMProvider:
    if model.startswith("claude"):
        return AnthropicProvider()
    return OpenAIProvider()


def resolve_model(request: Request) -> str:
    if request.model != "auto":
        return request.model

    total_length = sum(len(m.content) for m in request.messages)
    if total_length < 500:
        return "gpt-4o-mini"
    else:
        return "gpt-4o"


def get_fallback_provider(primary: LLMProvider) -> LLMProvider:
    if isinstance(primary, OpenAIProvider):
        return AnthropicProvider()
    return OpenAIProvider()
    