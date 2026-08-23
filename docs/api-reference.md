# API Reference

Interactive docs: `http://127.0.0.1:8000/docs` (local) or `https://gateway.prajwalkhatiwada.com/docs` (when the production deployment is live). Click **Authorize** once, it applies to every request in the session. Raw OpenAPI schema at `/openapi.json`.

## Getting access

There are two ways to get an API key.

**Self service sign up**, used by the frontend and available directly:

```bash
curl -X POST http://127.0.0.1:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
```

The email is not verified. This is intentional, to keep sign up to one step for a demo product. The response shows the raw key once, only its hash is stored, and it can never be retrieved again.

**Admin issued**, using `ADMIN_TOKEN`:

```bash
curl -X POST http://127.0.0.1:8000/admin/keys \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "client-name"}'
```

Either way, from here on that client authenticates with `Authorization: Bearer <key>` on every other endpoint.

## `POST /v1/chat/completions`

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer <issued-key>" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```

`"model": "auto"` lets the gateway pick based on prompt length. A real Anthropic model name routes to Anthropic, same request and response shape either way. If the resolved provider fails, the gateway automatically retries on the alternate provider before returning an error.

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

## `GET /dashboard/stats`

Returns aggregated usage for the calling key.

```bash
curl http://127.0.0.1:8000/dashboard/stats?range=7d \
  -H "Authorization: Bearer <issued-key>"
```

`range` accepts `24h`, `7d`, or `30d`.

**Response:**

```json
{
  "total_requests": 42,
  "total_cost": 0.0031,
  "cache_hit_rate": 28.5,
  "avg_latency_ms": 412.3,
  "provider_breakdown": { "openai": 30, "anthropic": 10, "cache": 2 }
}
```

## `GET /dashboard/history`

Returns recent individual requests for the calling key, most recent first.

```bash
curl http://127.0.0.1:8000/dashboard/history?limit=20 \
  -H "Authorization: Bearer <issued-key>"
```

## `POST /dashboard/failover-demo`

Admin only. Forces a provider to appear unhealthy for a set number of seconds, so failover can be demonstrated live without an actual outage.

```bash
curl -X POST http://127.0.0.1:8000/dashboard/failover-demo \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "seconds": 90}'
```

Any request made to that provider within the window automatically routes to the other one instead.

## `GET /health`

```bash
curl http://127.0.0.1:8000/health
```

```json
{ "status": "okay" }
```

## `GET /metrics`

```bash
curl http://127.0.0.1:8000/metrics
```

Returns Prometheus text format metrics, scraped by Prometheus and visualized in Grafana. See **[Architecture](architecture.md)** for the full metric list.

## Error responses

| Status        | Meaning                                                       |
| ------------- | ------------------------------------------------------------- |
| `401`         | Missing or invalid API key                                    |
| `429`         | Rate limit exceeded, includes a real `Retry-After` header     |
| `502` / `503` | Upstream provider failure (after failover attempts exhausted) |

Back to **[README](../README.md)**.
