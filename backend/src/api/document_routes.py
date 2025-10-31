from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from src.services.rag_service import RagService
from src.services.document_service import DocumentService
from src.schemas.document_schema import DocumentGroupResponse
from typing import List, Optional, Dict, Any

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

document_service = DocumentService()

@router.post("/group")
async def create_document_group(name: str = Query(...), description: Optional[str] = Query(default=None), color: str = Query(...)):
    """Create a new document group."""
    try:
        group = await document_service.create_document_group(name, description, color)
        return {"status": "success", "group_id": group.id}
    except Exception as e:
        logger.error(f"Error creating document group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document group.")


@router.get("/group", response_model=List[DocumentGroupResponse])
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
    

@router.get("/group/{id}", response_model=DocumentGroupResponse)
async def get_document_group(id: str):
    """Get document group by id."""
    try:
        group = await document_service.get_document_group(id)

        return DocumentGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            color=group.color,
            created_at=group.created_at,
            documents=[{"id": doc.id, "filename": doc.filename} for doc in group.documents] if group.documents else None
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to get document group: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document group.")


@router.delete("/group/{id}")
async def delete_document_group(id: str):
    """Delete document group by id."""
    try:
        await document_service.delete_document_group(id)
        return {"status": "success", "message": "Document group deleted successfully."}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to delete document group: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document group.")


