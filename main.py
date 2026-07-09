"""Stock tracker: reads a watchlist, pulls price + news for each ticker,
scores news sentiment, flags a likely catalyst headline, prints a report,
and logs everything to CSV files so trends build up over time (e.g. run
twice daily via cron at market open and close).

Also tracks gold/silver prices and world-news headlines for broader context."""

import csv
import os
import sys
from datetime import datetime, timezone

from report import build_stock_report, build_commodity_report, build_world_news_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.txt")
COMMODITIES_FILE = os.path.join(BASE_DIR, "commodities.txt")
HISTORY_FILE = os.path.join(BASE_DIR, "history.csv")
COMMODITIES_HISTORY_FILE = os.path.join(BASE_DIR, "commodities_history.csv")
WORLD_NEWS_LOG_FILE = os.path.join(BASE_DIR, "world_news_log.csv")

HISTORY_FIELDS = [
    "timestamp", "session", "ticker", "price", "change_pct",
    "sentiment_score", "sentiment_label", "catalyst_headline",
]
COMMODITIES_FIELDS = ["timestamp", "session", "ticker", "label", "price", "change_pct"]
WORLD_NEWS_FIELDS = ["timestamp", "session", "title", "source", "link", "category"]


def load_watchlist(path: str) -> list[str]:
    with open(path) as f:
        return [line.strip().upper() for line in f if line.strip()]


def load_commodities(path: str) -> list[tuple[str, str]]:
    pairs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ticker, label = line.split(",")
            pairs.append((ticker.strip(), label.strip()))
    return pairs


def append_csv_row(path: str, fieldnames: list[str], row: dict) -> None:
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def report_stock(ticker: str, session: str, timestamp: str) -> None:
    report = build_stock_report(ticker)
    price = report["price"]
    headlines = report["headlines"]
    sentiment = report["sentiment"]
    catalyst = report["catalyst"]
    bullish_driver = report["bullish_driver"]
    bearish_driver = report["bearish_driver"]

    print(f"\n=== {price['name']} ({price['ticker']}) [{session}] ===")
    print(f"Price: ${price['price']}  ({price['change']:+.2f}, {price['change_pct']:+.2f}%)")
    if price["market_cap"]:
        print(f"Market cap: ${price['market_cap']:,}")
    if price["pe_ratio"]:
        print(f"P/E ratio: {price['pe_ratio']:.2f}")
    if price["analyst_target_mean"]:
        print(
            f"Analyst 12-mo target: ${price['analyst_target_mean']:.2f} avg "
            f"(range ${price['analyst_target_low']:.2f}-${price['analyst_target_high']:.2f}, "
            f"{price['analyst_count']} analysts, {price['analyst_recommendation']})"
        )

    print(f"News sentiment: {sentiment['label']} (score {sentiment['average_score']})")
    if bullish_driver:
        print(f"Bullish driver: {bullish_driver['title']} [{bullish_driver['source']}] (score {bullish_driver['sentiment_score']:+.3f})")
    if bearish_driver:
        print(f"Bearish driver: {bearish_driver['title']} [{bearish_driver['source']}] (score {bearish_driver['sentiment_score']:+.3f})")

    print("Recent headlines:")
    for h in headlines:
        print(f"  - {h['title']} [{h['source']}]")

    append_csv_row(HISTORY_FILE, HISTORY_FIELDS, {
        "timestamp": timestamp,
        "session": session,
        "ticker": price["ticker"],
        "price": price["price"],
        "change_pct": price["change_pct"],
        "sentiment_score": sentiment["average_score"],
        "sentiment_label": sentiment["label"],
        "catalyst_headline": catalyst["title"] if catalyst else "",
    })


def report_commodity(ticker: str, label: str, session: str, timestamp: str) -> None:
    price = build_commodity_report(ticker, label)["price"]

    print(f"\n=== {label} ({ticker}) [{session}] ===")
    print(f"Price: ${price['price']}  ({price['change']:+.2f}, {price['change_pct']:+.2f}%)")

    append_csv_row(COMMODITIES_HISTORY_FILE, COMMODITIES_FIELDS, {
        "timestamp": timestamp,
        "session": session,
        "ticker": ticker,
        "label": label,
        "price": price["price"],
        "change_pct": price["change_pct"],
    })


def report_world_news(session: str, timestamp: str) -> None:
    headlines = build_world_news_report(limit=5)

    print(f"\n=== World news [{session}] ===")
    for h in headlines:
        print(f"  - {h['title']} [{h['source']}]")
        print(f"    {h['link']}")
        print(f"    ({h['category']}) {h['explanation']}")
        append_csv_row(WORLD_NEWS_LOG_FILE, WORLD_NEWS_FIELDS, {
            "timestamp": timestamp,
            "session": session,
            "title": h["title"],
            "source": h["source"],
            "link": h["link"],
            "category": h["category"],
        })


def main():
    # Optional first argument labels the run, e.g. "open" or "close" (set by cron).
    session = sys.argv[1] if len(sys.argv) > 1 else "manual"
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        report_world_news(session, timestamp)
    except Exception as e:
        print(f"\n=== World news ===\nFailed to fetch: {e}")

    for ticker in load_watchlist(WATCHLIST_FILE):
        try:
            report_stock(ticker, session, timestamp)
        except Exception as e:
            print(f"\n=== {ticker} ===\nFailed to fetch data: {e}")

    for ticker, label in load_commodities(COMMODITIES_FILE):
        try:
            report_commodity(ticker, label, session, timestamp)
        except Exception as e:
            print(f"\n=== {label} ({ticker}) ===\nFailed to fetch data: {e}")


if __name__ == "__main__":
    main()
