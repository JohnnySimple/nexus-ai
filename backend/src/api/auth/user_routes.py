from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import ValidationError
from passlib.context import CryptContext
import logging
import time

from src.db.models import User
from src.schemas.user_schema import UserRegisterRequest, UserLoginRequest, UserResponse, UserResponseWithToken, ResponseError
from src.crud.user_crud import create_user, get_user_by_email, get_user_by_id
from src.utils.jwt import generate_jwt_token
from src.db.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

@router.post("/register", response_model=UserResponseWithToken | ResponseError)
async def register_user(request: UserRegisterRequest):
    """Register a new user."""

    try:
        # check if user already exists
        async for session in get_session():
            existing_user = await get_user_by_email(session, request.email)
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists with this email")
        
        # hash password
        hashed_password = pwd_context.hash(request.password)
        request.password = hashed_password

        # create new user
        async for session in get_session():
            user_to_add = User(
                email=request.email,
                password_hash=hashed_password,
                name=request.name,
                role=request.role,
                created_at=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            user = await create_user(session, user_to_add)

            # generate token
            token = generate_jwt_token(user)

            user = UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role,
            )

            return UserResponseWithToken(
                user=user,
                token=token
            )
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        # return {"error": str(e)}
        return ResponseError(
            error=str(e)
        )
    
@router.post("/login", response_model=UserResponseWithToken | ResponseError)
async def login_user(request: UserLoginRequest):
    """Login user"""
    try:
        async for session in get_session():
            existing_user = await get_user_by_email(session, request.email)

            if(not existing_user):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            
            if pwd_context.verify(request.password, existing_user.password_hash):
            
                # generate token
                token = generate_jwt_token(existing_user)

                user = UserResponse(
                    id=str(existing_user.id),
                    email=existing_user.email,
                    name=existing_user.name,
                    role=existing_user.role,
                )

                return UserResponseWithToken(
                    user=user,
                    token=token
                )
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    except Exception as e:
        logger.error(f"Error logging user in: {e}")
        return ResponseError(
            error=str(e)
        )