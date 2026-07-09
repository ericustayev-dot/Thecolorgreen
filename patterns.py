"""Looks at your own logged history.csv and reports what price tended to do
AFTER past sentiment readings, per ticker. This is descriptive pattern-matching
on a small personal dataset, NOT a forecast or trading signal - with only a
few weeks of twice-daily data, sample sizes are far too small to predict
anything reliably. Treat this as "what happened last time," not "what will
happen next time." Run with: python patterns.py"""

import csv
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.csv")
MIN_SAMPLES = 3


def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE) as f:
        return list(csv.DictReader(f))


def group_by_ticker(rows: list[dict]) -> dict:
    by_ticker = defaultdict(list)
    for row in rows:
        by_ticker[row["ticker"]].append(row)
    return by_ticker


def analyze_ticker(rows: list[dict]) -> dict:
    """rows must be in chronological order. For each reading, looks at the
    NEXT reading's price change to see what tended to follow."""
    buckets = defaultdict(list)  # sentiment_label -> list of next-period change_pct

    for current, nxt in zip(rows, rows[1:]):
        buckets[current["sentiment_label"]].append(float(nxt["change_pct"]))

    summary = {}
    for label, changes in buckets.items():
        up = sum(1 for c in changes if c > 0)
        down = sum(1 for c in changes if c < 0)
        summary[label] = {
            "samples": len(changes),
            "avg_next_change_pct": round(sum(changes) / len(changes), 2),
            "up": up,
            "down": down,
        }
    return summary


def main():
    rows = load_history()
    if not rows:
        print("No history yet - let the tracker run for a while (e.g. via the cron schedule), then check back.")
        return

    print("Historical pattern lookup (from your own logged data, not a prediction)\n")

    for ticker, ticker_rows in group_by_ticker(rows).items():
        print(f"=== {ticker} ({len(ticker_rows)} readings logged) ===")
        summary = analyze_ticker(ticker_rows)

        if not summary:
            print("  Not enough readings yet to compare before/after.\n")
            continue

        for label in ("positive", "neutral", "negative"):
            stats = summary.get(label)
            if not stats:
                continue
            if stats["samples"] < MIN_SAMPLES:
                print(f"  After {label} sentiment: only {stats['samples']} sample(s) so far - too few to say anything.")
                continue
            print(
                f"  After {label} sentiment: next reading moved "
                f"{stats['avg_next_change_pct']:+.2f}% on average "
                f"({stats['up']} up / {stats['down']} down, n={stats['samples']})"
            )
        print()


if __name__ == "__main__":
    main()
