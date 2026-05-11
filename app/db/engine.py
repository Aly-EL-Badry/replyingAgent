"""
app/db/engine.py
-----------------
SQLAlchemy async engine + session factory.

A single module owns the engine so every part of the app imports
from the same place — no duplicate engine instances.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings_secrets import secrets

engine = create_async_engine(
    secrets.database_url,
    echo=False,          
    pool_pre_ping=True,  
    pool_size=10,
    max_overflow=20,
)


async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
