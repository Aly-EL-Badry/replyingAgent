"""
app/graph/nodes/_helpers.py
----------------------------
Shared utilities for graph nodes.

Centralises the reply-delay + Facebook post pattern that both
public_reply_node and private_reply_node use, so it lives in
exactly one place.
"""
from __future__ import annotations

import asyncio

from app.infrastructure.facebook_client import facebook_client

# Seconds to wait before posting a reply (avoids instant-bot feel).
REPLY_DELAY_SECONDS: int = 20

# Multilingual stub messages for private replies posted on the public thread.
PRIVATE_REPLY_STUBS: dict[str, str] = {
    "ar": "تم الرد بشكل خاص",
    "en": "Replied privately",
    "fr": "Répondu en privé",
    "es": "Respondido en privado",
    "de": "Privat beantwortet",
    "it": "Risposto privatamente",
    "pt": "Respondido em privado",
    "tr": "Özel olarak yanıtlandı",
}
PRIVATE_REPLY_STUBS_DEFAULT = "Replied privately"


async def post_thread_reply(comment_id: str, reply_text: str) -> None:
    """Wait REPLY_DELAY_SECONDS then post a reply to a Facebook comment thread."""
    await asyncio.sleep(REPLY_DELAY_SECONDS)
    await facebook_client.post_reply(comment_id, reply_text)
