from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from sqlalchemy import func, or_, select

from app.db        import async_session_factory
from app.db.models import ProductRow


class StockStatus(str, Enum):
    IN_STOCK     = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LIMITED      = "limited"
    PRE_ORDER    = "pre_order"


_AVAILABLE = {StockStatus.IN_STOCK.value, StockStatus.LIMITED.value, StockStatus.PRE_ORDER.value}


@dataclass
class ProductStatus:
    query:             str
    exists:            bool = False
    in_stock:          bool = False
    price_hint:        str  = ""
    estimated_restock: str  = ""
    notes:             str  = ""


class ProductService:
    """Availability and full-detail queries against the `products` table."""

    # ── internal ──────────────────────────────────────────────────────────────

    async def _find_best_match(self, query: str) -> Optional[ProductRow]:
        terms = query.lower().split()
        if not terms:
            return None
        async with async_session_factory() as session:
            conditions = [
                or_(
                    func.lower(ProductRow.name).contains(term),
                    func.lower(ProductRow.name_ar).contains(term),
                    func.lower(ProductRow.description).contains(term),
                    func.lower(ProductRow.category).contains(term),
                )
                for term in terms
            ]
            stmt = select(ProductRow).where(or_(*conditions)).limit(1)
            return (await session.execute(stmt)).scalar_one_or_none()

    # ── public API ─────────────────────────────────────────────────────────────

    async def find_product(self, query: str) -> Optional[ProductRow]:
        """Return the raw ProductRow best matching *query*, or None."""
        return await self._find_best_match(query)

    async def check_availability(self, query: str) -> ProductStatus:
        row = await self._find_best_match(query)
        if row is None:
            return ProductStatus(query=query, exists=False, in_stock=False,
                                 notes="Product not found in catalog.")
        return ProductStatus(
            query             = row.name,
            exists            = True,
            in_stock          = row.stock_status in _AVAILABLE,
            price_hint        = f"{float(row.price):,.0f} {row.currency}",
            estimated_restock = row.estimated_restock or "",
            notes             = f"status={row.stock_status}",
        )

    def get_details_dm(self, row: ProductRow, language: str = "en") -> str:
        """
        Build a rich bilingual product-details DM directly from a DB row.
        No LLM, no RAG — all data comes from the `products` table.
        """
        _STOCK: dict[str, tuple[str, str]] = {
            "in_stock":     ("✅ In Stock",       "✅ متوفر"),
            "limited":      ("⚠️ Limited Stock",  "⚠️ كمية محدودة"),
            "pre_order":    ("📦 Pre-Order",       "📦 طلب مسبق"),
            "out_of_stock": ("❌ Out of Stock",    "❌ غير متوفر"),
        }
        stock_en, stock_ar = _STOCK.get(row.stock_status, ("—", "—"))
        ar = language == "ar"

        qty = (
            (f"\n• {'الكمية المتاحة' if ar else 'Units available'}: {row.stock_qty}")
            if row.stock_qty is not None else ""
        )
        restock = (
            (f"\n• {'إعادة التوفر' if ar else 'Restock'}: {row.estimated_restock}")
            if row.estimated_restock else ""
        )
        tags = (
            (f"\n• {'الفئات' if ar else 'Tags'}: {', '.join(row.tags)}")
            if row.tags else ""
        )
        sep = "─" * 30

        if ar:
            return (
                f"📋 تفاصيل المنتج\n{sep}\n"
                f"🏷️ الاسم: {row.name_ar or row.name}\n"
                f"📂 الفئة: {row.category}\n"
                f"📝 الوصف: {row.description}\n"
                f"💰 السعر: {float(row.price):,.0f} {row.currency}\n"
                f"📦 الحالة: {stock_ar}{qty}{restock}{tags}\n"
                f"{sep}\n"
                f"للطلب أو الاستفسار تواصل معنا مباشرةً 🙌"
            )

        return (
            f"📋 Product Details\n{sep}\n"
            f"🏷️ Name: {row.name}\n"
            f"📂 Category: {row.category}\n"
            f"📝 Description: {row.description}\n"
            f"💰 Price: {float(row.price):,.0f} {row.currency}\n"
            f"📦 Status: {stock_en}{qty}{restock}{tags}\n"
            f"{sep}\n"
            f"To order or ask more questions, just reply here 🙌"
        )

    def format_availability_reply(self, status: ProductStatus, language: str = "en") -> str:
        if not status.exists:
            if language == "ar":
                return f"عذراً، لم نتمكن من إيجاد '{status.query}' في كتالوجنا. تواصل معنا للمزيد."
            return (f"Sorry, we couldn't find '{status.query}' in our catalog. "
                    "Please contact us for more details.")

        price_note = f" — {status.price_hint}" if status.price_hint else ""

        if status.in_stock:
            if language == "ar":
                return f"✅ نعم! '{status.query}' متوفر لدينا حالياً{price_note}. تواصل معنا لإتمام الطلب."
            return (f"✅ Great news! '{status.query}' is currently available{price_note}. "
                    "Contact us to place your order!")

        restock = f" {status.estimated_restock}" if status.estimated_restock else ""
        if language == "ar":
            return f"❌ '{status.query}' غير متوفر حالياً.{restock} سنُعلمك فور توفره."
        return (f"❌ '{status.query}' is currently out of stock.{restock} "
                "We'll notify you as soon as it's back!")


product_service = ProductService()
