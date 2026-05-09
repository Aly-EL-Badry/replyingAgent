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

__all__ = [
    "rag_service",
    "RAGService",
    "RetrievedChunk",
    "retrieve_context",
    "retrieve_context_as_string",
    "ingest_file",
]
