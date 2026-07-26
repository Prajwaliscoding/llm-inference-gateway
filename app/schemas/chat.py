from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    role: str
    content: str

class Request(BaseModel):
    model: str
    messages: list[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = None

##

