from fastapi import APIRouter, Depends

from src.api.deps import get_current_user
from src.db.models import User
from src.services.query_service import QueryService, serialize_query_session

router = APIRouter()

query_service = QueryService()


@router.get("/query-session")
async def list_query_sessions(distinct_conversation: bool = False, current_user: User = Depends(get_current_user)):
    """List the current user's query sessions, optionally only the first turn of each conversation."""
    return await query_service.get_query_sessions_by_user_id(current_user.id, distinct_conversation)


@router.get("/query-session/conversation/{conversation_id}")
async def get_query_sessions_by_conversation_id(conversation_id: str, current_user: User = Depends(get_current_user)):
    """Get the turns of a conversation, oldest first."""
    query_sessions = await query_service.get_query_sessions_by_conversation_id(conversation_id, current_user.id)
    return [serialize_query_session(s) for s in query_sessions]


@router.delete("/query-session/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: User = Depends(get_current_user)):
    """Delete conversation by conversation id."""
    await query_service.delete_conversation(conversation_id, current_user.id)
    return {"status": "success", "message": "Conversation deleted successfully."}


@router.get("/query-session/{id}")
async def get_query_session_by_id(id: str, current_user: User = Depends(get_current_user)):
    """Get query session by id."""
    return serialize_query_session(await query_service.get_query_session_by_id(id, current_user.id))
