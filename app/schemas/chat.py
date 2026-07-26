from pydantic import BaseModel
from typing import Optional

# For Request body

class Message(BaseModel):
    role: str
    content: str

class Request(BaseModel):
    model: str
    messages: list[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = None

# For Response Body
class ResponseMessage(BaseModel):
    role: str
    content: str

class Choice(BaseModel):
    index: int
    message: ResponseMessage
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class Response(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[Choice]
    usage: Usage