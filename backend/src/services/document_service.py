from fastapi import HTTPException
from src.config import settings
from src.db.database import get_session

from src.crud.document_crud import get_document_by_id, get_document_group_by_id,\
    get_all_document_groups_by_user_id, create_document_group, get_total_documents_by_user_id


class DocumentService:
    """
    Service for managing documents and document groups.
    """

    def __init__(self):
        pass

    async def create_document_group(self, name: str, description: str, color: str, user_id: str):
        """
        Create a new document group
        """
        if settings.USE_DB:
            async for session in get_session():
                document_group = await create_document_group(session, name, description, color, user_id=user_id)
                return document_group
        else:
            pass

    async def get_document_group(self, id: str) -> dict:
        """
        Get document group by id
        """
        if settings.USE_DB:
            async for session in get_session():
                document_group = await get_document_group_by_id(session, id)
                
                if not document_group:
                    raise HTTPException(status_code=404, detail="Document group not found")
                
                return document_group
        else:
            pass

    async def list_document_groups(self, user_id, limit: int = 50, offset: int = 0) -> list[dict]:
        """
        List all document groups
        """

        if settings.USE_DB:
            async for session in get_session():
                document_groups = await get_all_document_groups_by_user_id(session, user_id)
                
                return document_groups
        else:
            pass

    async def delete_document_group(self, id: str):
        """
        Delete document group by id
        """
        if settings.USE_DB:
            async for session in get_session():
                document_group = await get_document_group_by_id(session, id)
                
                if not document_group:
                    raise HTTPException(status_code=404, detail="Document group not found")
                
                await session.delete(document_group)
                await session.commit()
                
                return True
        else:
            pass

    async def delete_document(self, id: str):
        """
        Delete document by id
        """
        if settings.USE_DB:
            async for session in get_session():
                document = await get_document_by_id(session, id)

                if not document:
                    raise HTTPException(status_code=404, detail="Document not found")
                
                await session.delete(document)
                await session.commit()

                return True
        else:
            pass

    async def get_total_documents_by_user_id(self, user_id: str) -> int:
         """Get total documents"""
         async for session in get_session():
            count = await get_total_documents_by_user_id(session, user_id)
            
            return count
