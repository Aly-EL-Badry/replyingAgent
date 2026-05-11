"""
app/services/generator/generators/classifier_generator.py
----------------------------------------------------------
LLM-based comment intent classifier.

Sends the comment text to the LLM with a structured JSON-output prompt and
parses the result into an (intent, language) tuple.

Valid intents
-------------
Public  : policy_query | product_availability | shipping_cost | complaint | no_reply
Private : bad_feedback | make_order | product_details

Usage
-----
    from app.services.generator import classifier_generator

    intent, lang = await classifier_generator.classify("Do you have product X in stock?")
    # → ("product_availability", "en")
"""
from __future__ import annotations

import json
import re

from app.core.settings_constant import constants
from app.infrastructure.hf_client import HFClient

from ..base_generator import BaseReplyGenerator


PUBLIC_INTENTS: frozenset[str] = frozenset({
    "policy_query",
    "product_availability",
    "shipping_cost",
    "positive_feedback",
    "no_reply",
})
PRIVATE_INTENTS: frozenset[str] = frozenset({
    "bad_feedback",
    "make_order",
    "product_details",
})
VALID_INTENTS: frozenset[str] = PUBLIC_INTENTS | PRIVATE_INTENTS

_FALLBACK_INTENT    = "no_reply"
_FALLBACK_LANGUAGE  = "en"

_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)


def intent_to_classification(intent: str) -> str:
    return "private" if intent in PRIVATE_INTENTS else "public"


class ClassifierGenerator(BaseReplyGenerator):
    def __init__(self, client: HFClient | None = None) -> None:
        super().__init__(
            system_prompt=constants.classifier.system_prompt,
            client=client,
        )

    async def classify(self, text: str) -> tuple[str, str]:
        raw = await self.generate(text)
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> tuple[str, str]:
        try:
            match = _JSON_RE.search(raw)
            if not match:
                raise ValueError("No JSON object found in LLM output")
            data = json.loads(match.group())

            intent   = str(data.get("intent",   _FALLBACK_INTENT)).strip().lower()
            language = str(data.get("language", _FALLBACK_LANGUAGE)).strip().lower()

            if intent not in VALID_INTENTS:
                print(f"[ClassifierGenerator] Unknown intent '{intent}' — defaulting to '{_FALLBACK_INTENT}'")
                intent = _FALLBACK_INTENT

            return intent, language

        except Exception as exc:
            print(
                f"[ClassifierGenerator] Parse error – defaulting to '{_FALLBACK_INTENT}'. "
                f"Raw: {raw!r} | Error: {exc}"
            )
            return _FALLBACK_INTENT, _FALLBACK_LANGUAGE


classifier_generator = ClassifierGenerator()
