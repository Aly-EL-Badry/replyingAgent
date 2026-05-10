from __future__ import annotations

from app.graph.nodes._helpers import post_thread_reply
from app.graph.state import CommentState
from app.services.generator import facebook_comment_generator
from app.services.data.feedback_service import feedback_service

_THANKS_STUBS: dict[str, str] = {
    "en": "Thank you so much for the kind words! 🙏 We're thrilled you're happy with us!",
    "ar": "شكراً جزيلاً على كلماتك الطيبة! 🙏 يسعدنا أنك راضٍ عن خدمتنا!",
    "fr": "Merci infiniment pour ces gentils mots! 🙏 Nous sommes ravis de vous compter parmi nous!",
    "es": "¡Muchas gracias por tus amables palabras! 🙏 ¡Nos alegra mucho que estés satisfecho!",
    "de": "Vielen Dank für die netten Worte! 🙏 Wir freuen uns sehr, dass du zufrieden bist!",
    "tr": "Güzel sözleriniz için çok teşekkürler! 🙏 Memnuniyetiniz bizim için her şeyden önemli!",
}
_THANKS_DEFAULT = _THANKS_STUBS["en"]


async def positive_feedback_node(state: CommentState) -> dict:
    language = state.language or "en"

    # Store the positive feedback in PostgreSQL
    await feedback_service.store(
        sender_id  = state.sender_id,
        comment_id = state.comment_id,
        text       = state.text,
        language   = language,
    )

    try:
        reply_text = await facebook_comment_generator.generate(
            f"[Positive feedback from user — respond warmly and genuinely]\n{state.text}"
        )
    except Exception as exc:
        print(f"[positive_feedback_node] LLM failed, using stub. Error: {exc}")
        reply_text = _THANKS_STUBS.get(language, _THANKS_DEFAULT)

    if state.sender_id:
        reply_text = f"@[{state.sender_id}] {reply_text}"

    await post_thread_reply(state.comment_id, reply_text)
    print(f"[positive_feedback_node] Stored + replied for comment={state.comment_id}")

    return {}
