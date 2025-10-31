from fastapi import APIRouter, Query, HTTPException
from src.services.query_service import QueryService
from src.schemas.query_schema import QuerySessionCreateRequest

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

query_service = QueryService()

@router.post("/query-session")
async def create_query_session(request: QuerySessionCreateRequest):
    """Create a query session"""

    try:
        query_session = await query_service.create_query_session(request)
        return query_session
    except Exception as e:
        logger.error(f"Error creating query session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create query session.")
    

@router.get("/query-session/{id}")
async def get_query_session_by_id(id: str):
    """Get query session by id."""
    try:
        query_session = await query_service.get_query_session_by_id(id)

        return query_session

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to get query session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get query session.")
    
@router.get("/query-session/user/{user_id}")
async def get_query_session_by_user_id(user_id: str):
    """Get query session by id."""
    try:
        query_session = await query_service.get_query_sessions_by_user_id(user_id)

        return query_session

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to get query session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get query session.")