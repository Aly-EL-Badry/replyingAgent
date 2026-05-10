from __future__ import annotations

from datetime import datetime

from sqlalchemy                    import DateTime, Index, Text, func
from sqlalchemy.orm                import Mapped, mapped_column

from app.db.base import Base


class TicketRow(Base):
    __tablename__ = "tickets"

    ticket_id:     Mapped[str]      = mapped_column(Text, primary_key=True)
    sender_id:     Mapped[str]      = mapped_column(Text, nullable=False)
    comment_text:  Mapped[str]      = mapped_column(Text, nullable=False)
    feedback_type: Mapped[str]      = mapped_column(Text, nullable=False)
    language:      Mapped[str]      = mapped_column(Text, nullable=False, default="en")
    status:        Mapped[str]      = mapped_column(Text, nullable=False, default="open")
    notes:         Mapped[str]      = mapped_column(Text, nullable=False, default="")
    created_at:    Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_tickets_sender_status", "sender_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<TicketRow id={self.ticket_id!r} status={self.status!r}>"
