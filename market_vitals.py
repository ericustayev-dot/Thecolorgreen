"""Pairs commodity price moves (gold, silver, oil) with the world-news
headlines that were logged in the same scheduled run, so instead of a canned
"this type of event usually does X" statement, you see the actual observed
price action alongside whatever was in the news at that same time.

Important honesty note: this shows correlation (things logged around the
same time), not proven causation. Plenty else moves these prices too -
supply/demand, currency swings, seasonal effects - that has nothing to do
with the paired headline."""

import csv
import os

from main import COMMODITIES_HISTORY_FILE, WORLD_NEWS_LOG_FILE

# Only these categories (from news_context.py) are plausible drivers of
# commodity prices - pairing a gold move with an unrelated "leadership
# change" headline wouldn't be a useful or honest correlation.
COMMODITY_RELEVANT_CATEGORIES = {
    "Geopolitical conflict",
    "Central bank / monetary policy",
    "Trade / sanctions",
}


def _read_csv(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def _session_key(row: dict) -> str:
    return row["timestamp"][:10] + "|" + row["session"]


def get_latest_vitals() -> dict:
    """Returns the most recent logged session's commodity moves, paired with
    any relevant world-news headlines logged in that same session."""
    commodity_rows = _read_csv(COMMODITIES_HISTORY_FILE)
    news_rows = _read_csv(WORLD_NEWS_LOG_FILE)

    if not commodity_rows:
        return {}

    # Pick the session key from the row with the latest actual timestamp -
    # comparing session KEYS alphabetically would wrongly rank "open" above
    # "manual"/"close" regardless of when each was actually logged.
    latest_row = max(commodity_rows, key=lambda r: r["timestamp"])
    latest_key = _session_key(latest_row)
    latest_commodities = [r for r in commodity_rows if _session_key(r) == latest_key]
    matching_news = [
        r for r in news_rows
        if _session_key(r) == latest_key and r["category"] in COMMODITY_RELEVANT_CATEGORIES
    ]

    return {
        "session_key": latest_key,
        "commodities": latest_commodities,
        "headlines": matching_news,
    }
