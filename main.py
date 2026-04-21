from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.webhock import router as webhook_router

app = FastAPI()

app.include_router(health_router)
app.include_router(webhook_router)

