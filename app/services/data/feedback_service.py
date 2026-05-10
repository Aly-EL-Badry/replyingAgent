from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from app.db        import async_session_factory
from app.db.models import FeedbackRow


@dataclass
class FeedbackRecord:
    id:          int
    sender_id:   str
    comment_id:  str
    text:        str
    language:    str
    created_at:  str


def _row_to_record(row: FeedbackRow) -> FeedbackRecord:
    return FeedbackRecord(
        id         = row.id,
        sender_id  = row.sender_id,
        comment_id = row.comment_id,
        text       = row.text,
        language   = row.language,
        created_at = row.created_at.isoformat() if isinstance(row.created_at, datetime) else str(row.created_at),
    )


class FeedbackService:
    """CRUD for positive feedback stored in PostgreSQL."""

    async def store(
        self,
        sender_id:  str,
        comment_id: str,
        text:       str,
        language:   str = "en",
    ) -> FeedbackRecord:
        row = FeedbackRow(
            sender_id  = sender_id,
            comment_id = comment_id,
            text       = text,
            language   = language,
        )
        async with async_session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        print(f"[FeedbackService] Stored feedback #{row.id} from sender={sender_id}")
        return _row_to_record(row)

    async def list_all(self, limit: int = 100) -> List[FeedbackRecord]:
        async with async_session_factory() as session:
            stmt = select(FeedbackRow).order_by(FeedbackRow.created_at.desc()).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
        return [_row_to_record(r) for r in rows]

    async def get_by_id(self, feedback_id: int) -> Optional[FeedbackRecord]:
        async with async_session_factory() as session:
            row = await session.get(FeedbackRow, feedback_id)
        return _row_to_record(row) if row else None

    async def get_by_sender(self, sender_id: str) -> List[FeedbackRecord]:
        async with async_session_factory() as session:
            stmt = (
                select(FeedbackRow)
                .where(FeedbackRow.sender_id == sender_id)
                .order_by(FeedbackRow.created_at.desc())
            )
            rows = (await session.execute(stmt)).scalars().all()
        return [_row_to_record(r) for r in rows]


feedback_service = FeedbackService()
