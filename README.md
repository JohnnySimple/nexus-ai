# nexus-ai

## Alembic
#### Create migration from models. NB:// setup in alembic/env.py
alembic revision --autogenerate -m "message"

#### Run latest migration
alembic upgrade head

enable vector extension in your postgres database
