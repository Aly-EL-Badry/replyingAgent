"""
app/services/generator/generators/private_reply_generator.py
-------------------------------------------------------------
Concrete reply generator for sensitive / private Facebook comments.

Uses the private_reply system prompt from config/classifierPrompt.yaml
to generate a helpful, professional DM reply for queries about pricing,
deals, partnerships, and other commercially sensitive topics.

Usage
-----
    from app.services.generator import private_reply_generator

    reply_text = await private_reply_generator.generate("How much does it cost?")
"""
from __future__ import annotations

from app.core.settings_constant import constants
from app.infrastructure.hf_client import HFClient

from ..base_generator import BaseReplyGenerator


class PrivateReplyGenerator(BaseReplyGenerator):
    """Generates a private Messenger reply for sensitive comment inquiries."""

    def __init__(self, client: HFClient | None = None) -> None:
        super().__init__(
            system_prompt=constants.private_reply.system_prompt,
            client=client,
        )


private_reply_generator = PrivateReplyGenerator()
