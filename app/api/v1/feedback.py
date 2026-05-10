from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.services.data.feedback_service import feedback_service
from app.core.serializers.feedback      import FeedbackOut, FeedbackListResponse

router = APIRouter(prefix="/feedbacks", tags=["Feedbacks"])


@router.get("/", response_model=FeedbackListResponse)
async def list_feedbacks(
    sender_id: Optional[str] = None,
    limit: int = 100,
) -> FeedbackListResponse:
    """List all positive feedbacks, optionally filtered by sender_id."""
    if sender_id:
        feedbacks = await feedback_service.get_by_sender(sender_id)
    else:
        feedbacks = await feedback_service.list_all(limit=limit)
    return FeedbackListResponse(
        total     = len(feedbacks),
        feedbacks = [FeedbackOut(**asdict(f)) for f in feedbacks],
    )


@router.get("/{feedback_id}", response_model=FeedbackOut)
async def get_feedback(feedback_id: int) -> FeedbackOut:
    """Get a single feedback by its ID."""
    feedback = await feedback_service.get_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail=f"Feedback #{feedback_id} not found.")
    return FeedbackOut(**asdict(feedback))
