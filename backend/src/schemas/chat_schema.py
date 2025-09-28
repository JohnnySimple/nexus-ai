
import enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class ChatMessage(BaseModel):
    role: str = Field(..., description="The role of the message author")
    content: str = Field(..., description="The content of the message")

class ChatRequest(BaseModel):
    model: str = Field(..., description="ID of the model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: bool = Field(default=False)
    functions: Optional[List[Dict[str, Any]]] = Field(default=None)
    function_call: Optional[Union[str, Dict[str, str]]] = Field(default=None)