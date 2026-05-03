"""
app/graph/nodes/public_reply.py
--------------------------------
Node: public_reply_node

Generates an AI reply and posts it to the comment thread.
"""
from __future__ import annotations

from app.graph.nodes._helpers import post_thread_reply
from app.graph.state import CommentState
from app.services.generator import facebook_comment_generator


async def public_reply_node(state: CommentState) -> dict:
    reply_text = await facebook_comment_generator.generate(state.text)

    if state.sender_id:
        reply_text = f"@[{state.sender_id}] {reply_text}"

    await post_thread_reply(state.comment_id, reply_text)
    print(f"[public_reply_node] posted reply for comment={state.comment_id}")

    return {}
