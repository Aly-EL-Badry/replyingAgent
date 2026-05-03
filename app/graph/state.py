from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
from operator import add

class CommentState(BaseModel):
    comment_id: str
    sender_id: str
    text: str
    history: Annotated[List[dict], add] = Field(default_factory=list)
    
    classification: Optional[str] = None 

    language: Optional[str] = "en"
    next_node: Optional[str] = None