# LLM Inference Gateway

An API gateway that proxies requests to multiple LLM providers (OpenAI and Anthropic), with real auth, persistence, caching, rate limiting, cost tracking, smart routing, automatic failover, circuit breaking, and full observability. It is built as an OpenAI compatible drop-in endpoint.

**Live production deployment:** `https://gateway.prajwalkhatiwada.com`

## How it works

1. Client sends an OpenAI-shaped request to `/v1/chat/completions`
2. Gateway authenticates the request against a hashed API key in Postgres
3. Rate limit checked via atomic Redis counters
4. Redis checked for a cached response, instant return on hit
5. If `"model": "auto"`, gateway picks a model by prompt length, invisibly
6. Request routed to the right provider (OpenAI/Anthropic) via a shared interface
7. If the primary provider fails or its circuit is open, the gateway automatically retries on the other provider
8. Cost calculated from real token usage
9. Request logged and usage summary updated, atomically, in one transaction
10. Response cached, then returned
11. Every step emits metrics scraped by Prometheus and visualized in Grafana

## Getting access

Keys are not self service. The **admin** creates a key using `ADMIN_TOKEN`, then hands the raw key to whoever needs access (a teammate, a client app, a test script):

```bash
curl -X POST http://127.0.0.1:8000/admin/keys \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "client-name"}'
```

The response shows the raw key **once**. Copy it and send it to the client; only the hash is stored, so it can never be retrieved again. From here on, that client authenticates with `Authorization: Bearer <that-key>` on `/v1/chat/completions`.

## Features

- **Multi-provider abstraction**: one `LLMProvider` interface, `OpenAIProvider`/`AnthropicProvider` implementations. New provider = one file + one line.
- **Real auth**: keys generated via `secrets.token_urlsafe(32)`, SHA-256 hashed before storage, shown once.
- **Postgres persistence**: async SQLAlchemy, connection pooling, Alembic migrations.
- **Redis caching**: hashed request maps to cached response, TTL based expiry.
- **Redis rate limiting**: atomic `INCR`/`EXPIRE` per key, `429` + real `Retry-After`.
- **Smart routing**: `"model": "auto"` resolves by prompt length.
- **Automatic failover**: typed provider exceptions distinguish retry-worthy failures (5xx, timeout, connection errors) from client errors; failed requests transparently retry on the alternate provider.
- **Circuit breaker**: per-provider sliding-window failure tracking; a provider exceeding its failure threshold is skipped entirely until a cooldown passes and a single test request succeeds.
- **Cost tracking**: real per model pricing, sourced and dated.
- **Usage accounting**: per request log + per key daily summary, one atomic transaction.
- **Structured logging**: JSON logs, unique request ID per request.
- **Error handling**: upstream failures map to `502`/`503`, bad auth maps to `401`, over-limit maps to `429`.
- **Metrics & dashboards**: Prometheus instrumentation across requests, latency, cost, cache, provider failures, and circuit breaker state; pre-built Grafana dashboard for live visibility.
- **Tested against real infra**: `testcontainers-python` spins up real Postgres + Redis for tests. 82%+ coverage.
- **Production-deployed on Kubernetes**: runs on AWS EKS with autoscaling, RDS Postgres, HTTPS via ACM, and cluster-wide observability.

## Architecture

```
app/
├── main.py # routes, middleware, request pipeline
├── auth.py # bearer token verification (client + admin)
├── security.py # key generation & hashing
├── config.py # env-based settings
├── database.py # async engine, session factory, get_db
├── redis_client.py # async Redis client
├── cache.py # cache key building, save/find
├── rate_limit.py # Redis-backed rate limiting
├── pricing.py # pricing table + cost calc
├── usage.py # request log + usage summary writes
├── logging_config.py # structlog setup
├── metrics.py # Prometheus metric definitions
├── models/ # SQLAlchemy models
├── schemas/ # Pydantic request/response models
└── providers/
├── base.py # LLMProvider ABC
├── exceptions.py # typed provider exception hierarchy
├── openai_provider.py
├── anthropic_provider.py # + response normalization
├── factory.py # get_provider(), resolve_model(), get_fallback_provider()
├── failover.py # call_with_failover() - retry orchestration
└── circuit_breaker.py # per-provider sliding-window circuit breaker

grafana/
└── dashboard.json # pre-built Grafana dashboard

k8s/ # production Kubernetes manifests
├── 00-namespace.yaml
├── 01-configmap.yaml
├── 01-secret.yaml
├── 02-deployment.yaml
├── 03-hpa.yaml
├── 04-service.yaml
├── 05-ingress.yaml
├── 06-redis.yaml
├── 07-grafana-ingress.yaml
└── 08-servicemonitor.yaml

infra/ # cluster provisioning
└── eksctl-cluster.yaml

scripts/
└── traffic_generator.py # continuous synthetic traffic generator

alembic/ # migrations
tests/
├── conftest.py # testcontainers fixtures
├── test_main.py
└── fixtures/openai_response.json

```

## Request flow

```
Client
│
▼
Auth (Postgres) → Rate limit (Redis) → Cache check (Redis)
│ │
│ hit → return
▼
resolve_model() → get_provider()
│
▼
call_with_failover()
│
├─ is_available(primary)? ── no ──► skip, try fallback
│ │ yes
│ ▼
│ primary.chat_completion()
│ │
│ success ──► record metrics, cache, return
│ │
│ failure (ProviderError)
│ │
│ ▼
│ update_circuit(), try fallback provider
│
▼
All providers exhausted → 503
```

## Production deployment (AWS EKS)

The gateway runs live on a managed Kubernetes cluster, fully separate from the local Docker Compose setup below.

**Live URL:** `https://gateway.prajwalkhatiwada.com`
**Grafana:** `http://grafana.prajwalkhatiwada.com`

### Infrastructure

- **Cluster:** Amazon EKS (`eksctl`-provisioned, `us-east-2`), 2-node managed node group
- **Ingress:** AWS Load Balancer Controller, provisions an ALB per Ingress object
- **Database:** RDS Postgres, private subnets, security-group-scoped to cluster nodes only
- **Cache:** Redis, self-hosted in-cluster (intentionally ephemeral, cache/rate-limit data doesn't need to survive restarts)
- **Domain & TLS:** Route 53 hosted zone + ACM certificate, HTTP automatically redirects to HTTPS
- **Autoscaling:** HPA scales the gateway Deployment 2-6 replicas on CPU utilization
- **Secrets:** Kubernetes Secrets for API keys, DB credentials, and tokens, never committed to git

### Access control (IRSA)

The ALB Controller authenticates to AWS using IAM Roles for Service Accounts (IRSA). The cluster's OIDC provider is registered with AWS IAM, and a dedicated IAM Role (scoped to one Service Account) grants only the permissions needed to manage load balancers. No static AWS credentials live in the cluster.

### Deploying from scratch

```bash
# 1. Provision the cluster
eksctl create cluster -f infra/eksctl-cluster.yaml

# 2. Associate IAM OIDC provider (required for IRSA)
eksctl utils associate-iam-oidc-provider \
  --cluster llm-gateway-cluster --region us-east-2 --approve

# 3. Install the ALB Controller (see IRSA setup in project notes for full IAM steps)

# 4. Apply manifests, in order
kubectl apply -f k8s/

# 5. Run database migrations against RDS (from inside the cluster,
#    since RDS is not publicly accessible, see Dockerfile for
#    the alembic/ files baked into the image)
kubectl run migrate-job \
  --image=<your-ecr-image>:latest \
  --namespace=llm-gateway \
  --restart=Never \
  --command -- alembic upgrade head
```

### Observability

`kube-prometheus-stack` (Prometheus + Grafana + Alertmanager) runs in a dedicated `monitoring` namespace, separate from the app-level Prometheus/Grafana used in local dev. A `ServiceMonitor` tells this Prometheus instance to scrape the gateway's `/metrics` endpoint; the same `grafana/dashboard.json` used locally is imported here, alongside a community Kubernetes cluster-monitoring dashboard for node/pod-level health.

### Traffic generator

`scripts/traffic_generator.py` runs continuously on a small EC2 instance (`t3.nano`), sending a steady mix of cached/unique, streaming/non-streaming, and `"auto"`/explicit-model requests to the live gateway. This populates the Grafana dashboards with real, sustained traffic data over multiple days.

```bash
# On the EC2 instance
pip3 install -r scripts/requirements.txt
GATEWAY_API_TOKEN="<real-api-key>" nohup python3 scripts/traffic_generator.py \
  > traffic_gen.log 2>&1 &
```

## Observability

Every request updates a set of Prometheus counters, histograms, and gauges, scraped from `/metrics`:

- `gateway_requests_total{provider, model, status}`: request volume
- `gateway_request_duration_seconds{provider, model}`: latency distribution (enables p50/p95/p99)
- `gateway_cost_cents_total{provider, model}`: spend over time
- `gateway_cache_hits_total` / `gateway_cache_misses_total`: cache effectiveness
- `gateway_provider_failures_total{provider, error_type}`: failure breakdown by provider and cause
- `gateway_circuit_breaker_state{provider}`: live circuit state (0=closed, 0.5=half-open, 1=open)

A pre-built Grafana dashboard (`grafana/dashboard.json`) visualizes request rate, error rate, latency percentiles, cost over time, provider distribution, and cache hit ratio in one view. In production, this same dashboard runs alongside cluster-level node/pod dashboards under `kube-prometheus-stack`.

## Data model

- **`api_keys`**: hashed key, name, active flag, created timestamp
- **`requests`**: one row per call: key, model, provider, tokens, cost, timestamp
- **`usage_summaries`**: one row per (key, day), unique-constrained, running totals

## Local development setup

**Prereqs:** Docker and Docker Compose installed. That's the only requirement for the steps below.

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd llm-inference-gateway
```

### 2. Create your `.env` file

Create a file named `.env` in the repo root (same folder as `docker-compose.yml`) with the following:

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

### 3. Start everything

```bash
docker compose up --build
```

This starts five containers: the gateway, Postgres, Redis, Prometheus, and Grafana.

### 4. Run database migrations

In a separate terminal, while the stack is running:

```bash
docker compose exec gateway alembic upgrade head
```

### 5. Verify it's running

Open `http://localhost:8000/health` in your browser. You should see:

```json
{ "status": "okay" }
```

### 6. Create your first API key

```bash
curl -X POST http://localhost:8000/admin/keys \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-first-key"}'
```

Replace `your-admin-token` with whatever you set as `ADMIN_TOKEN` in `.env`. Save the `api_key` value from the response, it's shown only once.

### 7. Send your first request

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <the-key-from-step-6>" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```

If this returns a real response, everything is working.

### Other running services

- **API docs:** `http://localhost:8000/docs`
- **Prometheus:** `http://localhost:9090`
- **Grafana:** `http://localhost:3000` (login `admin`/`admin` on first run, you'll be asked to set a new password)

### Running locally without Docker (optional)

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

## API docs

`http://127.0.0.1:8000/docs`, click **Authorize** once, applies to every request in session. Raw schema at `/openapi.json`.

## Example request

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer <issued-key>" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```

`"model": "auto"` lets the gateway pick. A real Anthropic model name (e.g. `claude-haiku-4-5-20251001`) routes to Anthropic, same request/response shape either way. If the resolved provider fails, the gateway automatically retries on the alternate provider before returning an error.

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

**Metrics:** `curl http://127.0.0.1:8000/metrics` → Prometheus text format

## Tests

```bash
make test
```

Real, throwaway Postgres + Redis containers via `testcontainers-python`, only external provider calls are mocked (via `respx`), no real API costs during test runs.

```bash
uv run pytest --cov=app tests/
```

Current coverage: **82%+**

Covers: schema validation, auth (missing/invalid/valid key), provider failures (`502`), full mocked-provider flow, cache hits skip provider calls, rate limit `429` + real `Retry-After`, `"auto"` routing by prompt length.

## Tooling

- **Package mgmt:** `uv`
- **Lint/types:** `ruff`, `mypy` (strict)
- **Migrations:** Alembic
- **Metrics:** `prometheus-client`
- **CI:** GitHub Actions. lint, type-check, test on every push
- **Tasks:** `Makefile`. `make run`, `make start-db`, `make test`, `make lint`
- **Container orchestration:** Kubernetes (EKS), `eksctl`, Helm (`kube-prometheus-stack`, AWS Load Balancer Controller)

## Why it's built this way

- **Postgres + Redis, not one datastore:** Postgres holds data that must survive forever; Redis holds data that's fine to lose (worst case: fall back to normal behavior).
- **Keys hashed, never stored raw:** a DB breach never exposes usable credentials.
- **`usage_summaries` separate from `requests`:** reading a running total stays cheap regardless of history size.
- **Pricing table is sourced and dated:** LLM pricing changes; guessed numbers rot silently.
- **Typed provider exceptions, not raw `httpx` errors:** the failover layer catches its own domain's exceptions, never `httpx` directly. Swapping HTTP libraries later touches only the provider files.
- **Circuit breaker is per-provider, not global:** one provider having problems shouldn't affect routing decisions for the other.
- **Self-hosted Redis in production, not ElastiCache:** Redis holds intentionally ephemeral data; a managed service adds cost and setup overhead for no durability benefit here.
- **Migrations run from inside the cluster, not a developer laptop:** RDS is deliberately not publicly accessible; schema changes are applied from a pod that already has network access, keeping the database's attack surface minimal.
