"""Computes a daily list of the most bullish and bearish stocks from a
diversified universe of tickers (mixing mega/large/mid/small cap).

Runs once per calendar day (whichever scheduled run - open or close - hits
first), not on every page load, since scanning ~100 tickers is too slow for
a live dashboard request. Results are cached to daily_movers.json and the
dashboard just reads that file.

Day-to-day stability: a ticker that was on yesterday's list stays if it's
still bullish (or still bearish) today, rather than the whole list
reshuffling from scratch each day. Only tickers that flipped out of that
direction get replaced."""

import json
import os
from datetime import date

from report import build_stock_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UNIVERSE_FILE = os.path.join(BASE_DIR, "universe.txt")
DAILY_MOVERS_FILE = os.path.join(BASE_DIR, "daily_movers.json")

CAP_BUCKETS = [
    ("mega", 200_000_000_000),
    ("large", 10_000_000_000),
    ("mid", 2_000_000_000),
    ("small", 0),
]
CAP_ORDER = ["mega", "large", "mid", "small"]


def classify_cap(market_cap) -> str:
    if not market_cap:
        return "small"
    for label, floor in CAP_BUCKETS:
        if market_cap >= floor:
            return label
    return "small"


def load_universe() -> list[str]:
    with open(UNIVERSE_FILE) as f:
        return [line.strip().upper() for line in f if line.strip()]


def load_previous() -> dict:
    if not os.path.exists(DAILY_MOVERS_FILE):
        return {}
    with open(DAILY_MOVERS_FILE) as f:
        return json.load(f)


def save_movers(data: dict) -> None:
    with open(DAILY_MOVERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def scan_universe(tickers: list[str]) -> list[dict]:
    scanned = []
    for ticker in tickers:
        try:
            report = build_stock_report(ticker)
            price = report["price"]
            bullish = report["bullish_driver"]
            bearish = report["bearish_driver"]
            scanned.append({
                "ticker": price["ticker"],
                "name": price["name"],
                "price": price["price"],
                "change_pct": price["change_pct"],
                "sentiment_score": report["sentiment"]["average_score"],
                "sentiment_label": report["sentiment"]["label"],
                "cap": classify_cap(price["market_cap"]),
                "analyst_target_mean": price["analyst_target_mean"],
                "analyst_target_low": price["analyst_target_low"],
                "analyst_target_high": price["analyst_target_high"],
                "analyst_count": price["analyst_count"],
                "analyst_recommendation": price["analyst_recommendation"],
                "bullish_driver": bullish["title"] if bullish else None,
                "bullish_driver_source": bullish["source"] if bullish else None,
                "bearish_driver": bearish["title"] if bearish else None,
                "bearish_driver_source": bearish["source"] if bearish else None,
                "positive_headlines": len(report["headline_groups"]["positive"]),
                "negative_headlines": len(report["headline_groups"]["negative"]),
            })
        except Exception:
            continue
    return scanned


def pick_diverse_top(candidates: list[dict], count: int, direction: str) -> list[dict]:
    """Picks top `count` candidates by sentiment score, guaranteeing at least
    one from each cap bucket (mega/large/mid/small) before filling the rest
    purely by score."""
    ranked = sorted(candidates, key=lambda c: c["sentiment_score"], reverse=(direction == "bullish"))
    picked, picked_tickers = [], set()

    for bucket in CAP_ORDER:
        if len(picked) >= count:
            break
        bucket_candidates = [c for c in ranked if c["cap"] == bucket]
        if bucket_candidates:
            top = bucket_candidates[0]
            picked.append(top)
            picked_tickers.add(top["ticker"])

    for c in ranked:
        if len(picked) >= count:
            break
        if c["ticker"] not in picked_tickers:
            picked.append(c)
            picked_tickers.add(c["ticker"])

    return picked[:count]


def apply_stickiness(today_candidates: list[dict], previous_list: list[dict], count: int, direction: str) -> list[dict]:
    """Keeps yesterday's picks that are still in the same direction today;
    fills any open slots with fresh top picks (cap-diverse)."""
    today_by_ticker = {c["ticker"]: c for c in today_candidates}
    still_qualifies = (lambda s: s > 0.05) if direction == "bullish" else (lambda s: s < -0.05)

    kept, kept_tickers = [], set()
    for prev in previous_list or []:
        if len(kept) >= count:
            break
        current = today_by_ticker.get(prev["ticker"])
        if current and still_qualifies(current["sentiment_score"]):
            kept.append(current)
            kept_tickers.add(current["ticker"])

    if len(kept) < count:
        remaining = [c for c in today_candidates if c["ticker"] not in kept_tickers]
        kept.extend(pick_diverse_top(remaining, count - len(kept), direction))

    return kept[:count]


def compute_daily_movers(force: bool = False) -> dict:
    previous = load_previous()
    today = date.today().isoformat()

    if not force and previous.get("date") == today:
        return previous

    scanned = scan_universe(load_universe())
    bullish_candidates = [c for c in scanned if c["sentiment_score"] > 0.05]
    bearish_candidates = [c for c in scanned if c["sentiment_score"] < -0.05]

    result = {
        "date": today,
        "bullish": apply_stickiness(bullish_candidates, previous.get("bullish", []), 10, "bullish"),
        "bearish": apply_stickiness(bearish_candidates, previous.get("bearish", []), 10, "bearish"),
    }
    save_movers(result)
    return result


if __name__ == "__main__":
    result = compute_daily_movers(force=True)
    print(f"Date: {result['date']}")
    print(f"\nBullish ({len(result['bullish'])}):")
    for c in result["bullish"]:
        print(f"  {c['ticker']:6} ({c['cap']:5}) {c['sentiment_score']:+.3f}  {c['name']}")
    print(f"\nBearish ({len(result['bearish'])}):")
    for c in result["bearish"]:
        print(f"  {c['ticker']:6} ({c['cap']:5}) {c['sentiment_score']:+.3f}  {c['name']}")
