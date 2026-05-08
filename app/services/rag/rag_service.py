"""
app/services/rag/rag_service.py
--------------------------------
High-level RAG facade that combines ingestion + retrieval into a single
coherent service layer.

This is the recommended entry point for LangGraph nodes and generator
classes that need RAG capabilities.  It avoids importing multiple sub-modules
directly and provides a stable, versioned interface.

Usage
-----
    from app.services.rag.rag_service import rag_service

    # ── Ingestion (called from the /raghock endpoint) ──────────────────
    result = await rag_service.index_file(file_bytes, "policy.pdf")

    # ── Retrieval (called from graph nodes / generators) ───────────────
    chunks  = await rag_service.retrieve("What is the refund policy?")
    context = await rag_service.retrieve_as_string("What is the refund policy?")
"""
from __future__ import annotations

from typing import Any, List

from app.services.rag.ingestion import ingest_file
from app.services.rag.retriever import (
    RetrievedChunk,
    retrieve_context,
    retrieve_context_as_string,
)


class RAGService:
    """
    Unified facade for all RAG operations.

    Methods
    -------
    index_file(file_bytes, filename)
        Run the full ingestion pipeline for an uploaded file.
    retrieve(query, top_k, min_score)
        Return a ranked list of ``RetrievedChunk`` objects.
    retrieve_as_string(query, top_k, min_score, separator)
        Return retrieved context as a single prompt-ready string.
    """

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    async def index_file(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> dict[str, Any]:
        """
        Ingest a file into the knowledge base.

        Parameters
        ----------
        file_bytes:
            Raw content of the uploaded file.
        filename:
            Original filename (used to determine file type and stored as the
            ``source`` field in Weaviate).

        Returns
        -------
        dict with keys:
            - ``status``        : "ok" | "error"
            - ``source``        : original filename
            - ``chunks_stored`` : number of chunks successfully stored
            - ``message``       : error description (only on error)
        """
        return await ingest_file(file_bytes=file_bytes, filename=filename)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for *query*.

        Parameters
        ----------
        query:
            User question or comment text.
        top_k:
            Override the default number of results from ``ragSettings.yaml``.
        min_score:
            Override the default similarity threshold from ``ragSettings.yaml``.

        Returns
        -------
        List[RetrievedChunk]
            Ordered by descending cosine similarity.  Empty when nothing is
            relevant or the knowledge base is empty.
        """
        return await retrieve_context(query, top_k=top_k, min_score=min_score)

    async def retrieve_as_string(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        Retrieve relevant chunks and join them into a single context string.

        Ideal for direct injection into LLM system or user prompts.
        Returns an empty string when the knowledge base has no relevant
        content for *query*.
        """
        return await retrieve_context_as_string(
            query,
            top_k=top_k,
            min_score=min_score,
            separator=separator,
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
rag_service = RAGService()
