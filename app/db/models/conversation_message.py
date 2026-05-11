
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy                    import DateTime, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm                import Mapped, mapped_column

from app.db.base import Base


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sender_id:  Mapped[str]      = mapped_column(Text,     nullable=False)
    role:       Mapped[str]      = mapped_column(Text,     nullable=False)   # "user" | "assistant"
    content:    Mapped[str]      = mapped_column(Text,     nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        # Fast lookup for a sender's history ordered by time
        Index("ix_conversation_sender_time", "sender_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage sender={self.sender_id!r} role={self.role!r}>"
