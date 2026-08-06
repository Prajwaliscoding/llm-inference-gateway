import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
import redis.asyncio as redis_lib
from app.database import get_db
from app.main import app as fastapi_app

import httpx
from httpx import ASGITransport

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7") as redis:
        yield redis


@pytest_asyncio.fixture
async def db_session(postgres_container):
    db_url = postgres_container.get_connection_url().replace(
        "psycopg2", "asyncpg"
    )
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()

@pytest_asyncio.fixture
async def redis_session(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    client = redis_lib.Redis(host=host, port=int(port), decode_responses=True)
    yield client
    await client.flushdb()
    await client.aclose()

@pytest_asyncio.fixture
async def test_api_key(db_session):
    from app.models.api_key import ApiKey
    from app.security import generate_api_key, hash_api_key

    raw_key = generate_api_key()
    hashed = hash_api_key(raw_key)

    key_row = ApiKey(hashed_key=hashed, name="test-key")
    db_session.add(key_row)
    await db_session.commit()

    return raw_key



@pytest.fixture
def override_get_db(db_session):
    async def _get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _get_db
    yield
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def override_redis(redis_session):
    import app.cache
    import app.rate_limit

    original_cache_redis = app.cache.redis_client
    original_ratelimit_redis = app.rate_limit.redis_client

    app.cache.redis_client = redis_session
    app.rate_limit.redis_client = redis_session
    yield
    app.cache.redis_client = original_cache_redis
    app.rate_limit.redis_client = original_ratelimit_redis