"""
app/graph/router.py
-------------------
Conditional edge function for the comment graph.

Returns the name of the next node based on the classification
set by classifier_node.
"""
from __future__ import annotations
from app.graph.state import CommentState


def classification_router(state: CommentState) -> str:
    if state.classification == "private":
        return "private_reply_node"
    return "public_reply_node"
