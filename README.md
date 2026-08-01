# LLM Inference Gateway

A lightweight API gateway that proxies requests to LLM providers (currently OpenAI), with authentication, structured logging, and error handling — built as an OpenAI-compatible drop-in endpoint.

## Features

- OpenAI-compatible `/v1/chat/completions` endpoint
- Bearer token authentication
- Structured JSON logging with request tracing (unique request ID per request)
- Async request handling via httpx
- Graceful error handling (upstream failures mapped to `502`)
- `/health` endpoint for liveness checks
- 95%+ test coverage (unit + integration tests, mocked provider calls)

## Running locally

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker (optional, for containerized run)

### Setup

1. Clone the repo
2. Create a `.env` file with:

```
OPENAI_API_KEY=your-openai-key
GATEWAY_API_TOKEN=your-chosen-token
```

3. Install dependencies:

```bash
   uv sync
```

4. Run the server:

```bash
   make run
```

### Running with Docker

```bash
docker compose up
```

## Interactive API docs (Swagger UI)

Once the server is running, open:

```
http://127.0.0.1:8000/docs
```

This gives you an interactive UI to explore and test the `/v1/chat/completions` and `/health` endpoints directly in the browser — no curl needed. A raw OpenAPI schema is also available at `/openapi.json`.

## Example request

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```

### Example response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1722366000,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  }
}
```

### Health check

```bash
curl http://127.0.0.1:8000/health
```

```json
{ "status": "ok" }
```

## Running tests

```bash
make test
```

This runs the full test suite (unit tests for schema validation, auth, and error mapping, plus one integration test using a saved fixture) with coverage reporting. Current coverage: **95%**.

Individual test categories:

- Request/response schema validation
- Auth dependency (missing/invalid token → `401`)
- Provider failure handling (unreachable / 5xx → `502`)
- Full request→response flow (mocked OpenAI, using a saved fixture)

## Project structure

```markdown
app/
├── main.py # FastAPI app, routes, middleware
├── auth.py # Bearer token verification
├── config.py # Environment-based settings (Pydantic Settings)
├── logging_config.py # structlog setup
└── schemas/
└── chat.py # Request/Response Pydantic models
tests/
├── test_main.py # Unit + integration tests
└── fixtures/
└── openai_response.json
```
