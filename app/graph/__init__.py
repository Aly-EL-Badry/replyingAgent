"""
app/graph/__init__.py
---------------------
LangGraph orchestrator package.

Public surface:
    from app.graph import comment_graph
"""
from .builder import comment_graph

__all__ = ["comment_graph"]
