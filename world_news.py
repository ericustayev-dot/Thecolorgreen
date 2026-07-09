"""Fetch top world-news headlines (BBC World, free and reliable) so market
moves can be cross-referenced against major geopolitical events later."""

import feedparser

from sources import filter_reliable

RSS_URL = "http://feeds.bbci.co.uk/news/world/rss.xml"


def get_world_headlines(limit: int = 5) -> list[dict]:
    feed = feedparser.parse(RSS_URL)

    headlines = []
    for entry in feed.entries:
        headlines.append({
            "title": entry.get("title", ""),
            "published": entry.get("published", ""),
            "link": entry.get("link", ""),
        })

    return filter_reliable(headlines)[:limit]


if __name__ == "__main__":
    for h in get_world_headlines():
        print(f"- {h['title']} ({h['source']})")
