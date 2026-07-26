## Architecture

```
Client → Gateway → {OpenAI, Anthropic}
            ↓
            Postgres (persistent state)
            Redis (cache, rate limits)
            Prometheus/Grafana (observability)
```

- **Client** — the app calling the gateway
- **Gateway** — the decision-maker: routes each request, logs it, checks cache
- **Providers** — OpenAI/Anthropic, who actually run inference
- **Postgres** — permanent record of every request and rolled-up usage
- **Redis** — fast cache and rate-limit tracking
- **Prometheus/Grafana** — observability dashboards
