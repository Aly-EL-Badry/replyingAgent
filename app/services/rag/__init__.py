"""
app/services/rag/__init__.py
-----------------------------
Public re-exports for the RAG service module.

Import surface
--------------
    from app.services.rag import rag_service
    from app.services.rag import RetrievedChunk
    from app.services.rag import ingest_file, retrieve_context, retrieve_context_as_string
"""
from app.services.rag.rag_service import rag_service, RAGService
from app.services.rag.retriever import (
    RetrievedChunk,
    retrieve_context,
    retrieve_context_as_string,
)
from app.services.rag.ingestion import ingest_file
from app.services.rag.embedder import hf_embedder, RAGEmbedder

__all__ = [
    # Facade
    "rag_service",
    "RAGService",
    # Retrieval
    "RetrievedChunk",
    "retrieve_context",
    "retrieve_context_as_string",
    # Ingestion
    "ingest_file",
    # Embedder
    "hf_embedder",
    "RAGEmbedder",
]
