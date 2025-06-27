from pydantic import BaseModel, Field
from typing import List

class ChatBreakdownResult(BaseModel):
    """
    Represents the breakdown of a chat message.
    """
    steps: List[str]
    
class FaissTextModel(BaseModel):
    """
    Represents a Faiss text model with its ID and text.
    """
    id: int = Field(..., description="The unique identifier for the text.")
    text: str = Field(..., description="The text content associated with the ID.")