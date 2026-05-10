from __future__ import annotations

from app.graph.state import CommentState


async def no_reply_node(state: CommentState) -> dict:
    print(f"[no_reply_node] Skipping comment={state.comment_id} (no_reply intent)")
    return {}
