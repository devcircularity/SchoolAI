# SchoolOps AI Gateway

FastAPI gateway that routes intents to the Core API. LLM: Ollama (`llama3.2:latest`). Slot-state stored in Redis.

## Quick Start

```bash
cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
```

## Docker
```bash
docker compose up --build
```

## Endpoints
- `POST /ai/chats`
- `GET  /ai/chats/{id}/messages`
- `POST /ai/chats/{id}/messages`
- `GET  /healthz`

See `tests/*.http` for acceptance-flow examples.
