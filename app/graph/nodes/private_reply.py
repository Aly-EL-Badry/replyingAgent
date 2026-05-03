"""
app/graph/nodes/private_reply.py
---------------------------------
Node: private_reply_node

Posts a multilingual stub on the comment thread, then sends a
detailed DM via Messenger.
"""
from __future__ import annotations

from app.graph.nodes._helpers import (
    PRIVATE_REPLY_STUBS,
    PRIVATE_REPLY_STUBS_DEFAULT,
    post_thread_reply,
)
from app.graph.state import CommentState
from app.infrastructure.facebook_client import facebook_client
from app.services.generator import private_reply_generator


async def private_reply_node(state: CommentState) -> dict:
    stub = PRIVATE_REPLY_STUBS.get(state.language or "en", PRIVATE_REPLY_STUBS_DEFAULT)

    await post_thread_reply(state.comment_id, stub)

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
