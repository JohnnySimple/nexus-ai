from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from typing import Optional, List
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime, timezone

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str
    password_hash: str
    name: str
    role: str
    created_at: str

class DocumentGroup(SQLModel, table=True):
    __tablename__ = "document_groups"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: str
    color: str
    created_at: str
    documents: List["Document"] = Relationship(back_populates="document_group")

class Document(SQLModel, table=True):
    __tablename__ = "documents"

    # id: int | None = Field(default=None, primary_key=True)
    # content: list[dict]
    # metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    # embedding: list
    # chunks: list

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str
    created_at: str
    pages: List["Page"] = Relationship(back_populates="document")
    document_group_id: str = Field(foreign_key="document_groups.id")
    document_group: Optional[DocumentGroup] = Relationship(back_populates="documents")
    rag_settings: "RagSetting" = Relationship(back_populates="document")


class Page(SQLModel, table=True):
    __tablename__ = "pages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    page_number: int
    text: str
    sentence_count: int
    document_id: str = Field(foreign_key="documents.id")

    document: Optional[Document] = Relationship(back_populates="pages")
    embeddings: List["ChunkEmbedding"] = Relationship(back_populates="page")


class ChunkEmbedding(SQLModel, table=True):
    __tablename__ = "chunk_embeddings"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    chunk_text: str
    embedding: list[float] = Field(sa_column=Column(Vector(384)))
    page_id: str = Field(foreign_key="pages.id")

    page: Optional[Page] = Relationship(back_populates="embeddings")


class RagSetting(SQLModel, table=True):
    __tablename__ = "rag_settings"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    top_k: int
    temperature: int
    chunk_size: int
    chunk_overlap: int
    rerank: bool
    document_id: str = Field(foreign_key="documents.id")
    document: Optional[Document] = Relationship(back_populates="rag_settings")