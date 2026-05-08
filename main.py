from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.webhock import router as webhook_router
from app.api.v1.raghock import router as raghock_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup  — ensure the Weaviate knowledge-base collection exists.
    Shutdown — gracefully close the Weaviate connection.
    """
    # ── Startup ────────────────────────────────────────────────────────
    import asyncio
    from app.infrastructure.weaviate_client import weaviate_client

    await asyncio.to_thread(weaviate_client.ensure_collection)
    print("[App] Weaviate collection ready.")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────
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
app.include_router(raghock_router)
