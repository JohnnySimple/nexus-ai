import time
from dataclasses import dataclass
from typing import List

from sqlalchemy import delete, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.db.models import ChunkEmbedding, Document, DocumentGroup, Page, RagSetting


@dataclass
class VectorStoreStats:
    documents: int
    pages: int
    chunks: int
    embedding_bytes: int
    last_updated: str | None


def _pages_with_chunk_text():
    """Load pages and chunk text without pulling every embedding vector into memory."""
    return selectinload(Document.pages).selectinload(Page.embeddings).load_only(
        ChunkEmbedding.id, ChunkEmbedding.chunk_text, ChunkEmbedding.page_id
    )


async def create_document_group(session: AsyncSession, name: str, description: str, color: str, user_id: str) -> DocumentGroup:
    """Create a new document group in the database"""

    document_group = DocumentGroup(
        name=name,
        description=description,
        color=color,
        created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        user_id=user_id
    )
    session.add(document_group)
    await session.commit()
    await session.refresh(document_group)
    return document_group

async def get_document_group_by_id(session: AsyncSession, group_id: str, user_id: str) -> DocumentGroup | None:
    """Retrieve a document group owned by the user"""
    result = await session.execute(
        select(DocumentGroup)
        .where(DocumentGroup.id == group_id, DocumentGroup.user_id == user_id)
        .options(selectinload(DocumentGroup.documents))
    )
    return result.scalar_one_or_none()

async def get_all_document_groups_by_user_id(session: AsyncSession, user_id: str) -> List[DocumentGroup]:
    """Retrieve all document groups owned by the user"""
    result = await session.execute(
        select(DocumentGroup)
        .where(DocumentGroup.user_id == user_id)
        .options(selectinload(DocumentGroup.documents))
    )
    return result.scalars().all()

async def delete_document_group(session: AsyncSession, group_id: str) -> None:
    """Delete a group row. Delete its documents first with delete_documents; the caller commits."""
    await session.execute(delete(DocumentGroup).where(DocumentGroup.id == group_id))

async def create_document_with_pages_and_embeddings(session: AsyncSession, document: Document, pages: list[dict]) -> Document:
    """Create a document along with its pages and chunk embeddings"""
    session.add(document)

    for page in pages:
        current_page: Page = page["page"]
        current_page.document_id = document.id
        session.add(current_page)

        for embedding in page["embeddings"]:
            embedding.page_id = current_page.id
            session.add(embedding)

    await session.commit()
    return document

async def get_document_by_id(session: AsyncSession, document_id: str, user_id: str) -> Document | None:
    """Retrieve a document owned by the user, with pages and chunk text"""
    result = await session.execute(
        select(Document)
        .where(Document.id == document_id, Document.user_id == user_id)
        .options(_pages_with_chunk_text())
    )
    return result.scalar_one_or_none()

async def get_all_documents_by_user_id(session: AsyncSession, user_id: str) -> List[Document]:
    """Retrieve all documents owned by the user, with pages and chunk text"""
    result = await session.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .options(_pages_with_chunk_text())
    )
    return result.scalars().all()

async def resolve_document_ids(session: AsyncSession, user_id: str, document_ids: List[str], group_ids: List[str]) -> List[str]:
    """
    Expand the requested documents and groups into document ids the user owns.
    Ids belonging to other users are silently dropped.
    """
    conditions = []
    if document_ids:
        conditions.append(Document.id.in_(document_ids))
    if group_ids:
        conditions.append(Document.document_group_id.in_(group_ids))
    if not conditions:
        return []

    result = await session.execute(
        select(Document.id).where(Document.user_id == user_id, or_(*conditions))
    )
    return list(result.scalars().all())

async def delete_documents(session: AsyncSession, document_ids: List[str]) -> None:
    """
    Delete documents with their pages and embeddings using bulk statements.
    The foreign keys have no ON DELETE CASCADE, so children go first. The caller commits.
    """
    if not document_ids:
        return

    page_ids = select(Page.id).where(Page.document_id.in_(document_ids))
    await session.execute(delete(ChunkEmbedding).where(ChunkEmbedding.page_id.in_(page_ids)))
    await session.execute(delete(Page).where(Page.document_id.in_(document_ids)))
    await session.execute(delete(RagSetting).where(RagSetting.document_id.in_(document_ids)))
    await session.execute(delete(Document).where(Document.id.in_(document_ids)))

async def get_vector_store_stats(session: AsyncSession, user_id: str) -> VectorStoreStats:
    """Aggregate document, page and embedding counts plus on-disk vector size for a user"""
    sql = text("""
        SELECT count(DISTINCT d.id) AS documents,
               count(DISTINCT p.id) AS pages,
               count(ce.id) AS chunks,
               coalesce(sum(pg_column_size(ce.embedding)), 0) AS embedding_bytes,
               max(d.created_at) AS last_updated
        FROM documents d
        LEFT JOIN pages p ON p.document_id = d.id
        LEFT JOIN chunk_embeddings ce ON ce.page_id = p.id
        WHERE d.user_id = :user_id
    """)
    row = (await session.execute(sql, {"user_id": user_id})).mappings().one()
    return VectorStoreStats(
        documents=row["documents"],
        pages=row["pages"],
        chunks=row["chunks"],
        embedding_bytes=int(row["embedding_bytes"]),
        last_updated=row["last_updated"],
    )

async def search_similar_chunks(session: AsyncSession, embedding: list[float], document_ids: List[str], top_k: int = 5) -> List[dict]:
    """
    Nearest chunks to the embedding within the given documents, closest first.
    pgvector's <=> is cosine distance, so similarity_score = 1 - distance (higher is better).
    """
    sql = text("""
        SELECT ce.id,
               ce.chunk_text,
               p.page_number,
               d.id AS document_id,
               d.filename AS document_name,
               1 - (ce.embedding <=> CAST(:embedding AS vector)) AS similarity_score
        FROM chunk_embeddings ce
        JOIN pages p ON p.id = ce.page_id
        JOIN documents d ON d.id = p.document_id
        WHERE d.id = ANY(:document_ids)
        ORDER BY ce.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)
    result = await session.execute(
        sql, {"embedding": to_pgvector(embedding), "document_ids": list(document_ids), "top_k": top_k}
    )
    return [dict(row) for row in result.mappings().all()]

def to_pgvector(embedding: List[float]) -> str:
    """Convert a list of floats to PostgreSQL vector format"""
    return "[" + ','.join(str(v) for v in embedding) + "]"
