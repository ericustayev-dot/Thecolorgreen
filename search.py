"""Looks up ticker symbols by company name or symbol, so the dashboard can
search any stock on demand instead of only showing a fixed watchlist."""

import yfinance as yf


def search_tickers(query: str, max_results: int = 8) -> list[dict]:
    if not query.strip():
        return []

    results = yf.Search(query, max_results=max_results).quotes
    return [
        {
            "symbol": r.get("symbol"),
            "name": r.get("longname") or r.get("shortname") or r.get("symbol"),
            "exchange": r.get("exchDisp", ""),
            "type": r.get("typeDisp", ""),
        }
        for r in results
        if r.get("symbol")
    ]
