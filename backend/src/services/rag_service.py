"""Rag Service Module"""

from src.services.embeddings import Embeddings
import time
import uuid
import logging

from src.config import settings
from src.crud.document_crud import get_all_documents, get_document_by_id
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class RagService:
    
    """
    This module provides functionalities for RAG (Retrieval-Augmented Generation).
    """

    def __init__(self):
        self.embedding_service = Embeddings()


    def get_paginated_data(self, content):
        """
        Paginate content if not already paginated
        """
        if not isinstance(content, list):
            return [{
                "page_number": 0,
                "text": content
            }]
        else:
            return content
        
    
    async def ingest_document(self, content: str, metadata: dict) -> str:
        """
        Ingest a document into the RAG system.
        """
        try:
            document_id = str(uuid.uuid4())
            metadata["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

            document = {
                "id": document_id,
                "content": content,
                "metadata": metadata
            }

            await self.embedding_service.save_embedding(document)

            return document_id
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            raise e
    

    async def list_documents(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """
        List all ingested documents
        """

        if settings.USE_DB:
            from src.db.database import get_session
            async for session in get_session():
                documents = await get_all_documents(session)
                document_list = []

                for doc in documents:

                    single_document = {
                        "id": doc.id,
                        "metadata": {
                            "filename": doc.filename,
                            "created_at": doc.created_at
                        },
                        "content": []
                    }
                    
                    for page in doc.pages:
                        
                        page_content = {
                            "page_number": page.page_number,
                            "text": page.text,
                            "chunks": [],
                            "embedding": []
                        }
                        
                        for embedding in page.embeddings:
                            page_content["chunks"].append(embedding.chunk_text)
                            page_content["embedding"].append(embedding.embedding)

                        single_document["content"].append(page_content)
                                        
                    document_list.append(single_document)
                return document_list
        else:
            documents = []

            try:
                loaded_data = self.embedding_service.load_embedding()
                for doc in loaded_data:
                    documents.append(doc)
                return documents
            except Exception as e:
                logger.error(f"Failed to list documents: {e}")
    
    async def query_documents(self, query: str, top_k: int = 5, document_ids: list[str] = []):
        """Query documents in the RAG system."""
        try:
            results = self.embedding_service.search(query, top_k, document_ids)
            return results
        except Exception as e:
            logger.error(f"Document query failed: {e}")
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the RAG system.
        """
        try:
            return self.embedding_service.delete_embedding(document_id)
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False