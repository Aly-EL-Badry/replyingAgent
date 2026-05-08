from pydantic import BaseModel


class RagSettings(BaseModel):
    """Pydantic model for RAG configuration loaded from ragSettings.yaml."""

    collection_name: str
    embedding_model: str
    embedding_dimension: int
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float
