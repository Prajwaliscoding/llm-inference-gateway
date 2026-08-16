# API Reference

Interactive docs: `http://127.0.0.1:8000/docs` (local) — click **Authorize** once, it applies to every request in the session. Raw OpenAPI schema at `/openapi.json`.

## Getting access

Keys are not self-service. The **admin** creates a key using `ADMIN_TOKEN`, then hands the raw key to whoever needs access.

```bash
curl -X POST http://127.0.0.1:8000/admin/keys \
  -H "Authorization: Bearer your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "client-name"}'
```

The response shows the raw key **once**. Only its hash is stored, it can never be retrieved again. From here on, that client authenticates with `Authorization: Bearer <that-key>` on `/v1/chat/completions`.

## `POST /v1/chat/completions`

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer <issued-key>" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```

`"model": "auto"` lets the gateway pick based on prompt length. A real Anthropic model name routes to Anthropic, same request/response shape either way. If the resolved provider fails, the gateway automatically retries on the alternate provider before returning an error.

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

Returns Prometheus text-format metrics, scraped by Prometheus and visualized in Grafana. See **[Architecture](architecture.md)** for the full metric list.

## Error responses

| Status        | Meaning                                                       |
| ------------- | ------------------------------------------------------------- |
| `401`         | Missing or invalid API key                                    |
| `429`         | Rate limit exceeded, includes a real `Retry-After` header     |
| `502` / `503` | Upstream provider failure (after failover attempts exhausted) |

Back to **[README](../README.md)**.
