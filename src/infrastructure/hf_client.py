"""
src/ai/hf_client.py
-------------------
Modular Hugging Face Inference API client.

Usage
-----
    from src.ai.hf_client import HFClient
    client = HFClient()                    # uses settings singleton
    reply = await client.generate(prompt)
"""
from __future__ import annotations

import httpx
from config.config import Settings, settings as _default_settings


class HFClient:
    """
    Thin async wrapper around the Hugging Face Inference API
    (text-generation task).

    Parameters
    ----------
    cfg:
        Optional Settings override – useful for testing.
        Defaults to the project-wide settings singleton.
    """

    def __init__(self, cfg: Settings | None = None) -> None:
        self._cfg = cfg or _default_settings
        hf = self._cfg.huggingface

        self._url = f"{hf.api_base_url}/{hf.model_id}"
        self._headers = {
            "Authorization": f"Bearer {self._cfg.hf_token}",
            "Content-Type": "application/json",
        }
        self._params = {
            "max_new_tokens": hf.max_new_tokens,
            "temperature": hf.temperature,
            "top_p": hf.top_p,
            "repetition_penalty": hf.repetition_penalty,
            "return_full_text": False,
        }
        self._timeout = hf.request_timeout

    async def generate(self, prompt: str) -> str:
        """
        Send *prompt* to HF inference and return the generated text.

        Raises
        ------
        httpx.HTTPStatusError
            When the API returns a non-2xx status.
        ValueError
            When the response JSON is in an unexpected shape.
        """
        payload = {
            "inputs": prompt,
            "parameters": self._params,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._url,
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()

        data = response.json()

        # HF text-generation returns: [{"generated_text": "..."}]
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()

        raise ValueError(f"Unexpected HF response shape: {data}")


# Module-level client – one instance shared across all requests
hf_client = HFClient()