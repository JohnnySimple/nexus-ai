import ast
import json

from fastapi import HTTPException

from src.crud import query_crud
from src.db.database import get_session
from src.db.models import QuerySession
from src.schemas.query_schema import QuerySessionCreateRequest


def normalize_retrieved_chunks(value) -> list:
    """
    Return retrieved_chunks as a list. Sessions saved before chunks were stored as JSON
    hold a Python repr string, so fall back to parsing that.
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return []
    return value if isinstance(value, list) else []


def serialize_query_session(query_session: QuerySession) -> dict:
    data = query_session.model_dump()
    data["retrieved_chunks"] = normalize_retrieved_chunks(data["retrieved_chunks"])
    return data


class QueryService:
    """
    Service for managing query sessions. Every read and delete is scoped to a user.
    """

    async def create_query_session(self, payload: QuerySessionCreateRequest) -> QuerySession:
        """Create query session"""
        async for session in get_session():
            return await query_crud.create_query_session(session, payload)

    async def get_query_session_by_id(self, id: str, user_id: str) -> QuerySession:
        """Get a query session owned by the user"""
        async for session in get_session():
            query_session = await query_crud.get_query_session_by_id(session, id, user_id)

        if not query_session:
            raise HTTPException(status_code=404, detail="Query session not found")
        return query_session

    async def get_query_sessions_by_user_id(self, user_id: str, distinct_conversation: bool) -> list[dict]:
        """Get the user's query sessions, newest first"""
        async for session in get_session():
            query_sessions = await query_crud.get_query_sessions_by_user_id(session, user_id, distinct_conversation)
        return [serialize_query_session(s) for s in query_sessions]

    async def get_query_sessions_by_conversation_id(self, conversation_id: str, user_id: str) -> list[QuerySession]:
        """Get the turns of a user's conversation, oldest first"""
        async for session in get_session():
            query_sessions = await query_crud.get_query_sessions_by_conversation_id(session, conversation_id, user_id)

        if not query_sessions:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return query_sessions

    async def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        """Delete a user's conversation"""
        async for session in get_session():
            deleted = await query_crud.delete_conversation_by_conversation_id(session, conversation_id, user_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")

    async def get_total_query_sessions_by_user_id(self, user_id: str) -> int:
        async for session in get_session():
            return await query_crud.get_total_query_sessions_by_user_id(session, user_id)

    async def get_average_response_time_by_user_id(self, user_id: str) -> float:
        async for session in get_session():
            return await query_crud.get_average_response_time_by_user_id(session, user_id)

    async def get_daily_response_times_by_user_id(self, user_id: str):
        async for session in get_session():
            return await query_crud.get_daily_average_response_times_by_user_id(session, user_id)

    async def get_daily_query_counts_by_user_id(self, user_id: str):
        async for session in get_session():
            return await query_crud.get_daily_query_counts_by_user_id(session, user_id)
