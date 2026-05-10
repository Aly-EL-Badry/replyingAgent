"""
app/services/data/order_service.py
------------------------------------
Order management service backed by PostgreSQL.

Replaces the JSON-file backend (data/orders.json).
Same public async interface — graph nodes need no changes.

Order lifecycle: pending_confirmation → confirmed → processing → shipped | cancelled
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from app.core.settings_constant import constants
from app.db                     import async_session_factory, OrderRow


def _order_id() -> str:
    prefix = constants.agent.order_prefix
    uid    = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{uid}"


@dataclass
class OrderRecord:
    order_id:     str
    sender_id:    str
    product_name: str
    quantity:     int
    status:       str
    created_at:   str
    contact_info: Dict[str, Any]
    notes:        str = ""


def _row_to_record(row: OrderRow) -> OrderRecord:
    return OrderRecord(
        order_id     = row.order_id,
        sender_id    = row.sender_id,
        product_name = row.product_name,
        quantity     = row.quantity,
        status       = row.status,
        created_at   = row.created_at.isoformat() if isinstance(row.created_at, datetime) else str(row.created_at),
        contact_info = row.contact_info or {},
        notes        = row.notes or "",
    )


class OrderService:
    """Async CRUD operations for orders backed by PostgreSQL."""

    async def create_order(
        self,
        sender_id:    str,
        product_name: str,
        quantity:     int = 1,
        contact_info: Optional[Dict[str, Any]] = None,
        status:       str = "pending_confirmation",
    ) -> OrderRecord:
        row = OrderRow(
            order_id     = _order_id(),
            sender_id    = sender_id,
            product_name = product_name,
            quantity     = quantity,
            status       = status,
            contact_info = contact_info or {},
        )
        async with async_session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        print(f"[OrderService] Created {row.order_id} for sender={sender_id}")
        return _row_to_record(row)

    async def get_order(self, order_id: str) -> Optional[OrderRecord]:
        async with async_session_factory() as session:
            row = await session.get(OrderRow, order_id)
        return _row_to_record(row) if row else None

    async def get_pending_order_for_sender(self, sender_id: str) -> Optional[OrderRecord]:
        async with async_session_factory() as session:
            stmt = (
                select(OrderRow)
                .where(
                    OrderRow.sender_id == sender_id,
                    OrderRow.status    == "pending_confirmation",
                )
                .order_by(OrderRow.created_at.desc())
                .limit(1)
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
        return _row_to_record(row) if row else None

    async def list_orders(self, status: Optional[str] = None) -> List[OrderRecord]:
        async with async_session_factory() as session:
            stmt = select(OrderRow)
            if status:
                stmt = stmt.where(OrderRow.status == status)
            stmt = stmt.order_by(OrderRow.created_at.desc())
            rows = (await session.execute(stmt)).scalars().all()
        return [_row_to_record(r) for r in rows]

    async def update_order(
        self,
        order_id:     str,
        new_status:   str,
        contact_info: Optional[Dict[str, Any]] = None,
        notes:        str = "",
    ) -> Optional[OrderRecord]:
        async with async_session_factory() as session:
            row = await session.get(OrderRow, order_id)
            if row is None:
                return None
            row.status = new_status
            if contact_info:
                row.contact_info = {**(row.contact_info or {}), **contact_info}
            if notes:
                row.notes = notes
            await session.commit()
            await session.refresh(row)
        return _row_to_record(row)

    async def confirm_order(
        self, order_id: str, contact_info: Dict[str, Any]
    ) -> Optional[OrderRecord]:
        return await self.update_order(order_id, "confirmed", contact_info)


order_service = OrderService()
