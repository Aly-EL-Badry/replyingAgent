from __future__ import annotations

from typing import Any, List
import asyncio
from weaviate.classes.query import Filter
from app.infrastructure.weaviate_client import weaviate_client
from app.core.settings_constant import constants



from app.services.rag.ingestion import ingest_file
from app.services.rag.retriever import (
    RetrievedChunk,
    retrieve_context,
    retrieve_context_as_string,
)



class RAGService:
    def __init__(self):
        self.client = weaviate_client.get_client()
        self.collection_name = constants.rag.collection_name
   
    # Private Methods 
    def _do_delete(self, filename: str) -> int:    
        if not self.client.collections.exists(self.collection_name):
            return -1
        collection = self.client.collections.get(self.collection_name)
        result = collection.data.delete_many(where=Filter.by_property("source").equal(filename))
        return result.successful
    
    def _do_list(self) -> list[dict[str, Any]]:

        if not self.client.collections.exists(self.collection_name):
            return []

        collection = self.client.collections.get(self.collection_name)
        file_counts: dict[str, int] = {}
        for obj in collection.iterator(include_vector=False, return_properties=["source"]):
            source = obj.properties.get("source", "")
            if isinstance(source, str) and source:
                file_counts[source] = file_counts.get(source, 0) + 1

        return [
            {"source": src, "chunk_count": count}
            for src, count in sorted(file_counts.items())
        ]

    
    # Public Methods
    async def index_file(self,file_bytes: bytes,filename: str,) -> dict[str, Any]:
        return await ingest_file(file_bytes=file_bytes, filename=filename)

    async def retrieve(self,query: str,top_k: int | None = None,min_score: float | None = None,) -> List[RetrievedChunk]:
        return await retrieve_context(query, top_k=top_k, min_score=min_score)

    async def retrieve_as_string(self,query: str,top_k: int | None = None,min_score: float | None = None,separator: str = "\n\n---\n\n") -> str:
        return await retrieve_context_as_string(query,top_k=top_k,min_score=min_score,separator=separator)


    async def delete_file(self, filename: str) -> dict[str, Any]:
        deleted = await asyncio.to_thread(self._do_delete, filename)
        if deleted == -1:
            return {"status": "not_found", "source": filename, "chunks_deleted": 0}
        return {
            "status": "deleted" if deleted > 0 else "not_found",
            "source": filename,
            "chunks_deleted": deleted,
        }

    async def list_files(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._do_list)



rag_service = RAGService()
