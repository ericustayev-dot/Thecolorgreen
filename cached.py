"""Streamlit-cached wrappers around the live data fetchers, shared by every
page in the app. Defining these once here (rather than per-page) means
navigating between pages reuses the same cache instead of re-fetching."""

import streamlit as st

from report import build_stock_report, build_commodity_report, build_world_news_report
from search import search_tickers
from earnings import get_earnings_summary


@st.cache_data(ttl=300)
def cached_stock_report(ticker: str) -> dict:
    return build_stock_report(ticker)


@st.cache_data(ttl=300)
def cached_commodity_report(ticker: str, label: str) -> dict:
    return build_commodity_report(ticker, label)


@st.cache_data(ttl=300)
def cached_world_news() -> list:
    return build_world_news_report(limit=5)


@st.cache_data(ttl=300)
def cached_search(query: str) -> list:
    return search_tickers(query)


@st.cache_data(ttl=3600)
def cached_earnings_summary(ticker: str) -> dict:
    return get_earnings_summary(ticker)
