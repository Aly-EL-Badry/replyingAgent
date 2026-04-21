"""
app/features/reply/service.py
------------------------------
Orchestrates the reply cycle for Facebook post comments:
  1. Ingest & parse webhook payload  (ingestion.py)
  2. Generate an AI reply            (generator package)
  3. Post the reply back to Facebook (FacebookClient)
"""
from __future__ import annotations

import asyncio

from fastapi import BackgroundTasks

from app.infrastructure.facebook_client import facebook_client
from app.services.generator import facebook_comment_generator

from .ingestion import ingest_data


async def reply(data: dict, backgroundTasks: BackgroundTasks) -> None:
    """Entry point called by the webhook route handler."""
    events = ingest_data(data)
    for comment_id, comment_text, sender_id, sender_name in events:
        backgroundTasks.add_task(
            process_cycle, comment_id, comment_text, sender_id, sender_name 
        )


async def process_cycle(
    comment_id: str,
    text: str,
    sender_id: str,
    sender_name: str,
) -> None:
    """Background task: generate a reply and post it to Facebook."""
    try:
        reply_text = await facebook_comment_generator.generate(text)
        if sender_id:
            reply_text = f"@[{sender_id}] {reply_text}"
        await asyncio.sleep(20)
        await facebook_client.post_reply(comment_id, reply_text)
    except Exception as exc:
        print(f"Failed to process comment {comment_id}: {exc}")
