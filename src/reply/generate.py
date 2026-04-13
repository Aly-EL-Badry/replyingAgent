"""
src/reply/generate.py
---------------------
generate_reply(comment_text) → str

Builds the prompt and calls HFClient to produce a reply for a
Facebook comment.
"""
from __future__ import annotations

from config.config import settings
from src.ai.hf_client import hf_client



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
    prompt = _build_prompt(comment_text)
    return await hf_client.generate(prompt)


def _build_prompt(comment_text: str) -> str:
    """Format the final prompt using the system prompt from config."""
    system = settings.reply.system_prompt
    return (
        f"<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n"
        f"Comment: {comment_text} [/INST]"
    )
