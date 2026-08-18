# Circle 

A minimal OpenRouter-style LLM gateway built with FastAPI. It exposes one OpenAI-compatible `/v1/chat/completions` endpoint, routes requests to different providers, enforces API-key authentication and rate limits, and logs usage/cost metrics to Postgres.

It is intentionally lightweight, educational, and easy to extend. The goal is to show how a gateway can sit in front of multiple model providers and normalize the experience for clients.

## Why this project exists

The project demonstrates a simple but realistic architecture for an LLM gateway:

- One unified client-facing API
- Multiple upstream model providers behind it
- Per-provider request translation adapters
- Unified streaming response handling
- Gateway-level auth and request limiting
- Usage accounting for observability and cost tracking

This is a good sample project for learning API abstraction, request routing, provider adapters, and backend service composition.


[Architecture]

<img width="2527" height="1313" alt="image" src="https://github.com/user-attachments/assets/1f028b24-47ce-4b3d-8306-1ed1bc3a7857" />

```

### Request flow

```text
client -> gateway/auth -> rate_limit -> resolve_provider(model)
        -> adapter.build_request() -> provider API
        -> provider stream -> adapter.stream() -> normalized chunks
        -> client (SSE)
        -> usage ledger (Postgres)
```

## How routing works

The gateway expects model names in this format:

```text
provider/model_id
```

Examples:

```text
openai/gpt-4o-mini
anthropic/claude-sonnet-4-6
groq/llama-3.3-70b-versatile
```

The router splits the string on `/`, looks up the provider config in `app/config.py`, reads the matching provider API key from environment variables, and instantiates the right adapter.

This keeps the rest of the system provider-agnostic.

## Provider adapters

Each provider implements a shared adapter contract defined in `app/adapters/base.py`.

The adapter is responsible for:

- translating the unified request into provider-specific request bodies
- setting provider-specific headers and auth
- calling the upstream API
- normalizing the chunks back into a consistent OpenAI-compatible streaming format

The adapter layer is where all provider-specific logic lives.

## Features

- OpenAI-compatible `/v1/chat/completions` endpoint
- Provider abstraction via model names
- OpenAI, Anthropic, and Groq support
- Streaming response support
- Gateway API key validation
- Redis-based fixed-window rate limiting
- Postgres usage/cost ledger
- Docker Compose setup for local development
- Minimal infrastructure footprint

## Tech stack

- Python 3.11
- FastAPI
- httpx
- Redis
- PostgreSQL
- Docker + Docker Compose

## Project structure

```text
openrouter-clone/
├── app/
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── anthropic_adapter.py
│   │   ├── base.py
│   │   ├── groq_adapter.py
│   │   └── openai_adapter.py
│   ├── auth.py
│   ├── config.py
│   ├── ledger.py
│   ├── main.py
│   ├── rate_limit.py
│   └── router.py
├── scripts/
│   └── init_db.sql
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── test_client.py
├── README.md
└── .env
```

## Quick start

1. Copy the example env file:

```bash
cp .env.example .env
```

2. Fill in your real API keys:

```env
GATEWAY_API_KEYS=test-key-123
RATE_LIMIT_PER_MINUTE=20
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GROQ_API_KEY=...
```

3. Start the stack with Docker:

```bash
docker compose up --build
```

4. Open the app:

- Gateway: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Testing the gateway

### Using the included test script

```bash
python test_client.py "openai/gpt-4o-mini"
python test_client.py "anthropic/claude-sonnet-4-6"
python test_client.py "groq/llama-3.3-70b-versatile"
```

### Using curl

```bash
curl -N -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

### Using Python requests

```python
import requests

url = "http://localhost:8000/v1/chat/completions"
headers = {
    "Authorization": "Bearer test-key-123",
    "Content-Type": "application/json",
}
body = {
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "hi"}],
}

resp = requests.post(url, headers=headers, json=body, stream=True)
print(resp.status_code)
print(resp.text[:1000])
```

## Environment variables

### Gateway auth

```env
GATEWAY_API_KEYS=test-key-123
```

This is the key a client must send in the `Authorization` header using the `Bearer` scheme.

### Provider keys

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GROQ_API_KEY=...
```

These are not exposed to clients; they are stored only in the gateway environment.

### Redis / Postgres

```env
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql://openrouter:openrouter@postgres:5432/openrouter
```

These are supplied automatically by Docker Compose, but can be overridden for local runs.

## Usage ledger / cost tracking

The project logs token usage and estimated cost to Postgres via the `usage_log` table.

The general flow is:

1. provider streams response chunks back to the gateway
2. usage tokens from the final stream are captured
3. provider and model pricing are looked up from `app/config.py`
4. usage is written to Postgres for observability or future billing work

## Running without Docker

If you want to run the gateway outside of Docker:

```bash
pip install -r requirements.txt
```

Then ensure local Redis and Postgres are running and set env values accordingly:

```bash
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://openrouter:openrouter@localhost:5432/openrouter
uvicorn app.main:app --reload
```

You should also apply the schema in `scripts/init_db.sql` to your Postgres database.

## API behavior

The endpoint is:

```text
POST /v1/chat/completions
```

The API is intentionally modeled to feel OpenAI-like, but it is still a gateway wrapper around multiple providers.

## Strengths of the design

- Clear separation between gateway logic and provider adapters
- Minimal moving parts
- Easy to extend with new providers
- Close to a production-ready gateway skeleton
- Good starting point for demos, portfolios, or LLM gateway interviews

## Future extensions worth building

This project intentionally leaves out a few real-world production features. These are all good candidates for the next iteration:

- Fallback routing across multiple providers
- Token bucket or sliding-window rate limiting
- Prompt caching in Redis
- A small React or Next.js playground UI
- Better error classification and retry policies
- Provider-specific retry/backoff logic
- API usage dashboards and cost summaries

## Troubleshooting

### 401 Unauthorized

Usually means your gateway key is wrong or missing.

Check:

```env
GATEWAY_API_KEYS=test-key-123
```

and send:

```http
Authorization: Bearer test-key-123
```

### 500 Internal Server Error

Usually means a malformed JSON body or a provider failure caused by invalid upstream credentials or quota issues.

Check the container logs:

```bash
docker compose logs -f gateway
```

### Provider quota or access issues

These are normal provider-side problems, not app bugs. Common symptoms:

- OpenAI: insufficient quota
- Anthropic: credit balance too low
- Groq: model not found / terms required / deprecated model

You must fix those in the provider console.


