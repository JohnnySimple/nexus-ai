import os

# Settings are read when src.config is imported, so the environment must be set first.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-long-enough-for-hs256-signing")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/nexus_test")
os.environ["WARM_MODELS_ON_STARTUP"] = "false"

import pytest  # noqa: E402

from src.db.models import User  # noqa: E402


@pytest.fixture
def user() -> User:
    return User(
        id="user-ada",
        email="ada@example.com",
        password_hash="unused",
        name="Ada",
        role="user",
        created_at="2026-01-01 00:00:00",
    )
