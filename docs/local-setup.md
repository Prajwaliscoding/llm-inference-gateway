# Local Setup

Run the full gateway on your machine using Docker Compose. No AWS account or cloud resources needed for this.

## Prerequisites

Docker and Docker Compose installed. That's the only requirement.

## 1. Clone the repo

```bash
git clone https://github.com/Prajwaliscoding/llm-inference-gateway.git
cd llm-inference-gateway
```

## 2. Create your `.env` file

Create a file named `.env` in the repo root (same folder as `docker-compose.yml`):

```bash
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
ADMIN_TOKEN=any-secret-string-you-choose
POSTGRES_USER=gateway_user
POSTGRES_PASSWORD=gateway_pass
POSTGRES_DB=gateway_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_HOST=redis
```

You'll need real API keys from [platform.openai.com](https://platform.openai.com/api-keys) and [console.anthropic.com](https://console.anthropic.com/settings/keys). `ADMIN_TOKEN` can be any string you make up, it's what you'll use to create client API keys later.

`POSTGRES_HOST=postgres` and `REDIS_HOST=redis` must stay exactly as shown. These are the service names Docker Compose uses internally, not `localhost`.

## 3. Start everything

```bash
docker compose up --build
```

This starts five containers: the gateway, Postgres, Redis, Prometheus, and Grafana.

## 4. Run database migrations

In a separate terminal, while the stack is running:

```bash
docker compose exec gateway alembic upgrade head
```

## 5. Verify it's running

Open `http://localhost:8000/health` in your browser. You should see:

```json
{ "status": "okay" }
```

## 6. Create your first API key

```bash
curl -X POST http://localhost:8000/admin/keys \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-first-key"}'
```

Replace `your-admin-token` with whatever you set as `ADMIN_TOKEN` in `.env`. Save the `api_key` value from the response, it's shown only once.

## 7. Send your first request

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <the-key-from-step-6>" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```

If this returns a real response, everything is working.

## Other running services

- **API docs:** `http://localhost:8000/docs`
- **Prometheus:** `http://localhost:9090`
- **Grafana:** `http://localhost:3000` (login `admin`/`admin` on first run, you'll be asked to set a new password)

## Running locally without Docker (optional)

If you'd rather run the gateway process directly on your machine (Python 3.12+, [uv](https://github.com/astral-sh/uv) required):

```bash
# Start only Postgres and Redis in Docker
make start-db

# In your .env, use these instead:
# POSTGRES_HOST=localhost
# REDIS_HOST=localhost

uv sync
uv run alembic upgrade head
make run
```

Back to **[README](../README.md)**.
