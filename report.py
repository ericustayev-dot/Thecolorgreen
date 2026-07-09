"""Builds structured report data (price, news, sentiment, catalyst) for a
ticker or commodity. Shared by main.py (CLI/cron) and dashboard.py (UI) so
the two don't duplicate the same fetch-and-combine logic."""

from price_data import get_price_summary
from news_data import get_recent_headlines
from world_news import get_world_headlines
from news_context import explain
from sentiment import (
    score_headlines,
    average_sentiment,
    find_catalyst,
    find_bearish_driver,
    find_bullish_driver,
    split_by_sentiment,
)


def build_stock_report(ticker: str) -> dict:
    price = get_price_summary(ticker)
    headlines = score_headlines(get_recent_headlines(ticker, limit=5))
    sentiment = average_sentiment(headlines)

    return {
        "price": price,
        "headlines": headlines,
        "headline_groups": split_by_sentiment(headlines),
        "sentiment": sentiment,
        "catalyst": find_catalyst(headlines),
        "bearish_driver": find_bearish_driver(headlines),
        "bullish_driver": find_bullish_driver(headlines),
    }


def build_commodity_report(ticker: str, label: str) -> dict:
    return {"price": get_price_summary(ticker), "label": label}


def build_world_news_report(limit: int = 5) -> list:
    headlines = get_world_headlines(limit=limit)
    return [{**h, **explain(h["title"])} for h in headlines]
