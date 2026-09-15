from pydantic import BaseModel, Field
from typing import Optional

class QuerySessionCreateRequest(BaseModel):
    query: str
    response: str
    model: str
    top_k: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    chunk_size: Optional[int] = Field(default=None)
    chunk_overlap: Optional[int] = Field(default=None)
    retrieved_chunks: list[dict] = Field(default_factory=list)
    response_time: Optional[float] = Field(default=None)
    user_id: str
    conversation_id: Optional[str] = Field(default=None)
    document_ids: list[str] = Field(default_factory=list)
