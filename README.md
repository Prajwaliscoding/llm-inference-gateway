# LLM Inference Gateway

An API gateway that proxies requests to multiple LLM providers (OpenAI and Anthropic), with real auth, persistence, caching, rate limiting, cost tracking, smart routing, automatic failover, circuit breaking, and full observability. Built as an OpenAI compatible drop in endpoint, with a React dashboard on top for signing up, testing requests, and viewing usage.

**Live demo status:** This gateway is deployed to AWS on demand rather than run continuously, to control infrastructure cost. The frontend at `https://gateway-app.prajwalkhatiwada.com` stays live for free on Vercel and will tell you clearly if the backend is offline. The code, architecture, and screenshots of every screen are all in this repo. See [docs/production-deployment.md](docs/production-deployment.md) for the full deployment writeup with real screenshots from when it was live.

## Why this exists

A single provider LLM integration breaks the moment that provider has an outage, and it cannot scale intelligently with traffic or cost. This gateway sits in front of multiple providers, routes requests based on model and prompt characteristics, fails over automatically when a provider goes down, and gives full visibility into cost and performance per API key. It was built and deployed on real production infrastructure (AWS EKS), not just run locally.

## Features

**Backend**

- Multi provider abstraction with automatic failover and per provider circuit breaking
- Real auth: hashed API keys, checked on every request, never stored raw
- Self service sign up that issues a key instantly, shown once
- Redis caching and atomic rate limiting per key
- Smart routing: `"model": "auto"` resolves to a specific model based on prompt length
- Cost tracking and usage accounting per key, per day
- Full observability: Prometheus metrics with a pre built Grafana dashboard
- Production deployed on Kubernetes (EKS), with HTTPS, autoscaling, and cluster wide monitoring
- Tested against real infrastructure (`testcontainers-python`), 82%+ coverage

**Frontend**

- Single page React dashboard: sign up, live playground, usage stats, and a failover demo
- Real time stats pulled from the same data the backend logs, not mocked
- Deployed separately on Vercel, stays live even when the backend is torn down

## Tech stack

Python, FastAPI, PostgreSQL, Redis, AWS (EKS, RDS, EC2, Route 53, ACM, IAM), Kubernetes, Helm, Prometheus, Grafana, Docker, React, Vite, Tailwind CSS, Vercel

## Documentation

- **[Local Setup](docs/local-setup.md)**: get the backend and frontend running on your machine
- **[Production Deployment](docs/production-deployment.md)**: full AWS and EKS runbook, from a bare AWS account to a live HTTPS endpoint, with screenshots of the real deployed infrastructure
- **[API Reference](docs/api-reference.md)**: endpoints, auth flow, request and response examples
- **[Architecture](docs/architecture.md)**: request flow, data model, and the reasoning behind key design decisions

## Quick start

```bash
git clone https://github.com/Prajwaliscoding/llm-inference-gateway.git
cd llm-inference-gateway
docker compose up --build
```

Full first run instructions, including creating your first API key, are in **[docs/local-setup.md](docs/local-setup.md)**.

## Production deployment

This gateway has been deployed live to AWS EKS multiple times, with a real domain, HTTPS through ACM, autoscaling, RDS Postgres, and full Prometheus and Grafana observability. The infrastructure is torn down between deployments to avoid ongoing cost, since this is a personal project rather than a service with real users. The full deployment process, real screenshots, and lessons learned from actually running this on AWS are documented in **[docs/production-deployment.md](docs/production-deployment.md)**.

![Grafana dashboard populated with real data](docs/images/grafana-dashboard-full.png)

## Performance

Benchmarked with k6 against the live deployment.

|     | Cache hit | Live provider call |
| --- | --------- | ------------------ |
| p50 | 56ms      | 550ms              |
| p90 | 66ms      | 945ms              |
| p95 | 96ms      | 1.03s              |

Cache hit requests measure the gateway's own overhead: auth check, Redis lookup, response formatting. That overhead stays under 100ms at p95. Requests that require a live call to OpenAI are roughly ten times slower, almost entirely due to the provider's own round trip time, which is outside the gateway's control. This is a concrete, measured demonstration of what the caching layer actually buys in latency, not just a theoretical benefit.

## Design decisions and trade offs

**Auth is API key based, not full user accounts.** Signing up returns a real API key that is checked on every request, but the email behind it is never verified, and there is no password or session. This was a deliberate choice to keep sign up to one step for a demo product, and it is called out directly on the sign up page itself so it is never a hidden gap. A production version would add verified accounts and session based login.

**The circuit breaker treats client errors and provider outages differently on purpose.** A 400 from a provider, such as a bad request or a billing issue, surfaces directly to the caller instead of silently retrying on another provider. Masking a real client side problem behind an automatic retry would hide bugs rather than fix them. Only errors that indicate the provider itself is unhealthy trigger failover.

**RDS is reached through a Route 53 private hosted zone, not a hardcoded IP.** When the EKS cluster was rebuilt in a fresh VPC, RDS's default DNS hostname resolved to its public IP from the peered VPC instead of its private IP, which the security groups did not allow. Hardcoding the private IP into the config would have worked but defeats the purpose of using DNS. A private hosted zone with an A record pointing at the current private IP keeps the config as a stable hostname while still being simple to update if the IP ever changes.

**`resolve_model()` only checks prompt length for the `"auto"` routing mode, not cost or current provider health.** This is a known simplification. A more complete version would factor in current per provider pricing and live circuit breaker state when picking a model, not just prompt length.

## Tests

```bash
make test
```

Real, throwaway Postgres and Redis containers via `testcontainers-python`. Only external provider calls are mocked. Current coverage is 82%+.

## Tooling

`uv`, `ruff`, `mypy` (strict), Alembic, GitHub Actions CI, `eksctl`, Helm, npm

## What I learned

Building this taught me more about the difference between it works on my machine and it works in production than any tutorial could. A few specific things that were genuinely hard.

Cross VPC networking is not automatic. Rebuilding the EKS cluster after a teardown put it in a different VPC than the existing RDS instance, and getting them to actually talk to each other required VPC peering, routes in every subnet's route table, security group rules in both directions, and eventually a private hosted zone once I discovered that RDS's default DNS resolves to a public IP from a peered VPC. None of this shows up until you actually tear down and rebuild real infrastructure, which is exactly why I built that discipline in from the start instead of leaving everything running.

Exception boundaries matter more than I expected. Early on, raw `httpx` exceptions were leaking past my provider abstraction without being translated into typed errors, which meant my failover logic never actually ran when a provider failed. Fixing this taught me to think carefully about exactly where in a call stack an error needs to become a different, more meaningful type.

Cache hits are easy to forget about in logging. My request logging only fired for cache misses at first, which meant my own usage dashboard was quietly wrong about cache hit rate for every user. It is an easy bug to make and an easy one to miss, since everything still looks like it is working.

## Author

Prajwal Khatiwada, CS Undergraduate
