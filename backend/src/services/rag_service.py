"""Rag Service Module"""

from src.services.embeddings import Embeddings
import time
import uuid
import logging

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
        document_id = str(uuid.uuid4())
        metadata["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        document = {
            "id": document_id,
            "content": content,
            "metadata": metadata
        }

        self.embedding_service.save_embedding(document)

        return document_id
    

    async def list_documents(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """
        List all ingested documents
        """

        documents = []

        try:
            loaded_data = self.embedding_service.load_embedding()
            for doc in loaded_data:
                documents.append(doc)
            return documents
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")