"""
app/services/rag/embedder.py
-----------------------------
HuggingFace embedding service built on top of LlamaIndex's
``HuggingFaceEmbedding`` wrapper.

This module owns the singleton ``hf_embedder`` that is shared by both
the ingestion pipeline (document → vectors stored in Weaviate) and the
retriever (query → vector used for similarity search).

The embedding model is configured via ``config/ragSettings.yaml``:
    rag:
      embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

Usage
-----
    from app.services.rag.embedder import hf_embedder

    vector = await hf_embedder.embed_text("What is the return policy?")
    vectors = await hf_embedder.embed_batch(["text 1", "text 2"])
"""
from __future__ import annotations

import asyncio
from typing import List

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from app.core.settings_constant import constants


class RAGEmbedder:
    """
    Async wrapper around LlamaIndex's ``HuggingFaceEmbedding``.

    All heavy embedding work is executed in a thread pool via
    ``asyncio.to_thread`` so it does not block the FastAPI event loop.
    """

    def __init__(self) -> None:
        model_name: str = constants.rag.embedding_model
        self._embed_model = HuggingFaceEmbedding(model_name=model_name)
        print(f"[RAGEmbedder] Loaded embedding model: {model_name}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed_text(self, text: str) -> List[float]:
        """
        Embed a single string and return its vector.

        Parameters
        ----------
        text:
            The text to embed.

        Returns
        -------
        List[float]
            Dense embedding vector of length ``constants.rag.embedding_dimension``.
        """
        return await asyncio.to_thread(
            self._embed_model.get_text_embedding, text
        )

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of strings in a single batched call.

        Parameters
        ----------
        texts:
            The texts to embed.

        Returns
        -------
        List[List[float]]
            A list of embedding vectors, one per input text.
        """
        return await asyncio.to_thread(
            self._embed_model.get_text_embedding_batch, texts
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
hf_embedder = RAGEmbedder()
