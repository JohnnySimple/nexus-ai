"""add foreign key indexes

Revision ID: a1c4e7d2b9f0
Revises: 96c314f16bae
Create Date: 2026-09-14 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1c4e7d2b9f0'
down_revision: Union[str, None] = '96c314f16bae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Retrieval joins chunk_embeddings -> pages -> documents and every query filters by user_id.
INDEXES = [
    ("document_groups", "user_id"),
    ("documents", "user_id"),
    ("documents", "document_group_id"),
    ("pages", "document_id"),
    ("chunk_embeddings", "page_id"),
    ("query_sessions", "user_id"),
]


def upgrade() -> None:
    for table, column in INDEXES:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column], unique=False)


def downgrade() -> None:
    for table, column in reversed(INDEXES):
        op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
