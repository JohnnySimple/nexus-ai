# nexus-ai

Retrieval-augmented generation over your documents: FastAPI + Postgres/pgvector backend, sentence-transformer
embeddings with cross-encoder reranking, Ollama for generation, and a React dashboard.

## Backend

Requires Python 3.11+, Postgres with the [pgvector](https://github.com/pgvector/pgvector) extension available, and
[Ollama](https://ollama.com) with the configured model pulled (`ollama pull mistral`).

```bash
cd backend
cp .env.example .env          # set DATABASE_URL and JWT_SECRET_KEY (both required)
poetry install --with dev
poetry run alembic upgrade head   # also enables the vector extension
poetry run uvicorn src.main:app --reload --port 8000
```

Embedding and reranker models load at startup (`WARM_MODELS_ON_STARTUP`), so the first query isn't slow.

### Auth

Register or log in via `/api/auth/register` / `/api/auth/login` to get a JWT, then send it as
`Authorization: Bearer <token>`. Every document, group, conversation and stats route is scoped to the token's user;
resources belonging to other users return 404.

### Streaming queries

`GET /api/rag/query?stream=true` returns server-sent events: `status` (progress), `result` (same payload as the
non-streaming response), then `done`. Failures after the stream starts arrive as an `error` event.

### Migrations

```bash
poetry run alembic revision --autogenerate -m "message"   # create from models
poetry run alembic upgrade head                           # apply
```

Optional approximate-nearest-neighbour index for large corpora:

```sql
create index on chunk_embeddings using hnsw (embedding vector_cosine_ops);
```

### Tests

```bash
poetry run ruff check src tests
poetry run pytest
```

Integration tests run real pgvector queries and are skipped unless `TEST_DATABASE_URL` points at a disposable
database, e.g. `TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/nexus_test`. CI runs everything
against a pgvector service container, including migrations on a fresh database.

### GPU

Install torch with CUDA support:
```
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```
or
```
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

## Frontend

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev   # http://localhost:5001
```

## Docker

`docker compose up --build` builds the backend and an nginx-served frontend. Point `DATABASE_URL` and
`OLLAMA_API_URL` in `backend/.env` at `host.docker.internal` to reach Postgres and Ollama on the host.
