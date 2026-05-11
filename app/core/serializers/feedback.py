from pydantic import BaseModel
from typing import List


class FeedbackOut(BaseModel):
    id:          int
    sender_id:   str
    comment_id:  str
    text:        str
    language:    str
    created_at:  str


class FeedbackListResponse(BaseModel):
    total:     int
    feedbacks: List[FeedbackOut]
