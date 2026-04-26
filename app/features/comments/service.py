"""
app/features/comments/service.py
---------------------------------
Orchestrates the smart reply cycle for Facebook post comments:
  1. Ingest & parse webhook payload         (ingestion.py)
  2. Classify the comment as public/private  (ClassifierGenerator)
  3a. PUBLIC  → generate AI reply → post on comment thread
  3b. PRIVATE → post multilingual stub on thread
              → generate detailed reply → send via Messenger DM
"""
from __future__ import annotations

import asyncio

from fastapi import BackgroundTasks

from app.infrastructure.facebook_client import facebook_client
from app.services.generator import (
    facebook_comment_generator,
    classifier_generator,
    private_reply_generator,
)

from .ingestion import ingest_data

# ---------------------------------------------------------------------------
# Multilingual private-stub lookup
# ---------------------------------------------------------------------------
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


def _private_stub(lang: str) -> str:
    """Return the language-appropriate private-reply stub."""
    return _PRIVATE_STUBS.get(lang.lower(), _DEFAULT_STUB)



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
    """Background task: classify then route to public or private reply flow."""
    try:
        classification, lang = await classifier_generator.classify(text)
        print(f"[service] comment={comment_id} classification={classification} lang={lang}")

        if classification == "public":
            reply_text = await facebook_comment_generator.generate(text)
            if sender_id:
                reply_text = f"@[{sender_id}] {reply_text}"
            await asyncio.sleep(20)
            await facebook_client.post_reply(comment_id, reply_text)

        else:
            stub = _private_stub(lang)
            await asyncio.sleep(20)
            await facebook_client.post_reply(comment_id, stub)


            if sender_id:
                private_text = await private_reply_generator.generate(text)
                try:
                    await facebook_client.send_messenger_message(sender_id, private_text)
                except Exception as dm_exc:
                    print(
                        f"[service] DM failed for sender={sender_id} "
                        f"(PSID may not be available): {dm_exc}"
                    )
            else:
                print(f"[service] No sender_id for comment={comment_id}; skipping DM.")

    except Exception as exc:
        print(f"[service] Failed to process comment {comment_id}: {exc}")
