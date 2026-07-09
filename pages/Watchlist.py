"""Your personal watchlist - full detail card per stock (price, cap size,
analyst target, sentiment, bullish/bearish driver, headlines)."""

import streamlit as st

from main import load_watchlist, WATCHLIST_FILE
from components import render_stock_card, remove_from_watchlist, chunked

st.header(":material/visibility: Watchlist")

if st.button("Refresh now", icon=":material/refresh:"):
    st.cache_data.clear()

tickers = load_watchlist(WATCHLIST_FILE)
if not tickers:
    st.info("Your watchlist is empty - add stocks from the Home page's search bar.")

progress = st.progress(0.0, text="Loading watchlist...")

for row_num, row in enumerate(chunked(tickers, 4)):
    cols = st.columns(4)
    for col, ticker in zip(cols, row):
        with col:
            try:
                render_stock_card(ticker)
                if st.button("Remove from watchlist", icon=":material/delete:", key=f"remove_{ticker}"):
                    remove_from_watchlist(ticker)
                    st.rerun()
            except Exception as e:
                st.error(f"{ticker}: failed to load ({e})")
    if tickers:
        progress.progress(min(1.0, ((row_num + 1) * 4) / len(tickers)), text=f"Loaded {min((row_num + 1) * 4, len(tickers))}/{len(tickers)}")

progress.empty()
