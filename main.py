from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.webhock import router as webhook_router
from app.api.v1.ragHock import router as ragHock_router

import asyncio
from app.infrastructure.weaviate_client import weaviate_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup  — ensure the Weaviate knowledge-base collection exists.
    Shutdown — gracefully close the Weaviate connection.
    """

    await asyncio.to_thread(weaviate_client.get_client)
    print("[App] Weaviate collection ready.")

    yield

    weaviate_client.close()
    print("[App] Weaviate connection closed.")


app = FastAPI(
    title="FacebookReplay — AI-Powered Facebook Agent",
    description=(
        "FastAPI + LangGraph service that auto-replies to Facebook comments "
        "and Messenger DMs, backed by a Weaviate RAG knowledge base."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(ragHock_router)
