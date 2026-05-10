
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class OrderOut(BaseModel):
    order_id:     str
    sender_id:    str
    product_name: str
    quantity:     int
    status:       str
    created_at:   str
    contact_info: Dict[str, Any] = {}
    notes:        str = ""


class OrderStatusUpdate(BaseModel):
    status:       str              # "confirmed" | "processing" | "shipped" | "cancelled"
    contact_info: Optional[Dict[str, Any]] = None
    notes:        str = ""


class OrderListResponse(BaseModel):
    total:  int
    orders: List[OrderOut]
