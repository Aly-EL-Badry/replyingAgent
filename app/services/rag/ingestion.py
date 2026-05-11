"""
app/services/rag/ingestion.py
------------------------------
Document ingestion pipeline: raw file bytes → LlamaIndex chunks →
HF embeddings → PostgreSQL knowledge_chunks table.

Supported file types (auto-detected by extension):
    .txt .pdf .docx .md .csv
"""
from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any

from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from sqlalchemy import delete, func, select

from app.core.settings_constant import constants
from app.db                     import async_session_factory, KnowledgeChunk
from app.services.rag.embedder  import rag_embedder


def _load_and_split(file_path: str) -> list[str]:
    reader    = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()
    
    if file_path.lower().endswith('.md'):
        from llama_index.core.node_parser import MarkdownNodeParser
        parser = MarkdownNodeParser()
        nodes = parser.get_nodes_from_documents(documents)
    else:
        splitter  = SentenceSplitter(
            chunk_size=constants.rag.chunk_size,
            chunk_overlap=constants.rag.chunk_overlap,
        )
        nodes = splitter.get_nodes_from_documents(documents)
        
    return [node.get_content() for node in nodes]


async def _store_chunks(chunks: list[str], source: str) -> int:
    """Embed all chunks and bulk-insert them into PostgreSQL."""
    embeddings: list[list[float]] = await asyncio.to_thread(
        rag_embedder.embed_batch, chunks
    )
    rows = [
        KnowledgeChunk(
            text        = text,
            source      = source,
            chunk_index = idx,
            embedding   = emb,
        )
        for idx, (text, emb) in enumerate(zip(chunks, embeddings))
    ]
    async with async_session_factory() as session:
        session.add_all(rows)
        await session.commit()
    return len(rows)


async def ingest_file(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Ingest a file into the PostgreSQL knowledge base."""
    suffix = Path(filename).suffix or ".txt"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        chunks: list[str] = await asyncio.to_thread(_load_and_split, tmp_path)

        if not chunks:
            return {
                "status": "error", "source": filename,
                "chunks_stored": 0,
                "message": "No text could be extracted from the file.",
            }

        stored = await _store_chunks(chunks, filename)
        return {"status": "ok", "source": filename, "chunks_stored": stored}

    except Exception as exc:
        return {
            "status": "error", "source": filename,
            "chunks_stored": 0, "message": str(exc),
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def delete_chunks_for_source(source: str) -> int:
    async with async_session_factory() as session:
        count_stmt = select(func.count()).select_from(KnowledgeChunk).where(
            KnowledgeChunk.source == source
        )
        total = (await session.execute(count_stmt)).scalar_one()

        if total > 0:
            await session.execute(
                delete(KnowledgeChunk).where(KnowledgeChunk.source == source)
            )
            await session.commit()

        return total

