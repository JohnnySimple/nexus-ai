import jwt
import pytest
from fastapi.testclient import TestClient

import src.api.auth.user_routes as user_routes
import src.api.deps as deps
from src.config import settings
from src.db.models import User
from src.main import app
from src.utils.jwt import decode_jwt_token, generate_jwt_token


async def fake_get_session():
    yield None


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def known_user(monkeypatch, user):
    """Make `user` the only account get_current_user can resolve."""
    async def get_user_by_id(session, user_id):
        return user if user_id == user.id else None

    monkeypatch.setattr(deps, "get_session", fake_get_session)
    monkeypatch.setattr(deps, "get_user_by_id", get_user_by_id)
    return user


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_token_round_trip(user):
    assert decode_jwt_token(generate_jwt_token(user))["sub"] == user.id


def test_expired_token_is_rejected(monkeypatch, user):
    monkeypatch.setattr(settings, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", -1)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_jwt_token(generate_jwt_token(user))


@pytest.mark.parametrize("path", [
    "/api/auth/me",
    "/api/rag/documents",
    "/api/rag/query?query=revenue",
    "/api/documents/group",
    "/api/query/query-session",
    "/api/dashboard/stats",
])
def test_user_scoped_routes_require_a_token(client, path):
    response = client.get(path)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_token_signed_with_another_key_is_rejected(client, known_user):
    forged = jwt.encode({"sub": known_user.id, "exp": 4102444800}, "not-the-server-key-not-the-server-key", algorithm="HS256")

    assert client.get("/api/auth/me", headers=bearer(forged)).status_code == 401


def test_token_for_unknown_user_is_rejected(client, known_user):
    stranger = User(id="user-gone", email="gone@example.com", password_hash="x", name="Gone", role="user", created_at="")

    assert client.get("/api/auth/me", headers=bearer(generate_jwt_token(stranger))).status_code == 401


def test_me_returns_the_token_owner(client, known_user):
    response = client.get("/api/auth/me", headers=bearer(generate_jwt_token(known_user)))

    assert response.status_code == 200
    assert response.json() == {"id": known_user.id, "email": known_user.email, "name": "Ada", "role": "user"}


def test_registration_cannot_self_assign_admin(client, monkeypatch):
    async def no_existing_user(session, email):
        return None

    async def create_user(session, user):
        return user

    monkeypatch.setattr(user_routes, "get_session", fake_get_session)
    monkeypatch.setattr(user_routes, "get_user_by_email", no_existing_user)
    monkeypatch.setattr(user_routes, "create_user", create_user)

    response = client.post("/api/auth/register", json={
        "email": "eve@example.com", "password": "correct-horse-battery", "name": "Eve", "role": "admin",
    })

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "user"


def test_duplicate_registration_is_an_error_status(client, monkeypatch, user):
    async def existing_user(session, email):
        return user

    monkeypatch.setattr(user_routes, "get_session", fake_get_session)
    monkeypatch.setattr(user_routes, "get_user_by_email", existing_user)

    response = client.post("/api/auth/register", json={
        "email": user.email, "password": "correct-horse-battery", "name": "Ada",
    })

    assert response.status_code == 400
