"""
app/graph/builder.py
---------------------
Assembles and compiles the comment-processing StateGraph.

Uses MemorySaver (in-process) for validation.
Swap to RedisSaver later when ready.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import CommentState
from app.graph.nodes.classifier import classifier_node
from app.graph.nodes.public_reply import public_reply_node
from app.graph.nodes.private_reply import private_reply_node
from app.graph.router import classification_router


class AgentGraph():
    def __init__(self):
        builder = StateGraph(CommentState)

        builder.add_node("classifier_node",   classifier_node) 
        builder.add_node("public_reply_node", public_reply_node)
        builder.add_node("private_reply_node", private_reply_node)

        builder.add_edge(START, "classifier_node")

        builder.add_conditional_edges(
            "classifier_node",
            classification_router,
            {
                "public_reply_node":  "public_reply_node",
                "private_reply_node": "private_reply_node",
            },
        )

        builder.add_edge("public_reply_node",  END)
        builder.add_edge("private_reply_node", END)

        self.graph = builder.compile(checkpointer=MemorySaver())


# Module-level singleton — built once on import, reused across requests
comment_graph = AgentGraph()
