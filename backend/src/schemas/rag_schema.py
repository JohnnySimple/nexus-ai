import enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Status(enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class DocumentIngestResponse(BaseModel):
    document_id: str = Field(..., description="ID of the ingested document")
    status: Status

class DocumentResponse(BaseModel):
    id: str
    filename: str
    content: List[dict]
    metadata: Dict[str, Any]
    created_at: str

class DocumentQueryRequest(BaseModel):
    query: str = Field(..., description="Query text")
    with_llm_response: bool = Field(default=False, description="Whether to include LLM response")
    stream: bool = Field(default=False, description="Whether to stream the response")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of chunks to retrieve")
    document_ids: List[str] = Field(default_factory=list)
    document_group_ids: List[str] = Field(default_factory=list)
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation to continue")
