from pydantic import BaseModel

class CreateApiKeyRequest(BaseModel):
    name:str

class CreateApiKeyResponse(BaseModel):
    id:int
    name:str
    api_key:str
