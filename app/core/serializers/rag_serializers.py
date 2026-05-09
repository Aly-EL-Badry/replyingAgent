
from pydantic import BaseModel


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
