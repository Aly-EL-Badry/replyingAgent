from __future__ import annotations

from app.core.settings_constant import constants
from app.graph.nodes._helpers import (
    PRIVATE_REPLY_STUBS,
    PRIVATE_REPLY_STUBS_DEFAULT,
    post_thread_reply,
)
from app.graph.state import CommentState
from app.infrastructure.facebook_client import facebook_client
from app.services.data.ticket_service import ticket_service


def _build_dm(ticket_id: str, language: str) -> str:
    if language == "ar":
        return (
            f"شكراً لتواصلك معنا 🙏\n\n"
            f"لقد تلقينا مشكلتك وأحطنا بها فريق الدعم للمتابعة.\n\n"
            f"🎫 رقم تذكرتك: *{ticket_id}*\n"
            f"سيتواصل معك أحد أعضاء الفريق قريباً.\n\n"
        )
    return (
        f"Thank you for reaching out 🙏\n\n"
        f"We've received your report and our support team has been notified.\n\n"
        f"🎫 Your ticket ID: *{ticket_id}*\n"
        f"A team member will follow up with you shortly.\n\n"
    )


async def bad_feedback_node(state: CommentState) -> dict:
    language = state.language or "en"

    stub = PRIVATE_REPLY_STUBS.get(language, PRIVATE_REPLY_STUBS_DEFAULT)
    await post_thread_reply(state.comment_id, stub)

    ticket = await ticket_service.create_ticket(
        sender_id    = state.sender_id,
        comment_text = state.text,
        language     = language,
        feedback_type= "bad_feedback",
    )

    if state.sender_id:
        dm_text = _build_dm(ticket.ticket_id, language)
        try:
            await facebook_client.send_messenger_message(state.sender_id, dm_text)
            print(f"[bad_feedback_node] DM sent → sender={state.sender_id} ticket={ticket.ticket_id}")
        except Exception as exc:
            print(f"[bad_feedback_node] DM failed for sender={state.sender_id}: {exc}")

    return {"ticket_id": ticket.ticket_id}
