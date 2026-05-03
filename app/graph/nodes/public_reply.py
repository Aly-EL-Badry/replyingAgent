"""
app/graph/nodes/public_reply.py
--------------------------------
Node: public_reply_node

Generates an AI reply and posts it to the comment thread.
Mirrors the 'public' branch of the original process_cycle.
"""
from __future__ import annotations
import asyncio
from app.graph.state import CommentState
from app.infrastructure.facebook_client import facebook_client
from app.services.generator import facebook_comment_generator


async def public_reply_node(state: CommentState) -> dict:
    reply_text = await facebook_comment_generator.generate(state.text)

    if state.sender_id:
        reply_text = f"@[{state.sender_id}] {reply_text}"

    await asyncio.sleep(20)
    await facebook_client.post_reply(state.comment_id, reply_text)
    print(f"[public_reply_node] posted reply for comment={state.comment_id}")

    return {}
