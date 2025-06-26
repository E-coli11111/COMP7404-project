from pydantic import BaseModel, Field
from typing import List

class ChatBreakdownResult(BaseModel):
    """
    Represents the breakdown of a chat message.
    """
    steps: List[str]