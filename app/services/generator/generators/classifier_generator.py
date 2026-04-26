"""
app/services/generator/generators/classifier_generator.py
----------------------------------------------------------
LLM-based comment classifier.

Sends the comment text to the LLM with a structured JSON-output prompt and
parses the result into a (classification, language) tuple.

Usage
-----
    from app.services.generator import classifier_generator

    classification, lang = await classifier_generator.classify("How much does it cost?")
    # → ("private", "en")
"""
from __future__ import annotations

import json
import re

from app.core.settings_constant import constants
from app.infrastructure.hf_client import HFClient

from ..base_generator import BaseReplyGenerator

_FALLBACK_CLASSIFICATION = "public"
_FALLBACK_LANGUAGE = "en"

# Regex to extract JSON even if the model wraps it in markdown fences
_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)


class ClassifierGenerator(BaseReplyGenerator):
    """
    Classifies a Facebook comment as 'public' or 'private' and detects its language.

    Returns
    -------
    tuple[str, str]
        ("public"|"private",  ISO-639-1 language code)
    """

    def __init__(self, client: HFClient | None = None) -> None:
        super().__init__(
            system_prompt=constants.classifier.classifier.system_prompt,
            client=client,
        )

    async def classify(self, text: str) -> tuple[str, str]:
        """
        Run classification and return (classification, language).
        Falls back to ("public", "en") on any parse failure.
        """
        raw = await self.generate(text)
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> tuple[str, str]:
        """Extract classification and language from the LLM JSON output."""
        try:
            match = _JSON_RE.search(raw)
            if not match:
                raise ValueError("No JSON object found in LLM output")
            data = json.loads(match.group())
            classification = data.get("classification", _FALLBACK_CLASSIFICATION).strip().lower()
            language = data.get("language", _FALLBACK_LANGUAGE).strip().lower()
            if classification not in ("public", "private"):
                classification = _FALLBACK_CLASSIFICATION
            return classification, language
        except Exception as exc:
            print(f"[ClassifierGenerator] Parse error – defaulting to public. Raw: {raw!r} | Error: {exc}")
            return _FALLBACK_CLASSIFICATION, _FALLBACK_LANGUAGE


classifier_generator = ClassifierGenerator()
