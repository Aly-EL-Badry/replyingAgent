
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
