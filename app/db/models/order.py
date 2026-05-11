from __future__ import annotations

from datetime import datetime

from sqlalchemy                    import DateTime, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm                import Mapped, mapped_column

from app.db.base import Base


class OrderRow(Base):
    __tablename__ = "orders"

    order_id:     Mapped[str]      = mapped_column(Text,    primary_key=True)
    sender_id:    Mapped[str]      = mapped_column(Text,    nullable=False)
    product_name: Mapped[str]      = mapped_column(Text,    nullable=False)
    quantity:     Mapped[int]      = mapped_column(Integer, nullable=False)
    status:       Mapped[str]      = mapped_column(Text,    nullable=False)
    contact_info: Mapped[dict]     = mapped_column(JSONB,   nullable=False, default=dict)
    notes:        Mapped[str]      = mapped_column(Text,    nullable=False, default="")
    created_at:   Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_orders_sender_status", "sender_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<OrderRow id={self.order_id!r} status={self.status!r}>"
