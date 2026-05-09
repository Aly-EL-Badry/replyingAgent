from __future__ import annotations
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse


from app.services.rag import rag_service
from app.core.serializers.rag_serializers import QueryRequest, QueryResponse
from app.core.settings_constant import constants

router = APIRouter(prefix="/raghock", tags=["RAG Knowledge Base"])



# Background ingestion 
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



# Endpoints
@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="File to ingest (.txt, .pdf, .docx, .md, .csv)"),
) -> JSONResponse:
    """Receive a file upload and queue it for asynchronous ingestion into the knowledge base. Supported formats: txt, pdf, docx, md, csv"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    ext = Path(file.filename).suffix.lower()
    allowed = set(constants.rag.allowed_extensions)
    if ext not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(allowed))}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

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


@router.post("/query",response_model=QueryResponse,)  
async def query_knowledge_base(body: QueryRequest) -> QueryResponse:
    """Embed *query* and perform a similarity search against the knowledge base. Returns the top matching chunks as a formatted context string."""
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


@router.get("/files")
async def list_files() -> dict[str, Any]:
    """Return every unique source file"""
    files = await rag_service.list_files()
    return {
        "total_files": len(files),
        "files": files,
    }


@router.delete("/file/{filename}")
async def delete_file(filename: str) -> dict[str, Any]:
    """Delete every chunk in the knowledge base whose ``source`` matches"""
    result = await rag_service.delete_file(filename)
    if result["status"] == "not_found":
        raise HTTPException(
            status_code=404,
            detail=f"No embeddings found for file '{filename}'.",
        )
    return result
