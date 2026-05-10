
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.services.data.ticket_service import ticket_service
from app.core.serializers.ticket import (
    TicketOut, TicketListResponse, TicketStatusUpdate,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])



@router.get("/", response_model=TicketListResponse)
async def list_tickets(status: Optional[str] = None) -> TicketListResponse:
    tickets = await ticket_service.list_tickets(status=status)
    return TicketListResponse(
        total   = len(tickets),
        tickets = [TicketOut(**asdict(t)) for t in tickets],
    )


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(ticket_id: str) -> TicketOut:
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return TicketOut(**asdict(ticket))


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(ticket_id: str, body: TicketStatusUpdate) -> TicketOut:
    valid_statuses = {"open", "in_review", "resolved"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{body.status}'. Must be one of: {sorted(valid_statuses)}",
        )
    updated = await ticket_service.update_status(ticket_id, body.status, body.notes)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return TicketOut(**asdict(updated))

