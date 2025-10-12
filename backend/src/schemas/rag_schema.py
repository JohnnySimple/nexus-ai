
import enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Status(enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class DocumentIngestRequest(BaseModel):
    filename: str = Field(..., description="Name of the document")
    content: Optional[str] = Field(default=None, description="Text content of the document")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")

class DocumentIngestResponse(BaseModel):
    document_id: str = Field(..., description="ID of the ingested document")
    status: Status

class DocumentResponse(BaseModel):
    id: str
    filename: str
    content: str | List[dict]
    metadata: Dict[str, Any]
    created_at: str

class DocumentQueryRequest(BaseModel):
    query: str = Field(..., description="Query text")
    with_llm_response: bool = Field(default=False, description="Whether to include LLM response")
    top_k: int = Field(default=5, description="Number of results to return")
    filter_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")
    document_ids: List[str]

class QueryResults(BaseModel):
    document: Dict
    relevant_chunks: List[List[List]]

class DocumentQueryResponse(BaseModel):
    query: str
    results: List[QueryResults]
    context: str
    final_prompt: Optional[str] = None
    llm_response: Optional[str] = None
