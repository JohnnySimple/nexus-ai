"""Shared FastAPI dependencies."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.crud.user_crud import get_user_by_id
from src.db.database import get_session
from src.db.models import User
from src.utils.jwt import decode_jwt_token

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    """Resolve the user from the bearer token. Every user-scoped route depends on this."""
    if credentials is None:
        raise _unauthorized("Not authenticated")

    try:
        payload = decode_jwt_token(credentials.credentials)
    except jwt.PyJWTError:
        raise _unauthorized("Invalid or expired token") from None

    user = None
    async for session in get_session():
        user = await get_user_by_id(session, payload["sub"])

    if user is None:
        raise _unauthorized("User no longer exists")
    return user
