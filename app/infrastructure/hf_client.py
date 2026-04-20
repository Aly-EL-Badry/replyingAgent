"""
src/infrastructure/hf_client.py
-------------------------------
Modular Hugging Face Inference client using the official huggingface_hub library.

Usage
-----
    from src.infrastructure.hf_client import HFClient
    client = HFClient()                    # uses settings singleton
    reply = await client.generate(messages)
"""
from __future__ import annotations

import asyncio
from huggingface_hub import InferenceClient
from config.config import Settings, settings as _default_settings


class HFClient:
    """
    Async wrapper around ``huggingface_hub.InferenceClient``
    for chat-completion tasks.

    The library automatically picks the best available provider
    for the requested model – no manual URL wrangling needed.

    Parameters
    ----------
    cfg:
        Optional Settings override – useful for testing.
        Defaults to the project-wide settings singleton.
    """

    def __init__(self, cfg: Settings | None = None) -> None:
        self._cfg = cfg or _default_settings
        hf = self._cfg.huggingface

        self._primary_model = hf.model_id
        self._fallback_model = hf.fallback_model_id

        self._client = InferenceClient(
            provider="auto",
            api_key=self._cfg.hf_token,
        )

        self._gen_params = {
            "max_tokens": hf.max_new_tokens,
            "temperature": hf.temperature,
            "top_p": hf.top_p,
        }

    async def generate(self, messages: list[dict[str, str]]) -> str:
        """
        Send *messages* to HF inference and return the generated text.

        Tries the primary model first; if that fails, falls back to
        the secondary model.

        Raises
        ------
        Exception
            When both primary and fallback models fail.
        """
        try:
            return await self._call(self._primary_model, messages)
        except Exception as primary_err:
            print(
                f"Primary model {self._primary_model} failed: {primary_err}. "
                f"Falling back to {self._fallback_model}."
            )
            try:
                return await self._call(self._fallback_model, messages)
            except Exception as fallback_err:
                raise RuntimeError(
                    f"Both models failed.\n"
                    f"  Primary ({self._primary_model}): {primary_err}\n"
                    f"  Fallback ({self._fallback_model}): {fallback_err}"
                ) from fallback_err

    async def _call(
        self, model: str, messages: list[dict[str, str]]
    ) -> str:
        """Run a single chat-completion request in a thread (sync → async)."""
        response = await asyncio.to_thread(
            self._client.chat_completion,
            model=model,
            messages=messages,
            **self._gen_params,
        )
        return response.choices[0].message.content.strip()


# Module-level client – one instance shared across all requests
hf_client = HFClient()