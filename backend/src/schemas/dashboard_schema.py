
from pydantic import BaseModel, Field
from typing import Optional

class StatsResponse(BaseModel):
    query_count: int
    document_count: int

