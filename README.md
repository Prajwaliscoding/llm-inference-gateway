# LLM Inference Gateway

A lightweight API gateway that proxies requests to LLM providers (currently OpenAI), with authentication, structured logging, and error handling — built as an OpenAI-compatible drop-in endpoint.

## Features

- OpenAI-compatible `/v1/chat/completions` endpoint
- Bearer token authentication
- Structured JSON logging with request tracing
- Async request handling via httpx
- 95%+ test coverage

## Running locally

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker (optional, for containerized run)

### Setup

1. Clone the repo
2. Create a `.env` file with:

```
OPENAI_API_KEY=your-openai-key
GATEWAY_API_TOKEN=your-chosen-token
```

3. Install dependencies:

```bash
   uv sync
```

4. Run the server:

```bash
   make run
```

### Running with Docker

```bash
docker compose up
```

### Running tests

```bash
make test
```

## Example request

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}'
```
