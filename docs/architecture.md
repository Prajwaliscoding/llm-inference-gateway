# Architecture

## Request flow

```
Client (React frontend, or any HTTP client)
│
▼
Auth (Postgres) → Rate limit (Redis) → Cache check (Redis)
│                                        │
│                                        hit → return
▼
resolve_model() → get_provider()
│
▼
call_with_failover()
│
├─ is_available(primary)? ── no ──► skip, try fallback
│  │ yes
│  ▼
│  primary.chat_completion()
│  │
│  success ──► record metrics, cache, return
│  │
│  failure (ProviderError)
│  │
│  ▼
│  update_circuit(), try fallback provider
│
▼
All providers exhausted → 503
```

## Directory structure

```
app/
├── main.py            # routes, middleware, request pipeline
├── auth.py            # bearer token verification (client + admin)
├── security.py        # key generation & hashing
├── config.py           # env-based settings
├── database.py         # async engine, session factory, get_db
├── redis_client.py     # async Redis client
├── cache.py            # cache key building, save/find
├── rate_limit.py        # Redis-backed rate limiting
├── pricing.py           # pricing table + cost calc
├── usage.py             # request log + usage summary writes
├── dashboard.py          # stats, history, failover-demo endpoints
├── logging_config.py    # structlog setup
├── metrics.py            # Prometheus metric definitions
├── models/               # SQLAlchemy models
├── schemas/               # Pydantic request/response models
└── providers/
    ├── base.py               # LLMProvider ABC
    ├── exceptions.py          # typed provider exception hierarchy
    ├── openai_provider.py
    ├── anthropic_provider.py  # + response normalization
    ├── factory.py             # get_provider(), resolve_model(), get_fallback_provider()
    ├── failover.py            # call_with_failover() - retry orchestration
    └── circuit_breaker.py     # per-provider sliding-window circuit breaker, plus manual override for the failover demo

frontend/
├── src/
│   ├── App.jsx            # top-level state: landing -> signup -> dashboard
│   ├── api.js              # thin fetch wrapper, adds auth header
│   └── components/
│       ├── LandingPage.jsx
│       ├── SignUpForm.jsx
│       ├── StatsCards.jsx
│       ├── ProviderChart.jsx
│       ├── HistoryTable.jsx
│       └── Playground.jsx
└── public/
    └── architecture-diagram.png

grafana/
└── dashboard.json      # pre-built Grafana dashboard

k8s/                     # production Kubernetes manifests
infra/                   # cluster provisioning (eksctl config, IAM policy)
scripts/                 # traffic generator, k6 load test scripts
alembic/                 # migrations
tests/
├── conftest.py           # testcontainers fixtures
├── test_main.py
└── fixtures/openai_response.json
```

## Data model

- **`api_keys`**: hashed key, name, email, active flag, created timestamp
- **`request_log`**: one row per call: key, model, provider, tokens, cost, cache hit, latency, timestamp
- **`usage_summary`**: one row per (key, day), unique-constrained, running totals

## Observability

Every request updates a set of Prometheus counters, histograms, and gauges, scraped from `/metrics`:

- `gateway_requests_total{provider, model, status}`: request volume
- `gateway_request_duration_seconds{provider, model}`: latency distribution (enables p50/p95/p99)
- `gateway_cost_cents_total{provider, model}`: spend over time
- `gateway_cache_hits_total` / `gateway_cache_misses_total`: cache effectiveness
- `gateway_provider_failures_total{provider, error_type}`: failure breakdown by provider and cause
- `gateway_circuit_breaker_state{provider}`: live circuit state (0=closed, 0.5=half-open, 1=open)

The pre-built Grafana dashboard (`grafana/dashboard.json`) visualizes request rate, error rate, latency percentiles, cost over time, provider distribution, and cache hit ratio in one view. Separately, the React frontend's own dashboard shows the same kind of data scoped to a single API key, using `/dashboard/stats` and `/dashboard/history`. Grafana is for operating the whole system; the frontend dashboard is for one user to see their own usage.

## Why it's built this way

- **Postgres + Redis, not one datastore**: Postgres holds data that must survive forever, like accounts and billing history. Redis holds data that's fine to lose, like cache entries and rate limit counters.
- **Keys hashed, never stored raw**: even if the database is ever breached, no usable credentials are exposed.
- **`usage_summary` separate from `request_log`**: reading a user's running total stays fast no matter how much history piles up, since it doesn't have to scan every past request.
- **Pricing table is sourced and dated**: LLM prices change often, so a hardcoded guess would quietly become wrong over time.
- **Typed provider exceptions, not raw `httpx` errors**: the failover logic only understands its own error types, not the HTTP library's. If the HTTP library ever changes, only the provider files need to change.
- **Circuit breaker is per-provider, not global**: one provider having problems shouldn't affect routing decisions for the other.
- **Self-hosted Redis in production, not a managed service**: the data in Redis here is disposable by design, so paying for a managed service adds cost without adding real value.
- **Migrations run from inside the cluster, not a developer laptop**: the database isn't reachable from the open internet. Schema changes run from a pod that's already inside the network, keeping the database's exposure as small as possible.
- **Frontend deployed separately from the backend**: the React app lives on Vercel for free, all the time. The backend only runs on AWS when it's actively being shown, to avoid ongoing cost. The frontend can tell when the backend is offline and explains why instead of just failing.

Back to **[README](../README.md)**.
