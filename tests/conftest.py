import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.base import Base
import redis.asyncio as redis_lib


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