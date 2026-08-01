from app.schemas.chat import Request
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock
import httpx

def test_valid_request():
    data = {
        "model":"gpt-4o-mini",
        "messages":[{"role":"user", "content":"hi"}]
    }

    request = Request(**data)

    assert request.model == "gpt-4o-mini"
    assert request.messages[0].content == "hi"


def test_invalid_request_missing_model():
    data = {
            "messages":[{"role":"user", "content":"hi"}]
    }

    with pytest.raises(ValidationError):
        Request(**data) # type: ignore[call-arg]


client = TestClient(app) 

def test_missing_token_returns_401():

    response = client.post("/v1/chat/completions", 
                           json = {"model":"gpt-4o-mini", 
                                   "messages": [{"role":"user", "content":"hello"}]})

    assert response.status_code == 401


def test_provider_unreachable_returns_502():

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.RequestError("Connection failed")

        response = client.post("/v1/chat/completions", 
                           headers= {"Authorization" : "Bearer gateway-key"},
                           json = {"model":"gpt-4o-mini", 
                                   "messages": [{"role":"user", "content":"hello"}]})

    assert response.status_code == 502


def test_provider_server_error_returns_502():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = httpx.Response(status_code=500, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"))
        mock_post.return_value = mock_response

        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer gateway-key"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}
        )

    assert response.status_code == 502