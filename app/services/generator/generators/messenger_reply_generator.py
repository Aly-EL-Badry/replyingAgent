"""
app/services/generator/generators/messenger_reply_generator.py
---------------------------------------------------------------
Concrete reply generator for Facebook Messenger direct messages.

Reads the system prompt from the YAML config
(config/prompt.yaml → constants.messenger.system_prompt)
and formats the user message as a Messenger DM context.

Usage
-----
    from app.services.generator.generators.messenger_reply_generator import messenger_reply_generator

    reply_text = await messenger_reply_generator.generate(message_text)
"""
from __future__ import annotations

from app.core.settings_constant import constants
from app.infrastructure.hf_client import HFClient

from ..base_generator import BaseReplyGenerator


class MessengerReplyGenerator(BaseReplyGenerator):
    def __init__(self, client: HFClient | None = None) -> None:
        super().__init__(
            system_prompt=constants.messenger.system_prompt,
            client=client,
        )


messenger_reply_generator = MessengerReplyGenerator()
