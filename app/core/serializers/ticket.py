from pydantic import BaseModel
from typing import List

class TicketOut(BaseModel):
    ticket_id:     str
    sender_id:     str
    comment_text:  str
    feedback_type: str
    language:      str
    status:        str
    created_at:    str
    notes:         str = ""


class TicketStatusUpdate(BaseModel):
    status: str   # "open" | "in_review" | "resolved"
    notes:  str   = ""


class TicketListResponse(BaseModel):
    total:   int
    tickets: List[TicketOut]
