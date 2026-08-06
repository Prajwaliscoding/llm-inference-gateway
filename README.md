# LLM Inference Gateway

An API gateway that proxies requests to multiple LLM providers(OpenAI and Anthropic), with real auth, persistence, caching, rate limiting, cost tracking, and smart routing. It is built as an OpenAI compatible drop-in endpoint.

## How it works

1. Client sends an OpenAI-shaped request to `/v1/chat/completions`
2. Gateway authenticates the request against a hashed API key in Postgres
3. Rate limit checked via atomic Redis counters
4. Redis checked for a cached response — instant return on hit
5. If `"model": "auto"`, gateway picks a model by prompt length, invisibly
6. Request routed to the right provider (OpenAI/Anthropic) via a shared interface
7. Cost calculated from real token usage
8. Request logged and usage summary updated, atomically, in one transaction
9. Response cached, then returned

## Getting access

Keys aren't self-service. The **admin** creates a key using `ADMIN_TOKEN`, then hands the raw key to whoever needs access (a teammate, a client app, a test script):

```bash
curl -X POST http://127.0.0.1:8000/admin/keys \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "client-name"}'
```

The response shows the raw key **once**. Copy it and send it to the client — only the hash is stored, so it can never be retrieved again. From here on, that client authenticates with `Authorization: Bearer <that-key>` on `/v1/chat/completions`.

## Features

- **Multi-provider abstraction** — one `LLMProvider` interface, `OpenAIProvider`/`AnthropicProvider` implementations. New provider = one file + one line.
- **Real auth** — keys generated via `secrets.token_urlsafe(32)`, SHA-256 hashed before storage, shown once.
- **Postgres persistence** — async SQLAlchemy, connection pooling, Alembic migrations.
- **Redis caching** — hashed request → cached response, TTL-based expiry.
- **Redis rate limiting** — atomic `INCR`/`EXPIRE` per key, `429` + real `Retry-After`.
- **Smart routing** — `"model": "auto"` resolves by prompt length.
- **Cost tracking** — real per-model pricing, sourced and dated.
- **Usage accounting** — per-request log + per-key daily summary, one atomic transaction.
- **Structured logging** — JSON logs, unique request ID per request.
- **Error handling** — upstream failures → `502`, bad auth → `401`, over-limit → `429`.
- **Tested against real infra** — `testcontainers-python` spins up real Postgres + Redis for tests. 82%+ coverage.

## Architecture

```
app/
├── main.py                    # routes, middleware, request pipeline
├── auth.py                    # bearer token verification (client + admin)
├── security.py                # key generation & hashing
├── config.py                  # env-based settings
├── database.py                # async engine, session factory, get_db
├── redis_client.py            # async Redis client
├── cache.py                   # cache key building, save/find
├── rate_limit.py               # Redis-backed rate limiting
├── pricing.py                  # pricing table + cost calc
├── usage.py                    # request log + usage summary writes
├── logging_config.py           # structlog setup
├── models/                     # SQLAlchemy models
├── schemas/                    # Pydantic request/response models
└── providers/
    ├── base.py                 # LLMProvider ABC
    ├── openai_provider.py
    ├── anthropic_provider.py   # + response normalization
    └── factory.py               # get_provider() + resolve_model()

alembic/                        # migrations
tests/
├── conftest.py                 # testcontainers fixtures
├── test_main.py
└── fixtures/openai_response.json
```

## Data model

- **`api_keys`** — hashed key, name, active flag, created timestamp
- **`requests`** — one row per call: key, model, provider, tokens, cost, timestamp
- **`usage_summaries`** — one row per (key, day), unique-constrained, running totals

## Setup

**Prereqs:** Python 3.12+, [uv](https://github.com/astral-sh/uv), Docker

```bash
# 1. .env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
ADMIN_TOKEN=your-admin-secret
POSTGRES_USER=gateway_user
POSTGRES_PASSWORD=gateway_pass
POSTGRES_DB=gateway_db
POSTGRES_HOST=localhost
REDIS_HOST=localhost

# 2. install
uv sync

# 3. start Postgres + Redis
make start-db

# 4. migrate
uv run alembic upgrade head

# 5. run
make run
```

**Docker Compose (full stack):** `docker compose up`

## API docs

`http://127.0.0.1:8000/docs` — click **Authorize** once, applies to every request in session. Raw schema at `/openapi.json`.

## Example request

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer <issued-key>" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```

`"model": "auto"` lets the gateway pick. A real Anthropic model name (e.g. `claude-haiku-4-5-20251001`) routes to Anthropic — same request/response shape either way.

**Response:**

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
  "usage": { "prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18 }
}
```

**Health check:** `curl http://127.0.0.1:8000/health` → `{"status": "okay"}`

## Tests

```bash
make test
```

Real, throwaway Postgres + Redis containers via `testcontainers-python` — only external provider calls are mocked (via `respx`), no real API costs during test runs.

```bash
uv run pytest --cov=app tests/
```

Current coverage: **82%+**

Covers: schema validation, auth (missing/invalid/valid key), provider failures (`502`), full mocked-provider flow, cache hits skip provider calls, rate limit `429` + real `Retry-After`, `"auto"` routing by prompt length.

## Tooling

- **Package mgmt:** `uv`
- **Lint/types:** `ruff`, `mypy` (strict)
- **Migrations:** Alembic
- **CI:** GitHub Actions — lint, type-check, test on every push
- **Tasks:** `Makefile` — `make run`, `make start-db`, `make test`, `make lint`

## Why it's built this way

- **Postgres + Redis, not one datastore** — Postgres holds data that must survive forever; Redis holds data that's fine to lose (worst case: fall back to normal behavior).
- **Keys hashed, never stored raw** — a DB breach never exposes usable credentials.
- **`usage_summaries` separate from `requests`** — reading a running total stays cheap regardless of history size.
- **Pricing table is sourced and dated** — LLM pricing changes; guessed numbers rot silently.
