from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from src.api.deps import get_current_user
from src.db.models import DocumentGroup, User
from src.schemas.document_schema import DocumentGroupResponse
from src.services.document_service import DocumentService

router = APIRouter()

document_service = DocumentService()


def to_group_response(group: DocumentGroup) -> DocumentGroupResponse:
    return DocumentGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        color=group.color,
        created_at=group.created_at,
        documents=[{"id": doc.id, "filename": doc.filename} for doc in group.documents] if group.documents else None
    )


@router.post("/group")
async def create_document_group(
    name: str = Query(...),
    description: Optional[str] = Query(default=None),
    color: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    """Create a new document group."""
    group = await document_service.create_document_group(name, description or "", color, current_user.id)
    return {"status": "success", "group_id": group.id}


@router.get("/group", response_model=List[DocumentGroupResponse])
async def list_document_groups(current_user: User = Depends(get_current_user)):
    """List all document groups."""
    return [to_group_response(group) for group in await document_service.list_document_groups(current_user.id)]


@router.get("/group/{id}", response_model=DocumentGroupResponse)
async def get_document_group(id: str, current_user: User = Depends(get_current_user)):
    """Get document group by id."""
    return to_group_response(await document_service.get_document_group(id, current_user.id))


@router.delete("/group/{id}")
async def delete_document_group(id: str, current_user: User = Depends(get_current_user)):
    """Delete document group by id, including its documents."""
    await document_service.delete_document_group(id, current_user.id)
    return {"status": "success", "message": "Document group deleted successfully."}


@router.delete("/{id}")
async def delete_document(id: str, current_user: User = Depends(get_current_user)):
    """Delete document by id."""
    await document_service.delete_document(id, current_user.id)
    return {"status": "success", "message": "Document deleted successfully."}
