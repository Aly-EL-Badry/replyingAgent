"""
app/graph/router.py
-------------------
Conditional edge function for the 8-intent comment graph.

Maps state.intent -> the name of the next node to execute.
"""
from __future__ import annotations

from app.graph.state import CommentState

# Intent -> node name mapping
_INTENT_TO_NODE: dict[str, str] = {
    # Public intents
    "policy_query":         "policy_query_node",
    "product_availability": "product_availability_node",
    "shipping_cost":        "product_availability_node",   
    "positive_feedback":    "positive_feedback_node",
    "no_reply":             "no_reply_node",
    # Private intents
    "bad_feedback":         "bad_feedback_node",
    "make_order":           "make_order_node",
    "product_details":      "product_details_node",
}

_DEFAULT_NODE = "no_reply_node"


def classification_router(state: CommentState) -> str:
    return _INTENT_TO_NODE.get(state.intent or "", _DEFAULT_NODE)
