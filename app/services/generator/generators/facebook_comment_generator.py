"""
app/services/generator/facebook_comment_generator.py
------------------------------------------------------
Concrete reply generator for Facebook post comments.

Reads the system prompt from the YAML config (config/prompt.yaml → constants.reply.system_prompt)
and formats the user message as a Facebook comment context.

Usage
-----
    from app.services.generator.facebook_comment_generator import facebook_comment_generator

    reply_text = await facebook_comment_generator.generate(comment_text)
"""
from __future__ import annotations

from app.core.settings_constant import constants
from app.infrastructure.hf_client import HFClient

from ..base_generator import BaseReplyGenerator


class FacebookCommentGenerator(BaseReplyGenerator):
    def __init__(self, client: HFClient | None = None) -> None:
        super().__init__(
            system_prompt=constants.reply.system_prompt,
            client=client,
        )


facebook_comment_generator = FacebookCommentGenerator()
