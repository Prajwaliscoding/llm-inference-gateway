from app.config import settings
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)): # noqa: B008
    if credentials.credentials != settings.gateway_api_token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")