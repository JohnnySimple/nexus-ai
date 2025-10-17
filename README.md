# nexus-ai

## Alembic
#### Create migration from models. NB:// setup in alembic/env.py
alembic revision --autogenerate -m "message"

#### Run latest migration
alembic upgrade head

Enable vector extension in your postgres database

Create index

```
create index on chunk_embeddings using ivfflat (embedding vector_cosine_ops) with (lists=100)
```
