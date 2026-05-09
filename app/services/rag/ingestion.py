"""
app/services/rag/ingestion.py
------------------------------
Document ingestion pipeline: raw file bytes → LlamaIndex chunks → HF embeddings
→ Weaviate vector store.

Supported file types (auto-detected by extension):
    .txt   — plain text
    .pdf   — PDF (requires ``pypdf`` which LlamaIndex installs automatically)
    .docx  — Word documents (requires ``python-docx``)
    .md    — Markdown (treated as plain text)

Pipeline overview
-----------------
1. ``ingest_file()``   — receives raw bytes + filename from the API layer
2. Persists bytes to a temp file so LlamaIndex readers can open it
3. ``SimpleDirectoryReader`` (LlamaIndex) loads the file into ``Document`` objects
4. ``SentenceSplitter`` splits documents into overlapping chunks
5. ``RAGEmbedder.embed_batch()`` converts all chunk texts to vectors
6. Chunks + vectors are bulk-upserted into the Weaviate collection via
   ``WeaviateClientWrapper.ensure_collection()`` + batch insert

Usage
-----
    from app.services.rag.ingestion import ingest_file

    result = await ingest_file(file_bytes=b"...", filename="policy.pdf")
    # → {"status": "ok", "source": "policy.pdf", "chunks_stored": 42}
"""

from __future__ import annotations

import asyncio
import tempfile
import os
from pathlib import Path
from typing import Any

from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

from app.core.settings_constant import constants
from app.infrastructure.weaviate_client import weaviate_client
import weaviate.classes as wvc

# Internal helpers
def _load_and_split(file_path: str) -> list[str]:
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()

    splitter = SentenceSplitter(
        chunk_size=constants.rag.chunk_size,
        chunk_overlap=constants.rag.chunk_overlap,
    )
    nodes = splitter.get_nodes_from_documents(documents)
    return [node.get_content() for node in nodes]


def _store_chunks(chunks: list[str], source: str) -> int:
    client = weaviate_client.get_client()
    collection_name = constants.rag.collection_name
    collection = client.collections.get(collection_name)

    objects: list[wvc.data.DataObject[dict[str, Any]]] = [
        wvc.data.DataObject(
            properties={"text": text, "source": source, "chunk_index": idx},
        )
        for idx, text in enumerate(chunks)
    ]

    response = collection.data.insert_many(objects)
    errors = [str(e) for e in (response.errors or {}).values()]
    if errors:
        print(f"[RAGIngestion] Weaviate insert errors: {errors}")

    return len(objects) - len(errors)


# public API
async def ingest_file(file_bytes: bytes, filename: str) -> dict[str, Any]:
    suffix = Path(filename).suffix or ".txt"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        chunks: list[str] = await asyncio.to_thread(_load_and_split, tmp_path)

        if not chunks:
            return {
                "status": "error",
                "source": filename,
                "chunks_stored": 0,
                "message": "No text could be extracted from the file.",
            }

        stored: int = await asyncio.to_thread(_store_chunks, chunks, filename)

        return {
            "status": "ok",
            "source": filename,
            "chunks_stored": stored,
        }

    except Exception as exc:
        return {
            "status": "error",
            "source": filename,
            "chunks_stored": 0,
            "message": str(exc),
        }

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
