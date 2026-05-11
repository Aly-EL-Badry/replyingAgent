from __future__ import annotations

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from app.core.settings_constant import constants


class RAGEmbedder:
    """Lazy-loaded local HuggingFace embedding model."""

    def __init__(self) -> None:
        self._model: HuggingFaceEmbedding | None = None

    def _get_model(self) -> HuggingFaceEmbedding:
        if self._model is None:
            self._model = HuggingFaceEmbedding(
                model_name=constants.rag.embedding_model,
                embed_batch_size=32,
            )
            print(f"[RAGEmbedder] Loaded model: {constants.rag.embedding_model}")
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Return a single embedding vector for *text*."""
        return self._get_model().get_text_embedding(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return a list of embedding vectors for a batch of texts."""
        return self._get_model().get_text_embedding_batch(texts)


rag_embedder = RAGEmbedder()
