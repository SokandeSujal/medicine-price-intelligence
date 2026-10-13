"""Cached market quote integration using yfinance."""

import asyncio
import time
from typing import Any

import yfinance as yf

TICKERS = {
    "Sun Pharmaceutical Industries Ltd": "SUNPHARMA.NS",
    "Cipla Ltd": "CIPLA.NS",
    "Dr Reddy's Laboratories Ltd": "DRREDDY.NS",
    "Glenmark Pharmaceuticals Ltd": "GLENMARK.NS",
    "Lupin Ltd": "LUPIN.NS",
    "Mankind Pharma Ltd": "MANKIND.NS",
    "Torrent Pharmaceuticals Ltd": "TORNTPHARM.NS",
    "Abbott": "ABBOTINDIA.NS",
    "Pfizer Ltd": "PFIZER.NS",
    "Novartis India Ltd": "NOVARTIND.NS",
}

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
CACHE_SECONDS = 900


def _download(ticker: str) -> dict[str, Any]:
    quote = yf.Ticker(ticker)
    history = quote.history(period="5d", interval="1d", auto_adjust=False)
    if history.empty:
        raise RuntimeError("No recent market quote returned")
    last = history.iloc[-1]
    previous = history.iloc[-2] if len(history) > 1 else last
    price = float(last["Close"])
    previous_close = float(previous["Close"])
    change_pct = ((price - previous_close) / previous_close * 100) if previous_close else 0
    return {
        "ticker": ticker,
        "price": round(price, 2),
        "currency": "INR",
        "change_pct": round(change_pct, 2),
        "market_date": str(history.index[-1].date()),
        "source": "Yahoo Finance via yfinance",
        "is_cached": False,
    }


async def stock_quote(manufacturer: str) -> dict[str, Any]:
    ticker = TICKERS.get(manufacturer)
    if not ticker:
        return {"available": False, "reason": "Not publicly listed or ticker not mapped"}
    now = time.time()
    cached = _cache.get(ticker)
    if cached and now - cached[0] < CACHE_SECONDS:
        return {"available": True, **cached[1], "is_cached": True}
    try:
        result = await asyncio.to_thread(_download, ticker)
        _cache[ticker] = (now, result)
        return {"available": True, **result}
    except Exception as exc:
        if cached:
            return {"available": True, **cached[1], "is_cached": True, "warning": str(exc)}
        return {"available": False, "reason": "Market data temporarily unavailable", "ticker": ticker}
