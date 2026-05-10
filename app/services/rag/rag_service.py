"""
app/services/rag/rag_service.py
--------------------------------
High-level RAG service used by the API layer (ragHock.py).

Delegates storage/retrieval entirely to PostgreSQL via ingestion.py
and retriever.py — no Weaviate dependency.
"""
from __future__ import annotations

from typing import Any, List

from sqlalchemy import func, select

from app.db                        import async_session_factory, KnowledgeChunk
from app.services.rag.ingestion    import ingest_file, delete_chunks_for_source
from app.services.rag.retriever    import (
    RetrievedChunk,
    retrieve_context,
    retrieve_context_as_string,
)


class RAGService:

    async def index_file(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        return await ingest_file(file_bytes=file_bytes, filename=filename)

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
    ) -> List[RetrievedChunk]:
        return await retrieve_context(query, top_k=top_k, min_score=min_score)

    async def retrieve_as_string(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
        separator: str = "\n\n---\n\n",
    ) -> str:
        return await retrieve_context_as_string(
            query, top_k=top_k, min_score=min_score, separator=separator
        )

    async def delete_file(self, filename: str) -> dict[str, Any]:
        deleted = await delete_chunks_for_source(filename)
        return {
            "status":         "deleted" if deleted > 0 else "not_found",
            "source":         filename,
            "chunks_deleted": deleted,
        }

    async def list_files(self) -> list[dict[str, Any]]:
        async with async_session_factory() as session:
            stmt = (
                select(KnowledgeChunk.source, func.count().label("chunk_count"))
                .group_by(KnowledgeChunk.source)
                .order_by(KnowledgeChunk.source)
            )
            rows = (await session.execute(stmt)).all()
        return [{"source": r.source, "chunk_count": r.chunk_count} for r in rows]


rag_service = RAGService()
