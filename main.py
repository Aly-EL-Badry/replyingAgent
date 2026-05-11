from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health    import router as health_router
from app.api.v1.webhock   import router as webhook_router
from app.api.v1.ragHock   import router as ragHock_router
from app.api.v1.orders import router as ordersHock_router
from app.api.v1.ticket import router as ticketsHock_router
from app.api.v1.feedback  import router as feedback_router

from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
      - Enable pgvector extension (idempotent).
      - Create all tables if they do not exist.
      - Seed the product catalog if empty.

    Shutdown:
      - SQLAlchemy engine disposes connections automatically via GC;
        explicit dispose called for clean shutdown.
    """
    await init_db()
    print("[App] PostgreSQL ready.")

    yield

    from app.db import engine
    await engine.dispose()
    print("[App] PostgreSQL connections closed.")


app = FastAPI(
    title="FacebookReplay — AI-Powered Facebook Agent",
    description=(
        "FastAPI + LangGraph service that auto-replies to Facebook comments "
        "and Messenger DMs, backed by a PostgreSQL database (pgvector RAG, "
        "catalog, orders, tickets, conversation history)."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(webhook_router)
app.include_router(ragHock_router)
app.include_router(ordersHock_router)
app.include_router(ticketsHock_router)
app.include_router(feedback_router)

