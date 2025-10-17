
from fastapi import APIRouter, HTTPException

from typing import List, Optional, Dict, Any
import logging

from src.schemas.rag_schema import DocumentIngestRequest, DocumentIngestResponse,\
    Status, DocumentResponse, DocumentQueryRequest, DocumentQueryResponse, ErrorResponse
from src.schemas.chat_schema import ChatRequest

from src.services.rag_service import RagService
from src.config import settings
import src.helper_functions as helper_functions

logger = logging.getLogger(__name__)
router = APIRouter()

rag_service = RagService()

@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(request: DocumentIngestRequest):
    """Ingest a document into the RAG system."""
    try:

        doc_type = helper_functions.get_file_type(request.filename)

        if doc_type not in settings.SUPPORTED_FILE_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types are {settings.SUPPORTED_FILE_TYPES}.")
        
        content = helper_functions.get_file_content(request.filename)
        
        request.content = content

        paginated_data = rag_service.get_paginated_data(request.content)

        doc_id = await rag_service.ingest_document(
            content=paginated_data,
            metadata={
                "filename": request.filename.split("/")[-1],
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
        # return ErrorResponse(
        #     message=f"Error ingesting document: {str(e)}",
        #     status=Status.FAILURE
        # )

@router.get("documents/{document_id}", response_model=Optional[DocumentResponse])
async def get_document(document_id: str):
    """Get a specific document by its ID."""
    try:
        documents = await rag_service.list_documents()
        for doc in documents:
            if doc["id"] == document_id:
                return DocumentResponse(
                    id=doc["id"],
                    filename=doc["metadata"].get("filename", "Unknown"),
                    content=[{"page_number": page["page_number"],
                              "content": ''.join(page['text'])[:200] + "..." if len(''.join(page['text'])) > 200 else ''.join(page['text']),
                              "chunks": doc["chunks"][page_index]}
                              for page_index, page in enumerate(doc["content"])],
                    metadata=doc["metadata"],
                    created_at=doc["metadata"].get("created_at", "Unknown"),
                    # embeddings=[{"page_number": index,
                    #              "embeddings": item.tolist()}
                    #             for index, item in enumerate(doc["embedding"])]
                )
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(limit: int = 50, offset: int = 0):
    """List all ingested documents."""
    try:
        documents = await rag_service.list_documents(limit=limit, offset=offset)

        return [
            DocumentResponse(
                id=doc["id"],
                filename=doc["metadata"].get("filename", "Unknown"),
                content=[{"page_number": page["page_number"],
                          "content": ''.join(page['text'])[:200] + "..." if len(''.join(page['text'])) > 200 else ''.join(page['text']),
                          "chunks": documents[doc_index]["chunks"][page_index]}
                          for page_index, page in enumerate(doc["content"])],
                metadata=doc["metadata"],
                created_at=doc["metadata"].get("created_at", "Unknown")
            )
            for doc_index, doc in enumerate(documents)
        ]

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the RAG system."""
    try:
        success = await rag_service.delete_document(document_id)
        if success:
            return {"status": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.post("/query", response_model=DocumentQueryResponse)
async def query_documents(request: DocumentQueryRequest):
    """Query documents in the RAG system."""
    results = await rag_service.query_documents(
        query=request.query,
        top_k=request.top_k,
        document_ids=request.document_ids
    )

    # sort all the relevant chunks by score and return top_k
    # all_relevant_chunks = [(chunk_text, score, doc_id, page_num), ...]
    all_relevant_chunks = []
    for res in results:
        all_relevant_chunks.extend(res["relevant_chunks"])
    all_relevant_chunks = sorted(all_relevant_chunks, key=lambda x: x[1], reverse=True)[:request.top_k]

    # get top k chunks
    top_chunks = all_relevant_chunks[:request.top_k]

    # flatten top_chunks
    # t_chunks = [chunk for sub in top_chunks for chunk in sub]


    # results_content = "\n".join(f"- {chunk[0]}" for res in results for chunk in res["relevant_chunks"])
    context = "\n".join(f"- {chunk[0]}" for res in top_chunks for chunk in res)

    if request.with_llm_response:
        prompt_template = helper_functions.get_rag_prompt_template()
        prompt = prompt_template.format(question=request.query, context=context)

        from src.services.ollama_client_service import OllamaClient
        ollama_client = OllamaClient()

        chat_request = ChatRequest(
            model=settings.OLLAMA_MODEL_MISTRAL,
            messages=[{"role": "user", "content": prompt}]
        )

        llm_response = await ollama_client.generate(
            {
                "model": chat_request.model,
                "prompt": prompt
            }
        )

        return {
            "query": request.query,
            "results": results,
            # "results_content": results_content,
            "context": context,
            "final_prompt": prompt,
            "llm_response": llm_response.get("response", "")
        }

    return {
        "query": request.query,
        "results": results,
        # "results_content": results_content,
        "context": context,
    }