"""
app/db/init_db.py
------------------
Database bootstrap — called once at application startup.

1. Enable the pgvector extension (requires it on the PG server — available
   by default on Supabase, Neon, etc.).
2. Create all tables that do not yet exist (idempotent).
3. Seed the products table from the inline demo list if it is empty.
"""
from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import engine, async_session_factory
from app.db.base   import Base


import app.db.models  

from app.db.models import ProductRow

# Inline here — no dependency on any catalog layer.
_SEED_PRODUCTS: list[dict] = [
    {
        "id": "AGR-001", "name": "Smart Soil Sensor",
        "name_ar": "حساس التربة الذكي", "category": "monitoring",
        "description": "Measures soil moisture, pH, and nutrients. Sends data directly to your phone.",
        "price": 850.00, "currency": "EGP", "stock_status": "in_stock", "stock_qty": 150,
        "tags": ["soil", "sensor", "smart-farming", "moisture"], "estimated_restock": None,
    },
    {
        "id": "AGR-002", "name": "Automatic Drip Irrigation Kit",
        "name_ar": "نظام الري بالتنقيط التلقائي", "category": "irrigation",
        "description": "Solar-powered watering system that adjusts based on weather forecasts.",
        "price": 2200.00, "currency": "EGP", "stock_status": "limited", "stock_qty": 15,
        "tags": ["water", "irrigation", "solar", "automatic"], "estimated_restock": None,
    },
    {
        "id": "AGR-003", "name": "Crop Health Drone",
        "name_ar": "درون فحص المحاصيل", "category": "aerial",
        "description": "Easy-to-fly drone that spots dry patches and pest infestations from above.",
        "price": 15500.00, "currency": "EGP", "stock_status": "in_stock", "stock_qty": 25,
        "tags": ["drone", "camera", "crops", "aerial-view"], "estimated_restock": None,
    },
    {
        "id": "AGR-004", "name": "Organic Fertilizer Mix",
        "name_ar": "خليط سماد عضوي", "category": "nutrients",
        "description": "Premium 10kg bag of slow-release organic nutrients for better yields.",
        "price": 350.00, "currency": "EGP", "stock_status": "out_of_stock", "stock_qty": 0,
        "tags": ["fertilizer", "organic", "plants", "growth"], "estimated_restock": "Available next week",
    },
    {
        "id": "AGR-005", "name": "Solar Powered Pest Repeller",
        "name_ar": "طارد آفات يعمل بالطاقة الشمسية", "category": "protection",
        "description": "Uses ultrasonic sound to keep rodents and birds away without chemicals.",
        "price": 450.00, "currency": "EGP", "stock_status": "in_stock", "stock_qty": 200,
        "tags": ["pests", "solar", "protection", "ultrasonic"], "estimated_restock": None,
    },
    {
        "id": "AGR-006", "name": "Handheld pH Meter",
        "name_ar": "جهاز قياس الحموضة اليدوي", "category": "tools",
        "description": "Digital pocket-sized tool to check water and soil acidity instantly.",
        "price": 180.00, "currency": "EGP", "stock_status": "in_stock", "stock_qty": 85,
        "tags": ["tools", "pH", "water", "testing"], "estimated_restock": None,
    },
    {
        "id": "AGR-007", "name": "Weather Station Hub",
        "name_ar": "محطة أرصاد جوية", "category": "monitoring",
        "description": "Tracks local rain, wind, and humidity to help time your harvests.",
        "price": 1200.00, "currency": "EGP", "stock_status": "pre_order", "stock_qty": None,
        "tags": ["weather", "data", "humidity", "rain"], "estimated_restock": "Ships in 10 days",
    },
    {
        "id": "AGR-008", "name": "Greenhouse UV Film",
        "name_ar": "غطاء بلاستيك للصوبات الزراعية", "category": "infrastructure",
        "description": "Heavy-duty UV protected plastic roll (50m) for greenhouse shielding.",
        "price": 950.00, "currency": "EGP", "stock_status": "in_stock", "stock_qty": 40,
        "tags": ["greenhouse", "plastic", "protection", "farming"], "estimated_restock": None,
    },
]


async def _enable_pgvector(session: AsyncSession) -> None:
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    await session.commit()


async def _seed_products(session: AsyncSession) -> None:
    result = await session.execute(select(func.count()).select_from(ProductRow))
    if result.scalar_one() > 0:
        return
    for data in _SEED_PRODUCTS:
        session.add(ProductRow(**data))
    await session.commit()
    print(f"[DB] Seeded {len(_SEED_PRODUCTS)} products.")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        await _enable_pgvector(session)
        await _seed_products(session)

    print("[DB] PostgreSQL schema ready.")
