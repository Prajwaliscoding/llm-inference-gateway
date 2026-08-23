
from pydantic import BaseModel

# For Request body

class Message(BaseModel):
    role: str
    content: str

class Request(BaseModel):
    model: str
    messages: list[Message]
    temperature: float | None = None
    max_tokens: int | None = None
    n: int | None = None

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