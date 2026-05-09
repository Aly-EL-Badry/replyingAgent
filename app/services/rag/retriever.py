"""
app/services/rag/retriever.py
------------------------------
Similarity-search retriever: query text → embedding → Weaviate near-vector search
→ ranked list of ``RetrievedChunk`` objects.

Key concepts
------------
* The query is embedded with the same ``RAGEmbedder`` used during ingestion
  (same model = same vector space).
* Weaviate's ``near_vector`` query finds the ``top_k`` closest chunks by
  cosine similarity.
* Results with a certainty (cosine sim) below ``min_score`` are filtered out.

Usage
-----
    from app.services.rag.retriever import retrieve_context, RetrievedChunk

    chunks = await retrieve_context("What is the refund policy?")
    for c in chunks:
        print(c.text, c.score, c.source)
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List

from app.core.settings_constant import constants
from app.infrastructure.weaviate_client import weaviate_client
import weaviate.classes as wvc

@dataclass
class RetrievedChunk:
    """A single chunk returned by the retriever with its metadata."""

    text: str
    source: str
    chunk_index: int
    score: float 

    def to_context_string(self) -> str:
        return (
            f"[Source: {self.source} | Chunk #{self.chunk_index} | "
            f"Score: {self.score:.3f}]\n{self.text}"
        )


def _weaviate_search(query: str, top_k: int, min_score: float) -> List[RetrievedChunk]:
    """
    Execute a hybrid (BM25 + bi-encoder) search against the Weaviate collection.
    Weaviate auto-embeds the query via text2vec-huggingface for the dense leg.
    """

    client = weaviate_client.get_client()
    collection = client.collections.get(constants.rag.collection_name)

    response = collection.query.hybrid(
        query=query,
        alpha=0.5,
        limit=top_k,
        return_metadata=wvc.query.MetadataQuery(score=True),
    )

    results: List[RetrievedChunk] = []
    for obj in response.objects:
        score = obj.metadata.score if obj.metadata and obj.metadata.score is not None else 0.0
        if score < min_score:
            continue
        ci = obj.properties.get("chunk_index", 0)
        results.append(
            RetrievedChunk(
                text=str(obj.properties.get("text", "")),
                source=str(obj.properties.get("source", "unknown")),
                chunk_index=int(ci) if isinstance(ci, (int, float, str)) else 0,
                score=score,
            )
        )

    results.sort(key=lambda c: c.score, reverse=True)
    return results


async def retrieve_context(query: str,top_k: int | None = None,min_score: float | None = None,) -> List[RetrievedChunk]:
    effective_top_k: int = top_k if top_k is not None else constants.rag.top_k
    effective_min_score: float = min_score if min_score is not None else constants.rag.min_score

    return await asyncio.to_thread(
        _weaviate_search, query, effective_top_k, effective_min_score
    )


async def retrieve_context_as_string(query: str,top_k: int | None = None,min_score: float | None = None,separator: str = "\n\n---\n\n",) -> str:
    chunks = await retrieve_context(query, top_k=top_k, min_score=min_score)
    if not chunks:
        return ""
    return separator.join(c.to_context_string() for c in chunks)
