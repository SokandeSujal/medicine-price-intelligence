"""Supabase PostgreSQL connection pool."""

import asyncio
import os

from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()

_pool: ConnectionPool | None = None
_pool_lock = asyncio.Lock()


def database_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError(
            "DATABASE_URL is missing. Copy the Supabase Postgres connection string "
            "from Project Settings > Database into backend/.env."
        )
    return value


async def open_pool() -> None:
    global _pool
    async with _pool_lock:
        if _pool is not None and not _pool.closed:
            return

        # Build the candidate separately. If Supabase is paused or still waking
        # up, pool.open() can fail and leaves that object permanently closed.
        # Assigning only after a successful open lets later requests retry.
        candidate = ConnectionPool(
            conninfo=database_url(), min_size=1, max_size=8, open=False,
            kwargs={"row_factory": dict_row, "autocommit": True},
        )
        try:
            await asyncio.to_thread(candidate.open, True)
        except Exception:
            await asyncio.to_thread(candidate.close)
            _pool = None
            raise
        _pool = candidate


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await asyncio.to_thread(_pool.close)
        _pool = None


def _fetch_all_sync(query: str, params: tuple) -> list[dict]:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    assert _pool is not None
    with _pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


async def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    if _pool is None or _pool.closed:
        await open_pool()
    return await asyncio.to_thread(_fetch_all_sync, query, params)


async def fetch_one(query: str, params: tuple = ()) -> dict | None:
    rows = await fetch_all(query, params)
    return rows[0] if rows else None
