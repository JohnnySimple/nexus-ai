import asyncio
import logging
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

import src.helper_functions as helper_functions
from src.api.deps import get_current_user
from src.api.rag_stream import stream_query_events
from src.config import settings
from src.db.models import Document, User
from src.schemas.rag_schema import DocumentIngestResponse, DocumentQueryRequest, DocumentResponse, Status
from src.services import rag_helpers
from src.services.document_service import DocumentService
from src.services.ollama_client_service import get_llm_client
from src.services.rag_service import RagService

logger = logging.getLogger(__name__)
router = APIRouter()

rag_service = RagService()
document_service = DocumentService()

MEDIA_TYPES = {"pdf": "application/pdf", "txt": "text/plain"}
PREVIEW_LENGTH = 200


def to_document_response(document: Document) -> DocumentResponse:
    pages = sorted(document.pages, key=lambda page: page.page_number)
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        content=[
            {
                "page_number": page.page_number,
                "content": page.text[:PREVIEW_LENGTH] + "..." if len(page.text) > PREVIEW_LENGTH else page.text,
                "chunks": [chunk.chunk_text for chunk in page.embeddings],
            }
            for page in pages
        ],
        metadata={"filename": document.filename, "created_at": document.created_at},
        created_at=document.created_at,
    )


@router.post("/documents/upload", response_model=DocumentIngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    group_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    """Upload and ingest a document into the RAG system."""
    filename = os.path.basename(file.filename or "")
    file_type = helper_functions.get_file_type(filename)
    if file_type is None:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types are {settings.SUPPORTED_FILE_TYPES}.")

    # 404s if the group belongs to someone else
    await document_service.get_document_group(group_id, current_user.id)

    document_id = str(uuid.uuid4())
    os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
    # Never build paths from the client-supplied filename.
    temp_file_path = os.path.join(settings.TEMP_UPLOAD_DIR, f"{document_id}.{file_type}")
    with open(temp_file_path, "wb") as f:
        f.write(await file.read())

    try:
        pages = await asyncio.to_thread(helper_functions.get_file_content, temp_file_path)
        helper_functions.save_file_to_permanent_location(temp_file_path, document_id, filename)
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    try:
        await rag_service.ingest_document(
            document_id=document_id,
            filename=filename,
            pages=pages,
            group_id=group_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        helper_functions.delete_document_file(document_id)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        helper_functions.delete_document_file(document_id)
        raise

    return DocumentIngestResponse(document_id=document_id, status=Status.SUCCESS)


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str, current_user: User = Depends(get_current_user)):
    """Serve document file for viewing or downloading."""
    document = await rag_service.get_document(document_id, current_user.id)

    try:
        file_path = helper_functions.get_document_file_path(document_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document: {document_id} file not found.") from None

    return FileResponse(
        path=file_path,
        filename=document.filename,
        media_type=MEDIA_TYPES.get(helper_functions.get_file_type(document.filename), "application/octet-stream"),
        content_disposition_type="inline",
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific document by its ID."""
    return to_document_response(await rag_service.get_document(document_id, current_user.id))


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(current_user: User = Depends(get_current_user)):
    """List all ingested documents."""
    return [to_document_response(document) for document in await rag_service.list_documents(current_user.id)]


@router.get("/rewrite-query")
async def rewrite_query(query: str = Query(...), current_user: User = Depends(get_current_user)):
    """Rewrite a conversational question into a standalone search query."""
    return {"results": await rag_helpers.rewrite_query(query)}


@router.get("/query")
async def query_documents(
    query: str = Query(...),
    top_k: int = Query(5, ge=1, le=50),
    document_ids: List[str] = Query([]),
    document_group_ids: List[str] = Query([]),
    with_llm_response: bool = Query(False),
    stream: bool = Query(False),
    conversation_id: str = Query(""),
    current_user: User = Depends(get_current_user),
):
    """Query documents in the RAG system."""
    request = DocumentQueryRequest(
        query=query,
        top_k=top_k,
        document_ids=document_ids,
        document_group_ids=document_group_ids,
        with_llm_response=with_llm_response,
        stream=stream,
        conversation_id=conversation_id or None,
    )

    if request.stream:
        return StreamingResponse(
            stream_query_events(rag_service.answer_query_events(request, current_user)),
            media_type="text/event-stream",
        )
    return await rag_service.answer_query(request, current_user)


@router.get("/llms")
async def list_available_llms(current_user: User = Depends(get_current_user)):
    """List all available LLMs."""
    return await get_llm_client().list_models()
