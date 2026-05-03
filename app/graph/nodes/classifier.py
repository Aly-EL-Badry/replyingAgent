"""
app/graph/nodes/classifier.py
------------------------------
Node: classifier_node

Wraps the existing ClassifierGenerator — no logic changes.
Writes 'classification' and 'language' into state.
"""
from __future__ import annotations
from app.graph.state import CommentState
from app.services.generator import classifier_generator


async def classifier_node(state: CommentState) -> dict:
    classification, language = await classifier_generator.classify(state.text)
    print(f"[classifier_node] comment={state.comment_id} "
          f"classification={classification} lang={language}")
    return {"classification": classification, "language": language}
