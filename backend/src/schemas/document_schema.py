import enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class DocumentGroupResponse(BaseModel):
    id: str
    name: str
    description: str
    color: str
    created_at: str
    documents: Optional[List[Dict[str, Any]]] = None
