from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr

class SignupResponse(BaseModel):
    id: int
    name: str
    api_key: str