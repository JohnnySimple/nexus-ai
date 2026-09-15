from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.db.models import User


async def create_user(session: AsyncSession, user: User) -> User:
    """Create a new user in the database"""
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    """Retrieve a user by ID"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Retrieve a user by ID"""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    return user
