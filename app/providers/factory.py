from app.providers.anthropic_provider import AnthropicProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.base import LLMProvider

def get_provider(model:str) -> LLMProvider:
    if model.startswith("claude"):
        return AnthropicProvider()
    return OpenAIProvider()
