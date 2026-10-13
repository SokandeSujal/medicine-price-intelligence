"""FastAPI application for the Indian Medicine Price Intelligence dashboard."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query as QueryParam
from fastapi.middleware.cors import CORSMiddleware
from psycopg import OperationalError

try:
    from . import queries
    from .db import close_pool, fetch_all, fetch_one, open_pool
    from .stock import stock_quote
except ImportError:  # supports `uvicorn main:app` from backend/
    import queries
    from db import close_pool, fetch_all, fetch_one, open_pool
    from stock import stock_quote


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await open_pool()
    except Exception as exc:
        print(f"Database connection will retry on first request: {exc}")
    yield
    await close_pool()


app = FastAPI(title="Indian Medicine Price Intelligence API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def one(q: queries.Query, params: tuple = ()):
    try:
        return await fetch_one(q.sql, params)
    except (OperationalError, RuntimeError) as exc:
        raise HTTPException(503, f"Supabase database unavailable: {exc}") from exc


async def many(q: queries.Query, params: tuple = ()):
    try:
        return await fetch_all(q.sql, params)
    except (OperationalError, RuntimeError) as exc:
        raise HTTPException(503, f"Supabase database unavailable: {exc}") from exc


@app.get("/api/health")
async def health():
    try:
        row = await one(queries.OVERVIEW_KPIS)
        return {"status": "ok", "database": "supabase", "rows": row["total_medicines"]}
    except HTTPException as exc:
        return {"status": "degraded", "database": "supabase", "detail": exc.detail}


@app.get("/api/overview")
async def overview():
    return await one(queries.OVERVIEW_KPIS)


@app.get("/api/price-distribution")
async def price_distribution():
    return await many(queries.PRICE_HISTOGRAM)


@app.get("/api/manufacturers/top")
async def top_manufacturers(limit: int = QueryParam(10, ge=1, le=30)):
    return await many(queries.TOP_MANUFACTURERS, (limit,))


@app.get("/api/manufacturers/price-ranking")
async def price_ranking(order: str = "desc", min_products: int = 30, limit: int = 10):
    if order not in {"asc", "desc"}:
        raise HTTPException(422, "order must be asc or desc")
    return await many(queries.MANUFACTURER_PRICE_RANKING, (min_products, order, order, limit))


@app.get("/api/subcategories")
async def subcategories(limit: int = QueryParam(10, ge=1, le=30)):
    return await many(queries.TOP_SUBCATEGORIES, (limit,))


@app.get("/api/medicines/search")
async def search_medicines(q: str = QueryParam(..., min_length=2, max_length=80), limit: int = 12):
    clean = q.strip()
    return await many(queries.SEARCH_MEDICINES, (f"%{clean}%", f"{clean}%", min(limit, 25)))


@app.get("/api/medicines/{medicine_id}")
async def medicine_detail(medicine_id: int):
    result = await one(queries.MEDICINE_DETAIL, (medicine_id,))
    if not result:
        raise HTTPException(404, "Medicine not found")
    return result


@app.get("/api/medicines/{medicine_id}/alternatives")
async def alternatives(medicine_id: int, limit: int = 12):
    return await many(queries.CHEAPER_ALTERNATIVES, (medicine_id, min(limit, 30)))


@app.get("/api/manufacturers")
async def manufacturers():
    return await many(queries.LIST_MANUFACTURERS)


@app.get("/api/manufacturers/{manufacturer_id}")
async def manufacturer_insight(manufacturer_id: int):
    result = await one(queries.MANUFACTURER_INSIGHT, (manufacturer_id, manufacturer_id))
    if not result or result["name"] is None:
        raise HTTPException(404, "Manufacturer not found")
    return result


@app.get("/api/manufacturers/{manufacturer_id}/stock")
async def manufacturer_stock(manufacturer_id: int):
    manufacturer = await one(queries.MANUFACTURER_INSIGHT, (manufacturer_id, manufacturer_id))
    if not manufacturer or manufacturer["name"] is None:
        raise HTTPException(404, "Manufacturer not found")
    return await stock_quote(manufacturer["name"])


@app.get("/api/price-gaps")
async def price_gaps(min_brands: int = 5, limit: int = 15):
    return await many(queries.PRICE_GAPS, (min_brands, min(limit, 50)))


@app.get("/api/price-gaps/{salt}")
async def salt_range(salt: str):
    return await many(queries.SALT_PRICE_RANGE, (salt,))


@app.get("/api/safety/overview")
async def safety_overview():
    return await one(queries.SAFETY_OVERVIEW)


@app.get("/api/safety/side-effects")
async def top_side_effects(limit: int = 12):
    return await many(queries.TOP_SIDE_EFFECTS, (min(limit, 30),))


@app.get("/api/analytics/ingredient-complexity")
async def ingredient_complexity():
    return await many(queries.INGREDIENT_PRICE_COMPLEXITY)


@app.get("/api/analytics/manufacturer-positioning")
async def manufacturer_positioning(min_products: int = QueryParam(15, ge=5, le=100)):
    return await many(queries.MANUFACTURER_POSITIONING, (min_products,))


@app.get("/api/analytics/category-price-spread")
async def category_price_spread(limit: int = QueryParam(10, ge=5, le=20)):
    return await many(queries.CATEGORY_PRICE_SPREAD, (limit,))


@app.get("/api/debug/queries")
async def debug_queries():
    return {
        "single_source": "backend/queries.py",
        "count": len(queries.ALL_QUERIES),
        "queries": [q.__dict__ for q in queries.ALL_QUERIES.values()],
        "source": Path(queries.__file__).read_text(encoding="utf-8"),
    }
