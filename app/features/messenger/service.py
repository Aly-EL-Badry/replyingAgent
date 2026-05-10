from __future__ import annotations

from fastapi import BackgroundTasks

from app.services.messenger_agent import messenger_agent
from .ingestion import ingest_data


async def reply(data: dict, background_tasks: BackgroundTasks) -> None:
    events = ingest_data(data)
    for sender_psid, message_text in events:
        background_tasks.add_task(process_cycle, sender_psid, message_text)


async def process_cycle(sender_psid: str, text: str) -> None:
    try:
        await messenger_agent.process(sender_psid, text)
    except Exception as exc:
        print(f"[messenger/service] Failed to process message from {sender_psid}: {exc}")
