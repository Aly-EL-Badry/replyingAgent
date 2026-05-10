"""
app/graph/nodes/public/product_availability.py
------------------------------------------------
Node: product_availability_node

Handles two intents:
  - "product_availability": Is this product in stock?
  - "shipping_cost":        What are the shipping/delivery costs?

Both paths query the structured catalog (via ProductService / CatalogService).
No RAG is used here — availability data comes from the demo catalog only.
"""
from __future__ import annotations

from app.graph.nodes._helpers    import post_thread_reply
from app.graph.state             import CommentState
from app.services.data.product_service import product_service


# Static shipping reply — replace with a real ShippingService when ready
_SHIPPING_REPLY_EN = (
    "🚚 We offer nationwide delivery! Shipping costs vary by location — "
    "please DM us or contact support for an exact quote for your area."
)
_SHIPPING_REPLY_AR = (
    "🚚 نوفر التوصيل لجميع أنحاء المملكة! تتفاوت تكاليف الشحن حسب موقعك — "
    "تواصل معنا عبر الرسائل الخاصة أو الدعم للحصول على سعر دقيق."
)


async def product_availability_node(state: CommentState) -> dict:
    intent   = state.intent or "product_availability"
    language = state.language or "en"

    if intent == "shipping_cost":
        reply_text = _SHIPPING_REPLY_AR if language == "ar" else _SHIPPING_REPLY_EN
    else:
        status     = await product_service.check_availability(state.text)
        reply_text = product_service.format_availability_reply(status, language)

    if state.sender_id:
        reply_text = f"@[{state.sender_id}] {reply_text}"

    await post_thread_reply(state.comment_id, reply_text)
    print(f"[product_availability_node] intent={intent} replied to comment={state.comment_id}")

    return {}
