from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from src.db.models import QuerySession
from src.schemas.query_schema import QuerySessionCreateRequest

import time


async def create_query_session(session: AsyncSession, payload: QuerySessionCreateRequest) -> QuerySession:
    """
    Create a new query session
    """
    query_session = QuerySession(
        query=payload.query,
        response=payload.response,
        model=payload.model,
        top_k=payload.top_k,
        temperature=payload.temperature,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        retrieved_chunks=payload.retrieved_chunks,
        created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        response_time=payload.response_time,
        user_id=payload.user_id     
    )

    session.add(query_session)
    await session.commit()
    await session.refresh(query_session)
    return query_session


async def get_query_session_by_id(session: AsyncSession, id: str) -> QuerySession | None:
    """Retrieve a query session by its ID"""
    result = await session.execute(select(QuerySession).where(QuerySession.id == id))
    query_session = result.scalar_one_or_none()
    return query_session


async def get_query_sessions_by_user_id(session: AsyncSession, user_id: str) -> QuerySession | None:
    """Retrieve a query session by user id"""
    results = await session.execute(select(QuerySession).where(QuerySession.user_id == user_id))
    query_sessions = results.scalars().all()
    return query_sessions
