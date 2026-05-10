"""
app/services/rag/retriever.py
------------------------------
Similarity-search retriever: query text → HF embedding → pgvector
cosine-similarity search → ranked list of RetrievedChunk objects.

Replaces the Weaviate hybrid search.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List

from sqlalchemy import select, text

from app.core.settings_constant import constants
from app.db                     import async_session_factory, KnowledgeChunk
from app.services.rag.embedder  import rag_embedder


@dataclass
class RetrievedChunk:
    """A single chunk returned by the retriever with its metadata."""
    text:        str
    source:      str
    chunk_index: int
    score:       float

    def to_context_string(self) -> str:
        return (
            f"[Source: {self.source} | Chunk #{self.chunk_index} | "
            f"Score: {self.score:.3f}]\n{self.text}"
        )


async def retrieve_context(
    query: str,
    top_k: int | None = None,
    min_score: float | None = None,
) -> List[RetrievedChunk]:
    """
    Embed *query* and return the top_k most similar knowledge chunks
    whose cosine similarity >= min_score.
    """
    effective_top_k    = top_k     if top_k     is not None else constants.rag.top_k
    effective_min_score = min_score if min_score is not None else constants.rag.min_score

    # Embed the query in a thread (CPU-bound)
    query_vec: list[float] = await asyncio.to_thread(rag_embedder.embed_text, query)

    # pgvector cosine distance operator: <=>
    # cosine_similarity = 1 - cosine_distance
    async with async_session_factory() as session:
        stmt = (
            select(
                KnowledgeChunk.text,
                KnowledgeChunk.source,
                KnowledgeChunk.chunk_index,
                (
                    text("1 - (embedding <=> CAST(:vec AS vector))")
                ).label("score"),
            )
            .where(KnowledgeChunk.embedding.isnot(None))
            .order_by(text("embedding <=> CAST(:vec AS vector)"))
            .limit(effective_top_k)
            .params(vec=str(query_vec))
        )
        rows = (await session.execute(stmt)).all()

    results: List[RetrievedChunk] = [
        RetrievedChunk(
            text=row.text,
            source=row.source,
            chunk_index=row.chunk_index,
            score=float(row.score),
        )
        for row in rows
        if float(row.score) >= effective_min_score
    ]
    return results


async def retrieve_context_as_string(
    query: str,
    top_k: int | None = None,
    min_score: float | None = None,
    separator: str = "\n\n---\n\n",
) -> str:
    chunks = await retrieve_context(query, top_k=top_k, min_score=min_score)
    if not chunks:
        return ""
    return separator.join(c.to_context_string() for c in chunks)
