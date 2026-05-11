"""
app/graph/nodes/classifier.py
------------------------------
Node: classifier_node

Calls ClassifierGenerator.classify() to determine the fine-grained intent
and detected language. Derives the high-level classification (public/private)
from the intent and writes all three fields into state.
"""
from __future__ import annotations

from app.graph.state import CommentState
from app.services.generator import classifier_generator
from app.services.generator.generators.classifier_generator import intent_to_classification


async def classifier_node(state: CommentState) -> dict:
    intent, language = await classifier_generator.classify(state.text)
    classification   = intent_to_classification(intent)

    print(
        f"[classifier_node] comment={state.comment_id} "
        f"intent={intent} classification={classification} lang={language}"
    )

    return {
        "intent":         intent,
        "classification": classification,
        "language":       language,
    }
