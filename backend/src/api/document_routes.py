from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from src.services.rag_service import RagService
from src.services.document_service import DocumentService
from src.schemas.document_schema import DocumentGroupResponse
from typing import List, Optional, Dict, Any

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

document_service = DocumentService()

@router.post("/documents/group")
async def create_document_group(name: str = Query(...), description: Optional[str] = Query(default=None), color: str = Query(...)):
    """Create a new document group."""
    try:
        group = await document_service.create_document_group(name, description, color)
        return {"status": "success", "group_id": group.id}
    except Exception as e:
        logger.error(f"Error creating document group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document group.")


@router.get("/documents/groups", response_model=List[DocumentGroupResponse])
async def list_document_groups(limit: int = 50, offset: int = 0):
    """List all document groups."""
    try:
        document_groups = await document_service.list_document_groups(limit=limit, offset=offset)

        return [
            DocumentGroupResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                color=group.color,
                created_at=group.created_at,
                documents=[{"id": doc.id, "filename": doc.filename} for doc in group.documents] if group.documents else None
            )
            for group in document_groups
        ]

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")