from abc import ABC, abstractmethod
from app.schemas.chat import Request, Response


class LLMProvider(ABC):

    @abstractmethod
    async def chat_completion(self, request:Request) -> Response:
        raise NotImplementedError