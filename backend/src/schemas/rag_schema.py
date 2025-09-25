
import enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Status(enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class DocumentIngestRequest(BaseModel):
    filename: str = Field(..., description="Name of the document")
    content: str = Field(..., description="Text content of the document")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")

class DocumentIngestResponse(BaseModel):
    document_id: str = Field(..., description="ID of the ingested document")
    status: Status

class DocumentListResponse(BaseModel):
    id: str
    filename: str
    content: str | List[dict]
    metadata: Dict[str, Any]
    created_at: str