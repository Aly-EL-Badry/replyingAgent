"""
app/services/generator/base_generator.py
-----------------------------------------
Abstract base class for all AI reply generators.

To add a new service (e.g. Messenger, Ads), create a subclass that:
  1. Passes its own system_prompt to super().__init__()
  2. Implements _format_user_message() to wrap the raw input text

The shared generate() pipeline is inherited and must NOT be overridden.

Example
-------
    class MessengerReplyGenerator(BaseReplyGenerator):
        def __init__(self):
            super().__init__(system_prompt=constants.messenger.system_prompt)

        def _format_user_message(self, text: str) -> str:
            return f"Message: {text}"
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.infrastructure.hf_client import HFClient, hf_client


class BaseReplyGenerator(ABC):
    def __init__(self, system_prompt: str, client: HFClient | None = None) -> None:
        self._system_prompt = system_prompt
        self._client: HFClient = client or hf_client

    def _format_user_message(self, user_input: str) -> str:
        return user_input

    async def generate(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user",   "content": self._format_user_message(user_input)},
        ]
        return await self._client.generate(messages)