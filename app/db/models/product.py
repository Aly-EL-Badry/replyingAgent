from __future__ import annotations

from datetime import datetime

from sqlalchemy                    import ARRAY, DateTime, Integer, Numeric, Text, func
from sqlalchemy.orm                import Mapped, mapped_column

from app.db.base import Base


class ProductRow(Base):
    __tablename__ = "products"

    id:                Mapped[str]           = mapped_column(Text,    primary_key=True)
    name:              Mapped[str]           = mapped_column(Text,    nullable=False)
    name_ar:           Mapped[str | None]    = mapped_column(Text,    nullable=True)
    category:          Mapped[str]           = mapped_column(Text,    nullable=False, index=True)
    description:       Mapped[str]           = mapped_column(Text,    nullable=False, default="")
    price:             Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False)
    currency:          Mapped[str]           = mapped_column(Text,    nullable=False, default="EGP")
    stock_status:      Mapped[str]           = mapped_column(Text,    nullable=False)   # StockStatus value
    stock_qty:         Mapped[int | None]    = mapped_column(Integer, nullable=True)
    tags:              Mapped[list | None]   = mapped_column(ARRAY(Text), nullable=True, default=list)
    estimated_restock: Mapped[str | None]   = mapped_column(Text,    nullable=True)
    created_at:        Mapped[datetime]      = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at:        Mapped[datetime]      = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ProductRow id={self.id!r} name={self.name!r} status={self.stock_status!r}>"
