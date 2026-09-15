from fastapi import HTTPException

import src.helper_functions as helper_functions
from src.crud import document_crud
from src.crud.document_crud import VectorStoreStats
from src.db.database import get_session
from src.db.models import DocumentGroup


class DocumentService:
    """
    Service for managing documents and document groups. Every operation is scoped to a user.
    """

    async def create_document_group(self, name: str, description: str, color: str, user_id: str) -> DocumentGroup:
        """Create a new document group"""
        async for session in get_session():
            return await document_crud.create_document_group(session, name, description, color, user_id=user_id)

    async def get_document_group(self, group_id: str, user_id: str) -> DocumentGroup:
        """Get a document group owned by the user"""
        async for session in get_session():
            document_group = await document_crud.get_document_group_by_id(session, group_id, user_id)

        if not document_group:
            raise HTTPException(status_code=404, detail="Document group not found")
        return document_group

    async def list_document_groups(self, user_id: str) -> list[DocumentGroup]:
        """List the user's document groups"""
        async for session in get_session():
            return await document_crud.get_all_document_groups_by_user_id(session, user_id)

    async def delete_document_group(self, group_id: str, user_id: str) -> None:
        """Delete a document group together with its documents and stored files"""
        async for session in get_session():
            document_group = await document_crud.get_document_group_by_id(session, group_id, user_id)
            if not document_group:
                raise HTTPException(status_code=404, detail="Document group not found")

            document_ids = [document.id for document in document_group.documents]
            await document_crud.delete_documents(session, document_ids)
            await document_crud.delete_document_group(session, group_id)
            await session.commit()

        for document_id in document_ids:
            helper_functions.delete_document_file(document_id)

    async def delete_document(self, document_id: str, user_id: str) -> None:
        """Delete a document owned by the user, with its embeddings and stored file"""
        async for session in get_session():
            owned = await document_crud.resolve_document_ids(session, user_id, [document_id], [])
            if not owned:
                raise HTTPException(status_code=404, detail="Document not found")

            await document_crud.delete_documents(session, owned)
            await session.commit()

        helper_functions.delete_document_file(document_id)

    async def get_vector_store_stats(self, user_id: str) -> VectorStoreStats:
        """Document, page and embedding totals for the user"""
        async for session in get_session():
            return await document_crud.get_vector_store_stats(session, user_id)
