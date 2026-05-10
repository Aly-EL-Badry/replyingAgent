from pydantic import BaseModel, Field
from typing import Any, List, Optional, Annotated
from operator import add


class CommentState(BaseModel):
    # ── Core comment fields ────────────────────────────────────────────────
    comment_id: str
    sender_id:  str
    text:       str

    # ── Conversation history (LangGraph append-reducer) ────────────────────
    history: Annotated[List[dict], add] = Field(default_factory=list)

    # ── Classification ─────────────────────────────────────────────────────
    # Fine-grained intent returned by the classifier
    intent: Optional[str] = None
    # High-level bucket derived from intent ("public" | "private")
    classification: Optional[str] = None
    # ISO-639-1 language code detected by the classifier
    language: Optional[str] = "en"

    # ── Routing override (future use) ─────────────────────────────────────
    next_node: Optional[str] = None

    # ── RAG context (pre-fetched by nodes that need it) ───────────────────
    rag_context: Optional[str] = None

    # ── Structured data collected during node execution ───────────────────
    # e.g. order details, product status, extracted fields
    collected_data: dict[str, Any] = Field(default_factory=dict)

    # ── Output IDs created during processing ─────────────────────────────
    ticket_id: Optional[str] = None
    order_id:  Optional[str] = None