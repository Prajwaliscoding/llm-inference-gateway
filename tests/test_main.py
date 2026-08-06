from app.schemas.chat import Request, Message, Response, Choice, ResponseMessage, Usage
import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock, patch
import httpx
import respx
import json
from app.cache import build_cache_key, find_cache_key, save_cache_value


def test_valid_request():
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]}
    request = Request(**data)
    assert request.model == "gpt-4o-mini"
    assert request.messages[0].content == "hi"


def test_invalid_request_missing_model():
    data = {"messages": [{"role": "user", "content": "hi"}]}
    with pytest.raises(ValidationError):
        Request(**data)  # type: ignore[call-arg]


@pytest.mark.asyncio
async def test_missing_token_returns_401(client):
    response = await client.post(
        "/v1/chat/completions",
        json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_provider_unreachable_returns_502(test_api_key, override_get_db,override_redis, client):
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            side_effect=httpx.RequestError("Connection failed")
        )

        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {test_api_key}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]},
        )

    assert response.status_code == 502


@pytest.mark.asyncio
async def test_provider_server_error_returns_502(test_api_key, override_get_db, override_redis, client):
    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(status_code=500)
        )

        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {test_api_key}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]},
        )

    assert response.status_code == 502


@pytest.mark.asyncio
async def test_full_flow_with_fixture(test_api_key, override_get_db,override_redis, client):
    with open("tests/fixtures/openai_response.json") as f:
        fixture_data = json.load(f)

    with respx.mock:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(status_code=200, json=fixture_data)
        )

        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {test_api_key}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]},
        )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "Hello! How can I help you today?"
    assert response.json()["id"] == "chatcmpl-abc123"


@pytest.mark.asyncio
async def test_cache_hit_skips_provider(redis_session):
    request = Request(
        model="gpt-4o-mini",
        messages=[Message(role="user", content="2+2?")],
    )

    fake_response = Response(
        id="test-id",
        object="chat.completion",
        created=123,
        model="gpt-4o-mini",
        choices=[Choice(index=0, message=ResponseMessage(role="assistant", content="4"), finish_reason="stop")],
        usage=Usage(prompt_tokens=5, completion_tokens=1, total_tokens=6),
    )

    with patch("app.cache.redis_client", redis_session):
        cache_key = build_cache_key(request)
        await save_cache_value(cache_key, fake_response)

        cached = await find_cache_key(cache_key)

        assert cached is not None
        assert cached["choices"][0]["message"]["content"] == "4"


@pytest.mark.asyncio
async def test_rate_limit_returns_429(redis_session):
    from app.rate_limit import check_rate_limit, RATE_LIMIT
    from fastapi import HTTPException

    with patch("app.rate_limit.redis_client", redis_session):
        for _ in range(RATE_LIMIT):
            await check_rate_limit(api_key_id=1)

        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(api_key_id=1)

        assert exc_info.value.headers is not None
        assert "retry-after" in [h.lower() for h in exc_info.value.headers.keys()]


def test_resolve_model_short_prompt():
    from app.providers.factory import resolve_model
    request = Request(model="auto", messages=[Message(role="user", content="hi")])
    assert resolve_model(request) == "gpt-4o-mini"


def test_resolve_model_long_prompt():
    from app.providers.factory import resolve_model
    long_content = "x" * 600
    request = Request(model="auto", messages=[Message(role="user", content=long_content)])
    assert resolve_model(request) == "gpt-4o"