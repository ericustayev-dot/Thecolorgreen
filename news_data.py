"""Fetch recent news headlines for a stock ticker via Yahoo Finance's RSS feed."""

import feedparser

from sources import filter_reliable

RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"


def get_recent_headlines(ticker: str, limit: int = 5) -> list[dict]:
    feed = feedparser.parse(RSS_URL.format(ticker=ticker))

    headlines = []
    for entry in feed.entries:
        headlines.append({
            "title": entry.get("title", ""),
            "published": entry.get("published", ""),
            "link": entry.get("link", ""),
        })

    return filter_reliable(headlines)[:limit]


if __name__ == "__main__":
    for h in get_recent_headlines("AAPL"):
        print(f"- {h['title']} ({h['published']})")
