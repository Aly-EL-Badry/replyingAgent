from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FeedbackRow(Base):
    __tablename__ = "feedbacks"

    id:          Mapped[int]      = mapped_column(primary_key=True, autoincrement=True)
    sender_id:   Mapped[str]      = mapped_column(Text, nullable=False)
    comment_id:  Mapped[str]      = mapped_column(Text, nullable=False, unique=True)
    text:        Mapped[str]      = mapped_column(Text, nullable=False)
    language:    Mapped[str]      = mapped_column(Text, nullable=False, default="en")
    created_at:  Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_feedbacks_sender", "sender_id"),
    )

    def __repr__(self) -> str:
        return f"<FeedbackRow id={self.id} sender={self.sender_id!r}>"
