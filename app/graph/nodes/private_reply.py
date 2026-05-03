"""
app/graph/nodes/private_reply.py
---------------------------------
Node: private_reply_node

Posts a multilingual stub on the comment thread then sends a
detailed DM via Messenger. Mirrors the 'private' branch of the
original process_cycle.
"""
from __future__ import annotations
import asyncio
from app.graph.state import CommentState
from app.infrastructure.facebook_client import facebook_client
from app.services.generator import private_reply_generator

_PRIVATE_STUBS: dict[str, str] = {
    "ar": "تم الرد بشكل خاص ",
    "en": "Replied privately",
    "fr": "Répondu en privé",
    "es": "Respondido en privado",
    "de": "Privat beantwortet",
    "it": "Risposto privatamente",
    "pt": "Respondido em privado",
    "tr": "Özel olarak yanıtlandı",
}
_DEFAULT_STUB = "Replied privately"


async def private_reply_node(state: CommentState) -> dict:
    stub = _PRIVATE_STUBS.get(state.language or "en", _DEFAULT_STUB)

    await asyncio.sleep(20)
    await facebook_client.post_reply(state.comment_id, stub)

    if state.sender_id:
        private_text = await private_reply_generator.generate(state.text)
        try:
            await facebook_client.send_messenger_message(state.sender_id, private_text)
            print(f"[private_reply_node] DM sent to sender={state.sender_id}")
        except Exception as exc:
            print(f"[private_reply_node] DM failed for sender={state.sender_id}: {exc}")
    else:
        print(f"[private_reply_node] No sender_id for comment={state.comment_id}; skipping DM.")

    return {}
