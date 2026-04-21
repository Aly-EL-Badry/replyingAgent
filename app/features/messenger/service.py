"""
app/features/messenger/service.py
----------------------------------
Orchestrates the reply cycle for Facebook Messenger direct messages:
  1. Ingest & parse webhook payload  (ingestion.py)
  2. Generate an AI reply            (generator package)
  3. Send the reply back via Messenger (FacebookClient.send_messenger_message)
"""
from __future__ import annotations

from fastapi import BackgroundTasks

from app.infrastructure.facebook_client import facebook_client
from app.services.generator import messenger_reply_generator

from .ingestion import ingest_data


async def reply(data: dict, background_tasks: BackgroundTasks) -> None:
    """Entry point called by the Messenger webhook route handler."""
    events = ingest_data(data)
    for sender_psid, message_text in events:
        background_tasks.add_task(process_cycle, sender_psid, message_text)


async def process_cycle(sender_psid: str, text: str) -> None:
    """Background task: generate a reply and send it via Messenger."""
    try:
        reply_text = await messenger_reply_generator.generate(text)
        await facebook_client.send_messenger_message(sender_psid, reply_text)
    except Exception as exc:
        print(f"Failed to process Messenger message from {sender_psid}: {exc}")
