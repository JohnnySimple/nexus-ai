
import os
from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from starlette.responses import StreamingResponse

from typing import List, Optional, Dict, Any
import logging

from src.schemas.rag_schema import DocumentIngestRequest, DocumentIngestResponse,\
    Status, DocumentResponse, DocumentQueryRequest, DocumentQueryResponse, ErrorResponse
from src.schemas.chat_schema import ChatRequest

from src.services.rag_service import RagService
from src.services.query_service import QueryService
from src.schemas.query_schema import QuerySessionCreateRequest
from src.config import settings
import src.helper_functions as helper_functions
import src.services.rag_helpers as rag_helpers

import requests
import json
import time

logger = logging.getLogger(__name__)
router = APIRouter()

rag_service = RagService()
query_service = QueryService()

@router.post("/documents/upload", response_model=DocumentIngestResponse)
async def upload_document(file: UploadFile = File(...), group_id: Optional[str] = Query(default=None)):
    """Upload and ingest a document into the RAG system."""
    try:
        doc_type = helper_functions.get_file_type(file.filename)

        if doc_type not in settings.SUPPORTED_FILE_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types are {settings.SUPPORTED_FILE_TYPES}.")
        
        temp_file_path = os.path.join(settings.TEMP_UPLOAD_DIR, file.filename)
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        content = helper_functions.get_file_content(temp_file_path)

        os.remove(temp_file_path)  # Clean up the temporary file

        paginated_data = rag_service.get_paginated_data(content)

        doc_id = await rag_service.ingest_document(
            content=paginated_data,
            metadata={
                "filename": file.filename.split("/")[-1],
                # **(request.metadata or {})
            },
            group_id=group_id
        )
        
        return DocumentIngestResponse(
            document_id=doc_id,
            status=Status.SUCCESS
        )
        
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        return {"error": str(e)}

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

@router.get("/documents/{document_id}", response_model=Optional[DocumentResponse])
async def get_document(document_id: str):
    """Get a specific document by its ID."""
    try:
        # documents = await rag_service.list_documents()
        # for doc_index, doc in enumerate(documents):
        #     if doc["id"] == document_id:
        #         return DocumentResponse(
        #             id=doc["id"],
        #             filename=doc["metadata"].get("filename", "Unknown"),
        #             content=[{"page_number": page["page_number"],
        #                       "content": ''.join(page['text'])[:200] + "..." if len(''.join(page['text'])) > 200 else ''.join(page['text']),
        #                     #   "chunks": doc["chunks"][page_index]
        #                         # "chunks": documents[doc_index]["chunks"]
        #                         "chunks": page["chunks"]
        #                       }
        #                       for page_index, page in enumerate(doc["content"])],
        #             metadata=doc["metadata"],
        #             created_at=doc["metadata"].get("created_at", "Unknown"),
        #             # embeddings=[{"page_number": index,
        #             #              "embeddings": item.tolist()}
        #             #             for index, item in enumerate(doc["embedding"])]
        #         )
        # raise HTTPException(status_code=404, detail="Document not found")
        document = await rag_service.get_document(document_id)
        return DocumentResponse(
            id=document["id"],
            filename=document["metadata"].get("filename", "Unknown"),
                    content=[{"page_number": page["page_number"],
                              "content": ''.join(page['text'])[:200] + "..." if len(''.join(page['text'])) > 200 else ''.join(page['text']),
                            #   "chunks": doc["chunks"][page_index]
                                # "chunks": documents[doc_index]["chunks"]
                                "chunks": page["chunks"]
                              }
                              for page_index, page in enumerate(document["content"])],
                    metadata=document["metadata"],
                    created_at=document["metadata"].get("created_at", "Unknown"),
                    # embeddings=[{"page_number": index,
                    #              "embeddings": item.tolist()}
                    #             for index, item in enumerate(doc["embedding"])]
        )
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(limit: int = 50, offset: int = 0):
    """List all ingested documents."""
    try:
        documents = await rag_service.list_documents(limit=limit, offset=offset)

        # if settings.USE_DB:
        return [
            DocumentResponse(
                id=doc["id"],
                filename=doc["metadata"]["filename"],
                content=[{"page_number": single_page["page_number"],
                        "content": ''.join(single_page['text'])[:200] + "..." if len(''.join(single_page['text'])) > 200 else ''.join(single_page['text']),
                        "chunks": single_page["chunks"]
                        }
                        for single_page_index, single_page in enumerate(doc["content"])],
                metadata=doc["metadata"],
                created_at=doc["metadata"]["created_at"]
            )
            for doc_index, doc in enumerate(documents)
        ]
        # else:
        #     return [
        #         DocumentResponse(
        #             id=doc["id"],
        #             filename=doc["metadata"].get("filename", "Unknown"),
        #             content=[{"page_number": page["page_number"],
        #                     "content": ''.join(page['text'])[:200] + "..." if len(''.join(page['text'])) > 200 else ''.join(page['text']),
        #                     "chunks": documents[doc_index]["chunks"][page_index]
        #                     # "chunks": documents[doc_index]["chunks"]
        #                     }
        #                     for page_index, page in enumerate(doc["content"])],
        #             metadata=doc["metadata"],
        #             created_at=doc["metadata"].get("created_at", "Unknown")
        #         )
        #         for doc_index, doc in enumerate(documents)
        #     ]

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

# @router.delete("/documents/{document_id}")
# async def delete_document(document_id: str):
#     """Delete a document from the RAG system."""
#     try:
#         success = await rag_service.delete_document(document_id)
#         if success:
#             return {"status": "Document deleted successfully"}
#         else:
#             raise HTTPException(status_code=404, detail="Document not found")
#     except Exception as e:
#         logger.error(f"Failed to delete document: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/query", response_model=DocumentQueryResponse)
async def query_documents(
    query: str = Query(...),
    top_k: int = Query(5),
    document_ids: List[str] = Query([]),
    with_llm_response: bool = Query(False),
    stream: bool = Query(False),
    model: Optional[str] = "",
    user_id: str = "",
    conversation_id: str = ""
):
    """Query documents in the RAG system."""
    request = DocumentQueryRequest(
        query=query,
        top_k=top_k,
        document_ids=document_ids,
        with_llm_response=with_llm_response,
        stream=stream
    )

    if request.stream:
        from src.api.rag_stream import query_docs
        return StreamingResponse(query_docs(request), media_type="text/event-stream")
    
    results = await rag_service.query_documents(
        query=request.query,
        top_k=request.top_k,
        document_ids=request.document_ids
    )

    # retrieve conversation history
    history = []
    if conversation_id:
        history = await query_service.get_query_sessions_by_conversation_id(conversation_id)

    context = rag_helpers.build_context(results, request)
    output = await rag_helpers.get_query_output(request, context, results, history)

    # save query session
    relevant_chunks = [chunk for doc in output["results"] for chunk in doc["relevant_chunks"]]

    query_session_payload = QuerySessionCreateRequest(
        query=query,
        response=output["llm_response"],
        model=model,
        top_k=top_k,
        retrieved_chunks=str(relevant_chunks),
        user_id=user_id
    )

    await query_service.create_query_session(query_session_payload)

    return output


@router.get("/llms")
async def list_available_llms():
    """List all available LLMs."""
    try:

        response = requests.get(f"{settings.OLLAMA_API_URL}/api/tags")

        text = response.text

        if response.status_code == 200:
            return json.loads(text)

    except Exception as e:
        logger.error(f"Failed to list available LLMs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list available LLMs: {str(e)}")