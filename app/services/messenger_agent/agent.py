from __future__ import annotations

import re
from typing import Any

from app.core.settings_constant import constants
from app.infrastructure.facebook_client import facebook_client
from app.infrastructure.hf_client import hf_client
from app.services.conversation.history_store import history_store
from app.services.data.order_service import order_service
from app.services.data.product_service import product_service
from app.services.data.ticket_service import ticket_service
from app.services.data.feedback_service import feedback_service
from app.services.generator import classifier_generator
from app.services.rag import retrieve_context_as_string


_SYSTEM_PROMPT = constants.messenger_agent.system_prompt

def _build_ask_details_dm(product_name: str, language: str) -> str:
    if language == "ar":
        return (
            f"✅ رائع! سنكمل طلبك لـ *{product_name}*.\n\n"
            f"يُرجى إرسال بياناتك بهذا الشكل:\n"
            f"الاسم: [اسمك الكامل]\n"
            f"الهاتف: [رقم هاتفك]"
        )
    return (
        f"✅ Great! Let's complete your order for *{product_name}*.\n\n"
        f"Please send your details in this format:\n"
        f"Name: [Your full name]\n"
        f"Phone: [Your phone number]"
    )

def _build_order_confirmed_dm(order_id: str, language: str) -> str:
    base_url  = constants.agent.base_url
    order_url = f"{base_url}/api/v1/agent/orders/{order_id}"

    if language == "ar":
        return (
            f"🎉 تم تأكيد طلبك بنجاح!\n\n"
            f"📦 رقم الطلب: *{order_id}*\n"
            f"سيتواصل معك فريقنا لترتيب التوصيل.\n\n"
            f"تفاصيل الطلب:\n{order_url}"
        )
    return (
        f"🎉 Your order has been confirmed!\n\n"
        f"📦 Order ID: *{order_id}*\n"
        f"Our team will contact you to arrange delivery.\n\n"
        f"Order details:\n{order_url}"
    )


_NAME_RE  = re.compile(r"(?:name|اسم)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:phone|هاتف|tel|phone)[:\s]+([\d\s\+\-]+)", re.IGNORECASE)

def _parse_contact_details(text: str) -> dict:
    details = {}
    name_match  = _NAME_RE.search(text)
    phone_match = _PHONE_RE.search(text)
    if name_match:
        details["name"]  = name_match.group(1).strip()
    if phone_match:
        details["phone"] = phone_match.group(1).strip()
    return details


class MessengerAgent:
    """
    Intent-aware multi-turn Messenger agent.

    Each message is classified using the same classifier as the comment graph.
    Based on intent, side-effects are triggered (tickets, feedback storage,
    product context enrichment) before the LLM generates a conversational reply.
    """

    async def process(self, sender_psid: str, text: str) -> None:
        history_window = constants.agent.messenger_history_window
        history = await history_store.get_history(sender_psid, limit=history_window * 2)

        intent, language = await classifier_generator.classify(text)
        print(f"[MessengerAgent] sender={sender_psid} intent={intent} lang={language}")

        # ── Step 2: Order in pending_details → parse contact info and finalize ──────────
        pending_details_order = await order_service.get_pending_details_order_for_sender(sender_psid)
        if pending_details_order:
            contact_info = _parse_contact_details(text)
            if contact_info:
                confirmed = await order_service.confirm_order(pending_details_order.order_id, contact_info)
                if confirmed:
                    reply_text = _build_order_confirmed_dm(confirmed.order_id, language)
                    await history_store.append(sender_psid, "user",      text)
                    await history_store.append(sender_psid, "assistant", reply_text)
                    await facebook_client.send_messenger_message(sender_psid, reply_text)
                    print(f"[MessengerAgent] Order {confirmed.order_id} finalized for sender={sender_psid}")
                    return
            else:
                # Details not parsed — re-ask
                reply_text = _build_ask_details_dm(pending_details_order.product_name, language)
                await facebook_client.send_messenger_message(sender_psid, reply_text)
                return

        # ── Step 1: User confirms intent → move order to pending_details, ask for info ──
        if intent == "confirm_order":
            pending_order = await order_service.get_pending_order_for_sender(sender_psid)
            if pending_order:
                await order_service.move_to_pending_details(pending_order.order_id)
                reply_text = _build_ask_details_dm(pending_order.product_name, language)
                await history_store.append(sender_psid, "user",      text)
                await history_store.append(sender_psid, "assistant", reply_text)
                await facebook_client.send_messenger_message(sender_psid, reply_text)
                print(f"[MessengerAgent] Order {pending_order.order_id} moved to pending_details")
                return

        extra_context = ""

        if intent == "positive_feedback":
            await feedback_service.store(
                sender_id=sender_psid, comment_id=f"dm-{sender_psid}",
                text=text, language=language,
            )

        elif intent == "bad_feedback":
            ticket = await ticket_service.create_ticket(
                sender_id=sender_psid, comment_text=text,
                language=language, feedback_type="bad_feedback",
            )
            extra_context = (
                f"\n\n--- Support Ticket Created ---\n"
                f"Ticket ID: {ticket.ticket_id}\n"
                f"Tell the user their ticket has been created and a human agent will follow up."
            )

        elif intent in ("product_availability", "product_details", "make_order"):
            row = await product_service.find_product(text)
            if row:
                extra_context = (
                    f"\n\n--- Product Data ---\n"
                    f"{product_service.get_details_dm(row, language)}"
                )

        elif intent == "shipping_cost":
            extra_context = (
                "\n\n--- Shipping Info ---\n"
                "We offer nationwide delivery. Shipping costs vary by location. "
                "Guide the user to contact support or DM for an exact quote."
            )

        rag_context = await retrieve_context_as_string(
            text,
            top_k=constants.rag.top_k,
            min_score=constants.rag.min_score,
        )

        system_content = _SYSTEM_PROMPT
        if rag_context:
            system_content += f"\n\n--- Knowledge Base Context ---\n{rag_context}"
        if extra_context:
            system_content += extra_context

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content},
            *history,
            {"role": "user",   "content": text},
        ]

        reply_text = await hf_client.generate(messages)

        await history_store.append(sender_psid, "user",      text)
        await history_store.append(sender_psid, "assistant", reply_text)

        await facebook_client.send_messenger_message(sender_psid, reply_text)
        print(f"[MessengerAgent] Replied to sender={sender_psid} intent={intent} rag_hit={bool(rag_context)}")


messenger_agent = MessengerAgent()
