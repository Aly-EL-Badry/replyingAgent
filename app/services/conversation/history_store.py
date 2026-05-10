
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import delete, select

from app.db                        import async_session_factory, ConversationMessage
from app.core.settings_secrets     import secrets
from .schemas                      import ConversationMessage as ConversationMessageSchema


class HistoryStore:
    """Async PostgreSQL conversation history manager."""

    async def get_history(self, sender_id: str, limit: int = 20) -> List[dict]:
        """
        Return up to *limit* most-recent messages from the last
        conv_ttl_hours hours as {role, content} dicts.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=secrets.conv_ttl_hours)

        async with async_session_factory() as session:
            stmt = (
                select(ConversationMessage.role, ConversationMessage.content)
                .where(
                    ConversationMessage.sender_id == sender_id,
                    ConversationMessage.created_at >= cutoff,
                )
                .order_by(ConversationMessage.created_at.asc())
                .limit(limit)
            )
            rows = (await session.execute(stmt)).all()

        return [{"role": r.role, "content": r.content} for r in rows]

    async def append(self, sender_id: str, role: str, content: str) -> None:
        """Append a single message to the conversation history."""
        async with async_session_factory() as session:
            session.add(ConversationMessage(
                sender_id = sender_id,
                role      = role,
                content   = content,
            ))
            await session.commit()

    async def clear(self, sender_id: str) -> None:
        """Delete the entire conversation history for a sender."""
        async with async_session_factory() as session:
            await session.execute(
                delete(ConversationMessage)
                .where(ConversationMessage.sender_id == sender_id)
            )
            await session.commit()


history_store = HistoryStore()
