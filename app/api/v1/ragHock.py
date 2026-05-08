"""
app/api/v1/raghock.py
----------------------
RAG ingestion endpoint — accepts file uploads and indexes them into the
Weaviate knowledge base.

Endpoints
---------
POST /raghock/upload
    Upload a single file (txt, pdf, docx, md).  The file is immediately
    processed by the ingestion pipeline in the background and stored in
    Weaviate for future retrieval.

POST /raghock/query  (optional convenience endpoint)
    Query the knowledge base directly via the REST API (useful for
    debugging / testing without going through the LangGraph pipeline).

DELETE /raghock/collection
    Wipe the entire knowledge-base collection (dangerous — dev/debug only).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.rag import rag_service

router = APIRouter(prefix="/raghock", tags=["RAG Knowledge Base"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""
    query: str
    top_k: int | None = None
    min_score: float | None = None


class QueryResponse(BaseModel):
    """Response body for the /query endpoint."""
    query: str
    context: str
    chunks_found: int


# ---------------------------------------------------------------------------
# Background ingestion wrapper
# ---------------------------------------------------------------------------

async def _background_ingest(file_bytes: bytes, filename: str) -> None:
    """Called as a FastAPI background task so the upload returns immediately."""
    result = await rag_service.index_file(file_bytes=file_bytes, filename=filename)
    if result["status"] == "ok":
        print(
            f"[RAGhock] ✅ Indexed '{filename}' — "
            f"{result['chunks_stored']} chunks stored."
        )
    else:
        print(
            f"[RAGhock] ❌ Failed to index '{filename}': "
            f"{result.get('message', 'unknown error')}"
        )


# ---------------------------------------------------------------------------
# Allowed file types
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".md", ".csv"}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    summary="Upload a file to the knowledge base",
    response_description="Acknowledgement that the file has been queued for indexing",
)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="File to ingest (.txt, .pdf, .docx, .md, .csv)"),
) -> JSONResponse:
    """
    Receive a file upload and queue it for asynchronous ingestion into the
    Weaviate knowledge base.

    The endpoint returns **immediately** with ``202 Accepted``.  Indexing
    (loading, chunking, embedding, storing) happens in the background.

    Supported formats: ``.txt``, ``.pdf``, ``.docx``, ``.md``, ``.csv``
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    from pathlib import Path
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Queue ingestion as a background task (non-blocking)
    background_tasks.add_task(_background_ingest, file_bytes, file.filename)

    return JSONResponse(
        status_code=202,
        content={
            "status": "queued",
            "filename": file.filename,
            "size_bytes": len(file_bytes),
            "message": "File has been queued for indexing. Check server logs for progress.",
        },
    )


@router.post(
    "/query",
    summary="Query the knowledge base",
    response_model=QueryResponse,
)
async def query_knowledge_base(body: QueryRequest) -> QueryResponse:
    """
    Embed *query* and perform a similarity search against the Weaviate
    knowledge base.  Returns the top matching chunks as a formatted
    context string.

    Useful for debugging RAG retrieval quality without triggering the
    full LangGraph pipeline.
    """
    chunks = await rag_service.retrieve(
        query=body.query,
        top_k=body.top_k,
        min_score=body.min_score,
    )
    context = "\n\n---\n\n".join(c.to_context_string() for c in chunks)

    return QueryResponse(
        query=body.query,
        context=context,
        chunks_found=len(chunks),
    )


@router.delete(
    "/collection",
    summary="[DEBUG] Delete the entire knowledge-base collection",
    response_description="Deletion result",
)
async def delete_collection(
    confirm: bool = Query(
        False,
        description="Set to true to confirm deletion. THIS IS IRREVERSIBLE.",
    ),
) -> dict[str, Any]:
    """
    **Danger zone** — deletes the entire Weaviate collection and all indexed
    documents.  Intended for development and testing only.

    You must pass ``?confirm=true`` as a query parameter to prevent accidental
    deletion.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Pass ?confirm=true to confirm deletion.",
        )

    from app.infrastructure.weaviate_client import weaviate_client
    from app.core.settings_constant import constants

    client = weaviate_client.get_client()
    collection_name = constants.rag.collection_name

    if client.collections.exists(collection_name):
        client.collections.delete(collection_name)
        return {"status": "deleted", "collection": collection_name}

    return {"status": "not_found", "collection": collection_name}
