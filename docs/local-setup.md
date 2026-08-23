# Local Setup

Run the full gateway, backend and frontend, on your machine. No AWS account or cloud resources needed for this.

## Prerequisites

Docker and Docker Compose, plus Node.js (for the frontend). That's it.

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

You'll need real API keys from [platform.openai.com](https://platform.openai.com/api-keys) and [console.anthropic.com](https://console.anthropic.com/settings/keys). `ADMIN_TOKEN` can be any string you make up, it's what you'll use for admin-only endpoints.

`POSTGRES_HOST=postgres` and `REDIS_HOST=redis` must stay exactly as shown. These are the service names Docker Compose uses internally, not `localhost`.

## 3. Start the backend

```bash
docker compose up --build
```

This starts five containers: the gateway, Postgres, Redis, Prometheus, and Grafana.

## 4. Run database migrations

In a separate terminal, while the stack is running:

```bash
docker compose exec gateway alembic upgrade head
```

## 5. Verify the backend is running

Open `http://localhost:8000/health` in your browser. You should see:

```json
{ "status": "okay" }
```

## 6. Start the frontend

In a separate terminal:

```bash
cd frontend
npm install
```

Create a file named `.env` inside `frontend/`:

```bash
VITE_API_URL=http://localhost:8000
```

Then start it:

```bash
npm run dev
```

Open `http://localhost:5173`. You should see the landing page.

## 7. Try the full flow

From the landing page, click Get Started, sign up with any email, and you'll get a real API key shown once. From there the dashboard and playground both work against your local backend. No separate step needed, the frontend handles sign up for you.

If you'd rather test the API directly instead of through the browser:

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
```

Save the `api_key` value from the response, then:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <the-key-from-above>" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```

If this returns a real response, everything is working.

## Other running services

- **API docs:** `http://localhost:8000/docs`
- **Prometheus:** `http://localhost:9090`
- **Grafana:** `http://localhost:3000` (login `admin`/`admin` on first run, you'll be asked to set a new password)

## Running the backend without Docker (optional)

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
