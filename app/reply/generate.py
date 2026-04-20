"""
src/reply/generate.py
---------------------
generate_reply(comment_text) → str

Builds the prompt and calls HFClient to produce a reply for a
Facebook comment.
"""
from __future__ import annotations

from config.config import settings
from src.infrastructure.hf_client import hf_client



async def generate_reply(comment_text: str) -> str:
    """
    Generate an AI reply for a Facebook comment.

    Parameters
    ----------
    comment_text:
        Raw text of the Facebook comment.

    Returns
    -------
    str
        The generated reply text.
    """
    messages = _build_messages(comment_text)
    return await hf_client.generate(messages)


def _build_messages(comment_text: str) -> list[dict[str, str]]:
    """Build a chat-completions messages list from the system prompt + comment."""
    system = settings.reply.system_prompt
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Comment: {comment_text}"},
    ]
