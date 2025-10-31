from pydantic import BaseModel, Field
from typing import Optional

class QuerySessionCreateRequest(BaseModel):
    query: str
    response: str
    model: str
    top_k: Optional[int]
    temperature: Optional[float]
    chunk_size: Optional[int]
    chunk_overlap: Optional[int]
    retrieved_chunks: str
    # created_at: str
    response_time: Optional[float]
    user_id: str
