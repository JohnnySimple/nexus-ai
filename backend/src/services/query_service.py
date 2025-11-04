from fastapi import HTTPException
from src.config import settings
from src.db.database import get_session

from src.crud.query_crud import create_query_session, get_query_session_by_id, get_query_sessions_by_user_id,\
    get_query_sessions_by_conversation_id, get_total_query_sessions_by_user_id


class QueryService:
    """
    Service for managing query sessions
    """

    def __init__(self):
        pass

    async def create_query_session(self, payload):
        """Create query session"""
        async for session in get_session():
                query_session = await create_query_session(session, payload)
                return query_session
        
    async def get_query_session_by_id(self, id):
         """Get query session by id"""
         async for session in get_session():
                query_session = await get_query_session_by_id(session, id)
                
                if not query_session:
                    raise HTTPException(status_code=404, detail="Query session not found")
                
                return query_session
    
    async def get_query_sessions_by_user_id(self, user_id, distinct_conversation):
         """Get query session by user id"""
         async for session in get_session():
                query_sessions = await get_query_sessions_by_user_id(session, user_id, distinct_conversation)
                
                if not query_sessions:
                    raise HTTPException(status_code=404, detail="Query session not found")
                
                return query_sessions
         
    async def get_total_query_sessions_by_user_id(self, user_id):
         """Get total query sessions by user id"""
         async for session in get_session():
            count = await get_total_query_sessions_by_user_id(session, user_id)
            
            return count
    
    async def get_query_sessions_by_conversation_id(self, conversation_id):
         """Get query sessions by conversation id"""
         async for session in get_session():
              query_sessions = await get_query_sessions_by_conversation_id(session, conversation_id)
              
              if not query_sessions:
                   raise HTTPException(status_code=404, detail="No query sessions found.")
              
              return query_sessions
