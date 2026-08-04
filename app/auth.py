from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.api_key import ApiKey
from app.security import hash_api_key
from sqlalchemy import select


async def verify_token(authorization:str = Header(...), db:AsyncSession=Depends(get_db))->ApiKey:
    token = authorization.removeprefix("Bearer ").strip()
    hashed = hash_api_key(token)

    result = await db.execute(select(ApiKey).where(ApiKey.hashed_key == hashed))
    api_key = result.scalar_one_or_none()

    if api_key is None or not api_key.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    return api_key


