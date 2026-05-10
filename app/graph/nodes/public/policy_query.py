
from __future__ import annotations

from app.core.settings_constant import constants
from app.graph.nodes._helpers import post_thread_reply
from app.graph.state import CommentState
from app.services.generator import facebook_comment_generator
from app.services.rag import retrieve_context_as_string


async def policy_query_node(state: CommentState) -> dict:
    rag_context = await retrieve_context_as_string(
        state.text,
        top_k=constants.rag.top_k,
        min_score=constants.rag.min_score,
    )

    if rag_context:
        augmented = (
            f"Knowledge base context:\n{rag_context}\n\n"
            f"User question: {state.text}"
        )
    else:
        augmented = state.text   

    reply_text = await facebook_comment_generator.generate(augmented)

    if state.sender_id:
        reply_text = f"@[{state.sender_id}] {reply_text}"

    await post_thread_reply(state.comment_id, reply_text)
    print(f"[policy_query_node] replied to comment={state.comment_id} rag_hit={bool(rag_context)}")

    return {"rag_context": rag_context}
