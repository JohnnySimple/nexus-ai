
from fastapi import APIRouter, HTTPException

from typing import List, Optional, Dict, Any
import logging

from src.schemas.rag_schema import DocumentIngestRequest, DocumentIngestResponse, Status, DocumentListResponse
from src.services.rag_service import RagService

logger = logging.getLogger(__name__)
router = APIRouter()

rag_service = RagService()

@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(request: DocumentIngestRequest):
    """Ingest a document into the RAG system."""
    try:
        paginated_data = rag_service.get_paginated_data(request.content)

        doc_id = await rag_service.ingest_document(
            content=paginated_data,
            metadata={
                "filename": request.filename,
                **(request.metadata or {})
            }
        )
        
        return DocumentIngestResponse(
            document_id=doc_id,
            status=Status.SUCCESS
        )
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        return {"error": str(e)}

@router.get("/documents", response_model=List[DocumentListResponse])
async def list_documents(limit: int = 50, offset: int = 0):
    """List all ingested documents."""
    try:
        documents = await rag_service.list_documents(limit=limit, offset=offset)
        
        return [
            DocumentListResponse(
                id=doc["id"],
                filename=doc["metadata"].get("filename", "Unknown"),
                content=[{"page_number": page["page_number"], "content": ''.join(page['text'])[:200] + "..." if len(''.join(page['text'])) > 200 else ''.join(page['text'])} for page in doc["content"]],
                metadata=doc["metadata"],
                created_at=doc["metadata"].get("created_at", "Unknown")
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")