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
from app.services.rag.embedder import hf_embedder


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_and_split(file_path: str) -> list[str]:
    """
    Synchronous helper: load a file with LlamaIndex and split into chunks.

    Returns a list of raw text strings, one per chunk.
    """
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()

    splitter = SentenceSplitter(
        chunk_size=constants.rag.chunk_size,
        chunk_overlap=constants.rag.chunk_overlap,
    )
    nodes = splitter.get_nodes_from_documents(documents)
    return [node.get_content() for node in nodes]


def _store_chunks(
    chunks: list[str],
    vectors: list[list[float]],
    source: str,
) -> int:
    """
    Synchronous helper: bulk-insert chunk–vector pairs into Weaviate.

    Returns the number of objects successfully inserted.
    """
    import weaviate.classes as wvc

    client = weaviate_client.get_client()
    collection_name = constants.rag.collection_name
    collection = client.collections.get(collection_name)

    objects: list[wvc.data.DataObject] = []
    for idx, (text, vector) in enumerate(zip(chunks, vectors)):
        objects.append(
            wvc.data.DataObject(
                properties={
                    "text": text,
                    "source": source,
                    "chunk_index": idx,
                },
                vector=vector,
            )
        )

    response = collection.data.insert_many(objects)
    errors = [str(e) for e in (response.errors or {}).values()]
    if errors:
        print(f"[RAGIngestion] Weaviate insert errors: {errors}")

    inserted = len(objects) - len(errors)
    return inserted


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def ingest_file(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """
    Main entry point for the RAG ingestion pipeline.

    Parameters
    ----------
    file_bytes:
        Raw content of the uploaded file.
    filename:
        Original filename (used to determine file type and stored as ``source``).

    Returns
    -------
    dict with keys:
        - ``status``        : "ok" | "error"
        - ``source``        : original filename
        - ``chunks_stored`` : number of chunks successfully stored (0 on error)
        - ``message``       : error description (only present on error)
    """
    # 1. Ensure Weaviate collection exists (idempotent)
    await asyncio.to_thread(weaviate_client.ensure_collection)

    # 2. Write bytes to a temporary file so LlamaIndex readers can open it
    suffix = Path(filename).suffix or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # 3. Load + chunk (synchronous, run in thread pool)
        chunks: list[str] = await asyncio.to_thread(_load_and_split, tmp_path)

        if not chunks:
            return {
                "status": "error",
                "source": filename,
                "chunks_stored": 0,
                "message": "No text could be extracted from the file.",
            }

        # 4. Embed all chunks in one batched call
        vectors: list[list[float]] = await hf_embedder.embed_batch(chunks)

        # 5. Store in Weaviate (synchronous DB call, run in thread pool)
        stored: int = await asyncio.to_thread(
            _store_chunks, chunks, vectors, filename
        )

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
        # Always clean up the temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
