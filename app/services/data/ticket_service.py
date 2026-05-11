"""
app/services/data/ticket_service.py
-------------------------------------
Feedback ticket service backed by PostgreSQL.

Replaces the JSON-file backend (data/tickets.json).
Same public async interface — graph nodes need no changes.

Ticket lifecycle: open → in_review → resolved
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from app.core.settings_constant import constants
from app.db                     import async_session_factory, TicketRow


def _ticket_id() -> str:
    prefix = constants.agent.ticket_prefix
    uid    = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{uid}"


@dataclass
class FeedbackTicket:
    ticket_id:     str
    sender_id:     str
    comment_text:  str
    feedback_type: str
    language:      str
    status:        str
    created_at:    str
    notes:         str = ""


def _row_to_ticket(row: TicketRow) -> FeedbackTicket:
    return FeedbackTicket(
        ticket_id     = row.ticket_id,
        sender_id     = row.sender_id,
        comment_text  = row.comment_text,
        feedback_type = row.feedback_type,
        language      = row.language,
        status        = row.status,
        created_at    = row.created_at.isoformat() if isinstance(row.created_at, datetime) else str(row.created_at),
        notes         = row.notes or "",
    )


class TicketService:
    """Async CRUD operations for feedback tickets backed by PostgreSQL."""

    async def create_ticket(
        self,
        sender_id:     str,
        comment_text:  str,
        language:      str = "en",
        feedback_type: str = "bad_feedback",
    ) -> FeedbackTicket:
        row = TicketRow(
            ticket_id     = _ticket_id(),
            sender_id     = sender_id,
            comment_text  = comment_text,
            feedback_type = feedback_type,
            language      = language,
            status        = "open",
        )
        async with async_session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        print(f"[TicketService] Created {row.ticket_id} for sender={sender_id}")
        return _row_to_ticket(row)

    async def get_ticket(self, ticket_id: str) -> Optional[FeedbackTicket]:
        async with async_session_factory() as session:
            row = await session.get(TicketRow, ticket_id)
        return _row_to_ticket(row) if row else None

    async def list_tickets(self, status: Optional[str] = None) -> List[FeedbackTicket]:
        async with async_session_factory() as session:
            stmt = select(TicketRow)
            if status:
                stmt = stmt.where(TicketRow.status == status)
            stmt = stmt.order_by(TicketRow.created_at.desc())
            rows = (await session.execute(stmt)).scalars().all()
        return [_row_to_ticket(r) for r in rows]

    async def update_status(
        self, ticket_id: str, new_status: str, notes: str = ""
    ) -> Optional[FeedbackTicket]:
        async with async_session_factory() as session:
            row = await session.get(TicketRow, ticket_id)
            if row is None:
                return None
            row.status = new_status
            if notes:
                row.notes = notes
            await session.commit()
            await session.refresh(row)
        return _row_to_ticket(row)


ticket_service = TicketService()
