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
from app.services.rag.embedder import hf_embedder


# ---------------------------------------------------------------------------
# Data transfer object
# ---------------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    """A single chunk returned by the retriever with its metadata."""

    text: str
    source: str
    chunk_index: int
    score: float  # cosine certainty in [0, 1]

    def to_context_string(self) -> str:
        """Format the chunk as a context block for LLM prompts."""
        return (
            f"[Source: {self.source} | Chunk #{self.chunk_index} | "
            f"Score: {self.score:.3f}]\n{self.text}"
        )


# ---------------------------------------------------------------------------
# Internal helper (synchronous — runs in thread pool)
# ---------------------------------------------------------------------------

def _weaviate_search(
    query_vector: List[float],
    top_k: int,
    min_score: float,
) -> List[RetrievedChunk]:
    """
    Execute a ``near_vector`` search against the Weaviate collection.

    Parameters
    ----------
    query_vector:
        Dense embedding of the user query.
    top_k:
        Maximum number of results to return from Weaviate.
    min_score:
        Minimum cosine certainty (0–1) to include in the returned list.

    Returns
    -------
    List[RetrievedChunk]
        Filtered and sorted (descending score) list of matching chunks.
    """
    import weaviate.classes as wvc

    client = weaviate_client.get_client()
    collection_name = constants.rag.collection_name
    collection = client.collections.get(collection_name)

    response = collection.query.near_vector(
        near_vector=query_vector,
        limit=top_k,
        return_metadata=wvc.query.MetadataQuery(certainty=True),
    )

    results: List[RetrievedChunk] = []
    for obj in response.objects:
        certainty: float = (
            obj.metadata.certainty if obj.metadata and obj.metadata.certainty is not None
            else 0.0
        )
        if certainty < min_score:
            continue
        results.append(
            RetrievedChunk(
                text=str(obj.properties.get("text", "")),
                source=str(obj.properties.get("source", "unknown")),
                chunk_index=int(obj.properties.get("chunk_index", 0)),
                score=certainty,
            )
        )

    # Sort highest score first
    results.sort(key=lambda c: c.score, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def retrieve_context(
    query: str,
    top_k: int | None = None,
    min_score: float | None = None,
) -> List[RetrievedChunk]:
    """
    Retrieve the most relevant knowledge-base chunks for a user query.

    Parameters
    ----------
    query:
        The raw user question or comment text.
    top_k:
        Override the default number of results (``constants.rag.top_k``).
    min_score:
        Override the default similarity threshold (``constants.rag.min_score``).

    Returns
    -------
    List[RetrievedChunk]
        Ranked list of matching chunks (may be empty if nothing is relevant).
    """
    effective_top_k: int = top_k if top_k is not None else constants.rag.top_k
    effective_min_score: float = min_score if min_score is not None else constants.rag.min_score

    # Embed the query (async, thread-safe)
    query_vector: List[float] = await hf_embedder.embed_text(query)

    # Perform Weaviate search (synchronous DB call → thread pool)
    chunks: List[RetrievedChunk] = await asyncio.to_thread(
        _weaviate_search, query_vector, effective_top_k, effective_min_score
    )

    return chunks


async def retrieve_context_as_string(
    query: str,
    top_k: int | None = None,
    min_score: float | None = None,
    separator: str = "\n\n---\n\n",
) -> str:
    """
    Convenience wrapper: retrieve chunks and join them into a single
    context string ready to be injected into an LLM prompt.

    Returns an empty string when no relevant chunks are found.
    """
    chunks = await retrieve_context(query, top_k=top_k, min_score=min_score)
    if not chunks:
        return ""
    return separator.join(c.to_context_string() for c in chunks)
