"""Chunk embedding, reranking and vector search."""
import asyncio
import logging
from functools import lru_cache

import torch
from sentence_transformers import CrossEncoder, SentenceTransformer

import src.helper_functions as helper_functions
from src.config import settings
from src.crud.document_crud import create_document_with_pages_and_embeddings, search_similar_chunks
from src.db.database import get_session
from src.db.models import ChunkEmbedding, Document, Page
from src.services.rag_helpers import rank_chunks

logger = logging.getLogger(__name__)


class Embeddings:

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL, device=self.device)

        dimension = self.model.get_sentence_embedding_dimension()
        if dimension != settings.EMBEDDING_DIMENSION:
            raise RuntimeError(
                f"{settings.SENTENCE_TRANSFORMER_MODEL} produces {dimension}-d embeddings but "
                f"EMBEDDING_DIMENSION is {settings.EMBEDDING_DIMENSION}. Update the setting and "
                "migrate chunk_embeddings.embedding to match."
            )
        self._reranker: CrossEncoder | None = None

    @property
    def reranker(self) -> CrossEncoder:
        """Cross-encoder, loaded once on first use rather than per query."""
        if self._reranker is None:
            self._reranker = CrossEncoder(settings.CROSS_ENCODER_MODEL, device=self.device)
        return self._reranker

    async def save_document(self, *, document_id: str, filename: str, created_at: str, pages: list[dict],
                            group_id: str, user_id: str) -> None:
        """Chunk and embed pages, then persist the document with its pages and chunk embeddings."""
        chunked_pages = helper_functions.create_page_chunks(
            pages, settings.CHUNK_MAX_TOKENS, settings.CHUNK_OVERLAP_TOKENS, settings.CHUNK_MIN_SENTENCE_LENGTH
        )
        all_chunks = [chunk for page in chunked_pages for chunk in page["chunks"]]
        if not all_chunks:
            raise ValueError("No extractable text found in document.")

        # Encoding is CPU/GPU bound; run it off the event loop so other requests keep being served.
        vectors = await asyncio.to_thread(
            self.model.encode, all_chunks, convert_to_numpy=True, show_progress_bar=False
        )

        pages_to_save = []
        vector_index = 0
        for page in chunked_pages:
            chunk_embeddings = []
            for chunk in page["chunks"]:
                chunk_embeddings.append(ChunkEmbedding(chunk_text=chunk, embedding=vectors[vector_index]))
                vector_index += 1

            pages_to_save.append({
                "page": Page(page_number=page["page_number"], text=page["text"], sentence_count=page["sentence_count"]),
                "embeddings": chunk_embeddings,
            })

        document = Document(
            id=document_id,
            filename=filename,
            created_at=created_at,
            document_group_id=group_id,
            user_id=user_id
        )
        async for session in get_session():
            await create_document_with_pages_and_embeddings(session, document, pages_to_save)

    async def search(self, query: str, document_ids: list[str], top_k: int) -> list[dict]:
        """Return the top_k chunks from the given documents for the query, most relevant first."""
        if not document_ids:
            return []

        query_vector = await asyncio.to_thread(
            self.model.encode, query, convert_to_numpy=True, show_progress_bar=False
        )
        candidate_count = top_k * 2 if settings.RERANK_TOP_K else top_k

        async for session in get_session():
            rows = await search_similar_chunks(session, query_vector.tolist(), document_ids, candidate_count)

        chunks = [
            {
                "document_name": row["document_name"],
                "answer": row["chunk_text"],
                "similarity_score": round(float(row["similarity_score"]), 4),
                "document_id": row["document_id"],
                "page_number": row["page_number"],
                "rerank_score": None,
            }
            for row in rows
        ]

        if settings.RERANK_TOP_K and chunks:
            scores = await asyncio.to_thread(
                self.reranker.predict, [(query, chunk["answer"]) for chunk in chunks], show_progress_bar=False
            )
            for chunk, score in zip(chunks, scores):
                chunk["rerank_score"] = round(float(score), 4)

        return rank_chunks(chunks, top_k)


@lru_cache(maxsize=1)
def get_embedding_service() -> Embeddings:
    """Process-wide embedding service; models load on first call."""
    return Embeddings()
