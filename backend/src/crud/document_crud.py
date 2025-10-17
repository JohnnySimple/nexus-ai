from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.db.models import Document, Page, ChunkEmbedding

from typing import List


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