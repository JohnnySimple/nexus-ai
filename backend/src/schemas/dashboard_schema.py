
from pydantic import BaseModel, Field
from typing import Optional

class StatsResponse(BaseModel):
    query_count: int
    document_count: int
    total_documents: int
    total_chunks: int
    total_embeddings: int
    total_pages: int
    dimensionality: int
    disk_usage_mb: float
    health_status: str
    last_updated: Optional[str] = None
