
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException


from app.services.data.order_service  import order_service
from app.core.serializers.order import (  
    OrderOut,  OrderListResponse,  OrderStatusUpdate,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(status: Optional[str] = None) -> OrderListResponse:
    orders = await order_service.list_orders(status=status)
    return OrderListResponse(
        total  = len(orders),
        orders = [OrderOut(**asdict(o)) for o in orders],
    )


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: str) -> OrderOut:
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")
    return OrderOut(**asdict(order))


@router.patch("/orders/{order_id}", response_model=OrderOut)
async def update_order(order_id: str, body: OrderStatusUpdate) -> OrderOut:
    valid_statuses = {"pending_confirmation", "confirmed", "processing", "shipped", "cancelled"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{body.status}'. Must be one of: {sorted(valid_statuses)}",
        )
    updated = await order_service.update_order(
        order_id     = order_id,
        new_status   = body.status,
        contact_info = body.contact_info,
        notes        = body.notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")
    return OrderOut(**asdict(updated))
