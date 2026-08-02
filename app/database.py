from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:5432/{settings.postgres_db}"

engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=5)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

