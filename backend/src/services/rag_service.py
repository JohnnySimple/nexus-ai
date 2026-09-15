"""Rag Service Module"""
import time
from typing import AsyncIterator

from fastapi import HTTPException

from src.config import settings
from src.crud import document_crud
from src.db.database import get_session
from src.db.models import Document, User
from src.schemas.query_schema import QuerySessionCreateRequest
from src.schemas.rag_schema import DocumentQueryRequest
from src.services import rag_helpers
from src.services.embeddings import get_embedding_service
from src.services.query_service import QueryService, serialize_query_session


class RagService:
    """
    Document ingestion and the retrieval-augmented query pipeline.
    """

    def __init__(self, query_service: QueryService | None = None):
        self.query_service = query_service or QueryService()

    async def ingest_document(self, *, document_id: str, filename: str, pages: list[dict],
                              group_id: str, user_id: str) -> str:
        """Chunk, embed and store a document"""
        await get_embedding_service().save_document(
            document_id=document_id,
            filename=filename,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            pages=pages,
            group_id=group_id,
            user_id=user_id,
        )
        return document_id

    async def get_document(self, document_id: str, user_id: str) -> Document:
        """Get a document owned by the user"""
        async for session in get_session():
            document = await document_crud.get_document_by_id(session, document_id, user_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    async def list_documents(self, user_id: str) -> list[Document]:
        """List the user's documents"""
        async for session in get_session():
            return await document_crud.get_all_documents_by_user_id(session, user_id)

    async def answer_query_events(self, request: DocumentQueryRequest, user: User) -> AsyncIterator[dict]:
        """
        Run retrieval, optional generation and persistence for a query.
        Yields {"event": "status"} progress events, then a single {"event": "result"} with the output.
        Streaming and non-streaming endpoints both use this, so they cannot drift apart.
        """
        start_time = time.perf_counter()

        history = []
        if request.conversation_id:
            history = await self.query_service.get_query_sessions_by_conversation_id(request.conversation_id, user.id)

        yield {"event": "status", "data": {"message": "Retrieving relevant chunks"}}
        async for session in get_session():
            document_ids = await document_crud.resolve_document_ids(
                session, user.id, request.document_ids, request.document_group_ids or []
            )
        chunks = await get_embedding_service().search(request.query, document_ids, request.top_k)
        context = rag_helpers.build_context(chunks)

        output = {
            "query": request.query,
            "results": [
                {"document": {"id": chunk["document_id"], "filename": chunk["document_name"]}, "relevant_chunks": [chunk]}
                for chunk in chunks
            ],
            "context": context,
        }

        if request.with_llm_response:
            yield {"event": "status", "data": {"message": "Generating response"}}
            prompt, answer = await rag_helpers.generate_answer(request.query, context, history)
            output["final_prompt"] = prompt
            output["llm_response"] = answer

        query_session = await self.query_service.create_query_session(QuerySessionCreateRequest(
            query=request.query,
            response=output.get("llm_response", ""),
            model=settings.DEFAULT_LLM_MODEL,
            top_k=request.top_k,
            retrieved_chunks=chunks,
            user_id=user.id,
            document_ids=document_ids,
            conversation_id=request.conversation_id or None,
            response_time=round(time.perf_counter() - start_time, 2),
        ))
        output["query_session"] = serialize_query_session(query_session)

        yield {"event": "result", "data": output}

    async def answer_query(self, request: DocumentQueryRequest, user: User) -> dict:
        """Run the query pipeline to completion and return its result"""
        async for event in self.answer_query_events(request, user):
            if event["event"] == "result":
                return event["data"]
        raise RuntimeError("Query pipeline finished without a result")
