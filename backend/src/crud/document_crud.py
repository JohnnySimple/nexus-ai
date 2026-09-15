from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy import text
from src.db.models import DocumentGroup, Document, Page, ChunkEmbedding

from typing import List
import time


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

async def get_document_group_by_id(session: AsyncSession, group_id: str) -> DocumentGroup | None:
    """Retrieve a document group by its ID"""
    result = await session.execute(select(DocumentGroup).where(DocumentGroup.id == group_id).options(
        selectinload(DocumentGroup.documents)
    ))
    document_group = result.scalar_one_or_none()
    return document_group

async def get_all_document_groups_by_user_id(session: AsyncSession, user_id) -> List[DocumentGroup]:
    """Retrieve all document groups from the database"""
    result = await session.execute(select(DocumentGroup)
    .where(DocumentGroup.user_id == user_id)
    .options(
        selectinload(DocumentGroup.documents)
    ))
    document_groups = result.scalars().all()
    return document_groups

async def create_document(session: AsyncSession, document: Document) -> Document:
    """Create a new document in the database"""
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document

async def create_page(session: AsyncSession, page: Page) -> Page:
    """Create a new page in the database"""
    session.add(page)
    await session.commit()
    await session.refresh(page)
    return page

async def create_document_with_pages_and_embeddings(session: AsyncSession, document: Document, pages: dict) -> Document:
    """Create a document along with its pages and chunk embeddings"""

    # List[Page]
    # chunk_embeddings: List[ChunkEmbedding]

    session.add(document)

    for page in pages:
        current_page: List[Page] = page["page"]
        current_page.document_id = document.id
        session.add(current_page)

        for embedding in page["embeddings"]:
            embedding.page_id = current_page.id
            session.add(embedding)
        
    await session.commit()
    await session.refresh(document)

    return document

async def get_document_by_id(session: AsyncSession, document_id: str) -> Document | None:
    """Retrieve a document by its ID"""
    result = await session.execute(select(Document).where(Document.id == document_id).options(
        selectinload(Document.pages).selectinload(Page.embeddings)
    ))
    document = result.scalar_one_or_none()
    return document

async def get_documents_by_ids(session: AsyncSession, document_ids: List[str]) -> List[Document]:
    """Retrieve documents by ids"""
    result = await session.execute(select(Document).where(Document.id.in_(document_ids)).options(
        selectinload(Document.pages).selectinload(Page.embeddings)
    ))
    documents = result.scalars().all()
    return documents

async def get_document_ids_by_group_ids(session: AsyncSession, group_ids: List[str]) -> List[Document]:
    """Retrieve documents by group ids"""
    result = await session.execute(select(Document.id).where(Document.document_group_id.in_(group_ids)))
    document_ids = result.scalars().all()
    return document_ids

async def get_all_documents_by_user_id(session: AsyncSession, user_id: str) -> List[Document]:
    """Retrieve all documents from the database"""
    result = await session.execute(select(Document)
    .where(Document.user_id == user_id)
    .options(
        selectinload(Document.pages).selectinload(Page.embeddings)
    ))
    documents = result.scalars().all()
    return documents

async def get_total_documents_by_user_id(session: AsyncSession, user_id: str) -> int:
    """Retrieve total documents by user id"""
    results = await session.execute(select(func.count()).select_from(Document).where(Document.user_id == user_id))
    return results.scalar_one()

async def search_similar_chunks(session: AsyncSession, embedding: list[float], page_ids: list, top_k: int = 5) -> List[ChunkEmbedding]:
    """Search for similar chunks based on embedding"""
    sql = text("""
        SELECT id,
               chunk_text,
               page_id,
               embedding <=> :embedding AS distance
        FROM chunk_embeddings ce
        WHERE ce.page_id = ANY(:page_ids)
        ORDER BY ce.embedding <=> :embedding 
        LIMIT :top_k
    """)
    result = await session.execute(sql, {"embedding": to_pgvector(embedding), "page_ids": page_ids, "top_k": top_k})
    return result.mappings().all()
    # similar_chunks = result.fetchall()
    # return [row[0] for row in similar_chunks]

def to_pgvector(embedding: List[float]) -> str:
    """Convert a list of floats to PostgreSQL vector format"""
    return "[" + ','.join(str(v) for v in embedding) + "]"