"""Runs the real pgvector SQL. Needs TEST_DATABASE_URL pointing at a disposable database."""
import math
import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from src.config import settings
from src.crud import document_crud
from src.db.models import ChunkEmbedding, Document, DocumentGroup, Page, User

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not set"),
]


def unit_vector(*weights: float) -> list[float]:
    vector = [0.0] * settings.EMBEDDING_DIMENSION
    vector[:len(weights)] = weights
    norm = math.sqrt(sum(w * w for w in vector))
    return [w / norm for w in vector]


@pytest.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(SQLModel.metadata.create_all)

    # Each test runs inside a transaction that is rolled back, so tests leave no rows behind.
    async with engine.connect() as conn:
        transaction = await conn.begin()
        async with AsyncSession(bind=conn, expire_on_commit=False) as db_session:
            yield db_session
        await transaction.rollback()
    await engine.dispose()


async def make_user(session: AsyncSession, name: str) -> User:
    user = User(email=f"{name}-{uuid.uuid4()}@example.com", password_hash="x", name=name, role="user",
                created_at="2026-01-01 00:00:00")
    session.add(user)
    await session.flush()
    return user


async def seed_document(session: AsyncSession, owner: User, chunks: dict[str, list[float]]) -> Document:
    group = DocumentGroup(name="filings", description="", color="#000000", created_at="2026-01-01 00:00:00",
                          user_id=owner.id)
    session.add(group)
    await session.flush()

    document = Document(filename=f"{owner.name}-10k.pdf", created_at="2026-01-02 00:00:00", user_id=owner.id,
                        document_group_id=group.id)
    session.add(document)
    await session.flush()

    page = Page(page_number=7, text=" ".join(chunks), sentence_count=len(chunks), document_id=document.id)
    session.add(page)
    await session.flush()

    session.add_all([ChunkEmbedding(chunk_text=chunk, embedding=vector, page_id=page.id) for chunk, vector in chunks.items()])
    await session.flush()
    return document


async def test_search_returns_cosine_similarity_best_first(session):
    ada = await make_user(session, "ada")
    document = await seed_document(session, ada, {
        "orthogonal": unit_vector(0, 1),
        "exact": unit_vector(1),
        "partial": unit_vector(1, 1),
    })

    rows = await document_crud.search_similar_chunks(session, unit_vector(1), [document.id], top_k=3)

    assert [row["chunk_text"] for row in rows] == ["exact", "partial", "orthogonal"]
    assert [round(row["similarity_score"], 4) for row in rows] == [1.0, 0.7071, 0.0]
    assert (rows[0]["document_name"], rows[0]["page_number"]) == (document.filename, 7)


async def test_resolve_document_ids_only_returns_the_users_documents(session):
    ada, eve = await make_user(session, "ada"), await make_user(session, "eve")
    ada_doc = await seed_document(session, ada, {"ada chunk": unit_vector(1)})
    eve_doc = await seed_document(session, eve, {"eve chunk": unit_vector(1)})

    assert await document_crud.resolve_document_ids(session, ada.id, [ada_doc.id, eve_doc.id], []) == [ada_doc.id]
    assert await document_crud.resolve_document_ids(session, ada.id, [], [eve_doc.document_group_id]) == []
    assert await document_crud.resolve_document_ids(session, ada.id, [], [ada_doc.document_group_id]) == [ada_doc.id]
    assert await document_crud.resolve_document_ids(session, ada.id, [], []) == []


async def test_vector_store_stats_are_per_user(session):
    ada, eve = await make_user(session, "ada"), await make_user(session, "eve")
    await seed_document(session, ada, {"one": unit_vector(1), "two": unit_vector(0, 1)})
    await seed_document(session, eve, {"three": unit_vector(1)})

    stats = await document_crud.get_vector_store_stats(session, ada.id)

    assert (stats.documents, stats.pages, stats.chunks) == (1, 1, 2)
    assert stats.embedding_bytes > 0
    assert stats.last_updated == "2026-01-02 00:00:00"


async def test_delete_documents_removes_pages_and_embeddings(session):
    ada = await make_user(session, "ada")
    document = await seed_document(session, ada, {"one": unit_vector(1), "two": unit_vector(0, 1)})

    await document_crud.delete_documents(session, [document.id])

    remaining = await session.execute(text("""
        SELECT (SELECT count(*) FROM documents WHERE id = :id),
               (SELECT count(*) FROM pages WHERE document_id = :id),
               (SELECT count(*) FROM chunk_embeddings ce JOIN pages p ON p.id = ce.page_id WHERE p.document_id = :id)
    """), {"id": document.id})
    assert remaining.one() == (0, 0, 0)
