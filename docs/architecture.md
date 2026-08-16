# Architecture

## Request flow

```
Client
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
    └── circuit_breaker.py     # per-provider sliding-window circuit breaker

grafana/
└── dashboard.json      # pre-built Grafana dashboard

k8s/                     # production Kubernetes manifests
infra/                   # cluster provisioning (eksctl config)
scripts/                 # traffic generator
alembic/                 # migrations
tests/
├── conftest.py           # testcontainers fixtures
├── test_main.py
└── fixtures/openai_response.json
```

## Data model

- **`api_keys`**: hashed key, name, active flag, created timestamp
- **`requests`**: one row per call: key, model, provider, tokens, cost, timestamp
- **`usage_summaries`**: one row per (key, day), unique-constrained, running totals

## Observability

Every request updates a set of Prometheus counters, histograms, and gauges, scraped from `/metrics`:

- `gateway_requests_total{provider, model, status}`: request volume
- `gateway_request_duration_seconds{provider, model}`: latency distribution (enables p50/p95/p99)
- `gateway_cost_cents_total{provider, model}`: spend over time
- `gateway_cache_hits_total` / `gateway_cache_misses_total`: cache effectiveness
- `gateway_provider_failures_total{provider, error_type}`: failure breakdown by provider and cause
- `gateway_circuit_breaker_state{provider}`: live circuit state (0=closed, 0.5=half-open, 1=open)

The pre-built Grafana dashboard (`grafana/dashboard.json`) visualizes request rate, error rate, latency percentiles, cost over time, provider distribution, and cache hit ratio in one view.

## Why it's built this way

- **Postgres + Redis, not one datastore**: Postgres holds data that must survive forever; Redis holds data that's fine to lose (worst case: fall back to normal behavior).
- **Keys hashed, never stored raw**: a DB breach never exposes usable credentials.
- **`usage_summaries` separate from `requests`**: reading a running total stays cheap regardless of history size.
- **Pricing table is sourced and dated**: LLM pricing changes; guessed numbers rot silently.
- **Typed provider exceptions, not raw `httpx` errors**: the failover layer catches its own domain's exceptions, never `httpx` directly. Swapping HTTP libraries later touches only the provider files.
- **Circuit breaker is per-provider, not global**: one provider having problems shouldn't affect routing decisions for the other.
- **Self-hosted Redis in production, not ElastiCache**: Redis holds intentionally ephemeral data; a managed service adds cost and setup overhead for no durability benefit here.
- **Migrations run from inside the cluster, not a developer laptop**: RDS is deliberately not publicly accessible; schema changes are applied from a pod that already has network access, keeping the database's attack surface minimal.

Back to **[README](../README.md)**.
