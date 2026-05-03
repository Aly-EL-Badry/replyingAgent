"""
app/features/comments/service.py
---------------------------------
Orchestrates the smart reply cycle for Facebook post comments:
  1. Ingest & parse webhook payload         (ingestion.py)
  2. Run the LangGraph comment pipeline     (app/graph)

The graph handles classification and routing internally.
"""
from __future__ import annotations

from fastapi import BackgroundTasks
from langchain_core.runnables import RunnableConfig

from app.graph import comment_graph
from app.graph.state import CommentState
from .ingestion import ingest_data


async def reply(data: dict, backgroundTasks: BackgroundTasks) -> None:
    """Entry point called by the webhook route handler."""
    events = ingest_data(data)
    for comment_id, comment_text, sender_id in events:
        backgroundTasks.add_task(
            process_cycle, comment_id, comment_text, sender_id,
        )


async def process_cycle(
    comment_id: str,
    text: str,
    sender_id: str,
) -> None:
    """Background task: runs the comment through the LangGraph pipeline."""
    try:
        config: RunnableConfig = {"configurable": {"thread_id": comment_id}}
        initial_state = CommentState(
            comment_id=comment_id,
            text=text,
            sender_id=sender_id,
        )
        await comment_graph.graph.ainvoke(initial_state, config=config) 
    except Exception as exc:
        print(f"[service] Failed to process comment {comment_id}: {exc}")
