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

Cre
