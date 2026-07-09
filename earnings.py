"""Fetches upcoming and most recent earnings info for a ticker via yfinance.
Dates and results are as reported/scheduled by the company - not predictions
of what a future report will say."""

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf


def _clean(value):
    return None if value is None or pd.isna(value) else float(value)


def get_earnings_summary(ticker: str) -> dict:
    df = yf.Ticker(ticker).earnings_dates
    if df is None or df.empty:
        return {"ticker": ticker.upper(), "next": None, "last": None}

    now = datetime.now(timezone.utc)
    upcoming = df[df.index > now].sort_index()
    past = df[df.index <= now].sort_index(ascending=False)

    next_earnings = None
    if not upcoming.empty:
        row = upcoming.iloc[0]
        next_earnings = {
            "date": upcoming.index[0].isoformat(),
            "eps_estimate": _clean(row.get("EPS Estimate")),
        }

    last_earnings = None
    if not past.empty:
        row = past.iloc[0]
        eps_estimate = _clean(row.get("EPS Estimate"))
        eps_actual = _clean(row.get("Reported EPS"))
        surprise_pct = _clean(row.get("Surprise(%)"))
        last_earnings = {
            "date": past.index[0].isoformat(),
            "eps_estimate": eps_estimate,
            "eps_actual": eps_actual,
            "surprise_pct": surprise_pct,
            "beat": surprise_pct is not None and surprise_pct > 0,
        }

    return {"ticker": ticker.upper(), "next": next_earnings, "last": last_earnings}


if __name__ == "__main__":
    import json
    print(json.dumps(get_earnings_summary("AAPL"), indent=2))
