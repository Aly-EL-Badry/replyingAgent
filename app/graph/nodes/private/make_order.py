"""
app/graph/nodes/make_order.py
-------------------------------
Node: make_order_node

Handles "make_order" intent.

Phase A (this node — triggered by comment):
  1. Post a private stub on the comment thread.
  2. Check product availability via ProductService.
  3a. If out of stock → DM the user with unavailability info and stop.
  3b. If in stock → Create a pending order record.
       → DM the user a confirmation request (asking for CONFIRM + address + phone).

Phase B (handled by MessengerAgent when user replies "CONFIRM"):
  The Messenger agent detects a pending order for this sender and finalises it.
"""
from __future__ import annotations

import re

from app.core.settings_constant import constants
from app.graph.nodes._helpers import (
    PRIVATE_REPLY_STUBS,
    PRIVATE_REPLY_STUBS_DEFAULT,
    post_thread_reply,
)
from app.graph.state import CommentState
from app.infrastructure.facebook_client import facebook_client
from app.services.data.order_service import order_service
from app.services.data.product_service import product_service


# ── Product name extraction helpers ──────────────────────────────────────────
_ORDER_KEYWORDS = re.compile(
    r"\b(?:i want|i'd like|order|buy|purchase|get me|أريد|اطلب|شراء)\b",
    re.IGNORECASE,
)


def _extract_product(text: str) -> str:
    """Best-effort product name extraction from the comment text."""
    # Strip common order-intent phrases to leave just the product name
    cleaned = _ORDER_KEYWORDS.sub("", text).strip(" .,!?")
    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or text


def _build_confirm_dm(
    order_id: str, product_name: str, language: str
) -> str:
    base_url  = constants.agent.base_url

    if language == "ar":
        return (
            f"مرحباً! 😊 لقد تلقينا طلبك.\n\n"
            f"📦 المنتج: *{product_name}*\n"
            f"🔢 رقم الطلب المؤقت: *{order_id}*\n\n"
            f"لتأكيد طلبك، يُرجى الرد بكلمة *تأكيد* أو *Confirm*."
        )
    return (
        f"Hi! 😊 We've received your order request.\n\n"
        f"📦 Product: *{product_name}*\n"
        f"🔢 Pending order ID: *{order_id}*\n\n"
        f"To confirm your order, please reply with *Confirm*."
    )


def _build_unavailable_dm(product_name: str, language: str) -> str:
    if language == "ar":
        return (
            f"عذراً 😔 المنتج '{product_name}' غير متوفر حالياً.\n"
            f"سنُعلمك فور توفره. شكراً لتواصلك معنا!"
        )
    return (
        f"Sorry 😔 '{product_name}' is currently out of stock.\n"
        f"We'll notify you as soon as it becomes available. Thank you!"
    )


async def make_order_node(state: CommentState) -> dict:
    language     = state.language or "en"
    product_name = _extract_product(state.text)

    # 1. Post private stub on thread
    stub = PRIVATE_REPLY_STUBS.get(language, PRIVATE_REPLY_STUBS_DEFAULT)
    await post_thread_reply(state.comment_id, stub)

    # 2. Check availability
    status = await product_service.check_availability(product_name)


    if not status.in_stock:
        dm_text = _build_unavailable_dm(product_name, language)
        try:
            await facebook_client.send_messenger_message(state.sender_id, dm_text)
        except Exception as exc:
            print(f"[make_order_node] DM failed: {exc}")
        return {}


    order = await order_service.create_order(
        sender_id    = state.sender_id,
        product_name = product_name,
        quantity     = 1,
        status       = "pending_confirmation",
    )

    dm_text = _build_confirm_dm(order.order_id, product_name, language)
    try:
        await facebook_client.send_messenger_message(state.sender_id, dm_text)
        print(
            f"[make_order_node] Pending order {order.order_id} created; "
            f"confirmation DM sent to sender={state.sender_id}"
        )
    except Exception as exc:
        print(f"[make_order_node] DM failed: {exc}")

    return {"order_id": order.order_id, "collected_data": {"product_name": product_name}}
