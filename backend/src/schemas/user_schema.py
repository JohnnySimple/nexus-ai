import enum
from pydantic import BaseModel, Field


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class UserRegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    name: str

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str

class UserResponseWithToken(BaseModel):
    user: UserResponse
    token: str

class ResponseError(BaseModel):
    error: str
