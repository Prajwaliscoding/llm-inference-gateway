from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.api_key import ApiKey
from app.security import hash_api_key

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security), 
                       db:AsyncSession=Depends(get_db))->ApiKey:
    hashed = hash_api_key(credentials.credentials)

    result = await db.execute(select(ApiKey).where(ApiKey.hashed_key == hashed))
    api_key = result.scalar_one_or_none()

    if api_key is None or not api_key.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    return api_key


def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    