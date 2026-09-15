from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
import logging
import time

from src.api.deps import get_current_user
from src.db.models import User
from src.schemas.user_schema import UserRegisterRequest, UserLoginRequest, UserResponse, UserResponseWithToken, UserRole
from src.crud.user_crud import create_user, get_user_by_email
from src.utils.jwt import generate_jwt_token
from src.db.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def to_user_response(user: User) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, name=user.name, role=user.role)


@router.post("/register", response_model=UserResponseWithToken)
async def register_user(request: UserRegisterRequest):
    """Register a new user."""
    async for session in get_session():
        if await get_user_by_email(session, request.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists with this email")

        # Roles are never taken from the request, otherwise anyone could self-register as admin.
        user = await create_user(session, User(
            email=request.email,
            password_hash=pwd_context.hash(request.password),
            name=request.name,
            role=UserRole.USER.value,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        ))

    return UserResponseWithToken(user=to_user_response(user), token=generate_jwt_token(user))


@router.post("/login", response_model=UserResponseWithToken)
async def login_user(request: UserLoginRequest):
    """Login user"""
    async for session in get_session():
        user = await get_user_by_email(session, request.email)

    if user is None or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return UserResponseWithToken(user=to_user_response(user), token=generate_jwt_token(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user."""
    return to_user_response(current_user)
