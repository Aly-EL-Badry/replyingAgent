"""
app/graph/builder.py
---------------------
Assembles and compiles the 8-intent comment-processing StateGraph.

Node map:
  Public  -> policy_query_node, product_availability_node, positive_feedback_node, no_reply_node
  Private -> bad_feedback_node, make_order_node, product_details_node

Uses MemorySaver (in-process) for the checkpointer.
Swap to RedisSaver when persistent multi-tenant sessions are needed.
"""
from typing import Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import CommentState
from app.graph.router import classification_router

from app.graph.nodes.classifier           import classifier_node
from app.graph.nodes.public.policy_query         import policy_query_node
from app.graph.nodes.public.product_availability import product_availability_node
from app.graph.nodes.public.positive_feedback    import positive_feedback_node
from app.graph.nodes.public.no_reply             import no_reply_node
from app.graph.nodes.private.bad_feedback         import bad_feedback_node
from app.graph.nodes.private.make_order           import make_order_node
from app.graph.nodes.private.product_details      import product_details_node


_ALL_INTENT_NODES: dict[str, Any] = {
    "policy_query_node":         policy_query_node,
    "product_availability_node": product_availability_node,
    "positive_feedback_node":    positive_feedback_node,
    "no_reply_node":             no_reply_node,
    
    "bad_feedback_node":         bad_feedback_node,
    "make_order_node":           make_order_node,
    "product_details_node":      product_details_node,
}


class AgentGraph:
    def __init__(self) -> None:
        builder = StateGraph(CommentState)

        builder.add_node("classifier_node", classifier_node)
        for name, fn in _ALL_INTENT_NODES.items():
            builder.add_node(name, fn)

        builder.add_edge(START, "classifier_node")

        builder.add_conditional_edges(
            "classifier_node",
            classification_router,
            {name: name for name in _ALL_INTENT_NODES},
        )

        for name in _ALL_INTENT_NODES:
            builder.add_edge(name, END)

        self.graph = builder.compile(checkpointer=MemorySaver())



comment_graph = AgentGraph()
