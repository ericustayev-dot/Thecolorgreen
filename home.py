"""The Home page content - search, and today's bullish/bearish picks.
Rendered by dashboard.py's navigation router."""

import json
import os

import streamlit as st
from streamlit_searchbox import st_searchbox

from main import load_watchlist, load_commodities, WATCHLIST_FILE, COMMODITIES_FILE
from movers import DAILY_MOVERS_FILE, compute_daily_movers
from cached import cached_search, cached_commodity_report
from components import render_stock_card, cap_indicator


def load_daily_movers() -> dict:
    if not os.path.exists(DAILY_MOVERS_FILE):
        return {}
    with open(DAILY_MOVERS_FILE) as f:
        return json.load(f)


def render_mover_row(m: dict, direction: str) -> None:
    color = "green" if direction == "bullish" else "red"
    price_color = "#2D6B40" if direction == "bullish" else "#A32D2D"
    with st.container(border=True):
        if st.button(m["ticker"], key=f"mover_{m['ticker']}", width="stretch"):
            st.session_state.selected_mover = m["ticker"]
        st.caption(m["name"])
        st.markdown(
            f"<span style='font-size:1.15rem; font-weight:700; color:{price_color};'>${m['price']} ({m['change_pct']:+.2f}%)</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"{cap_indicator(m['cap'], color)} {m['cap'].capitalize()} cap")


def render_mover_detail(ticker: str) -> None:
    st.subheader(f"Details: {ticker}")
    try:
        render_stock_card(ticker)
        current_watchlist = load_watchlist(WATCHLIST_FILE)
        if ticker in current_watchlist:
            st.caption(f"{ticker} is already in your watchlist.")
        elif st.button(f"Add {ticker} to my watchlist", icon=":material/add:", key=f"add_mover_detail_{ticker}"):
            with open(WATCHLIST_FILE, "a") as f:
                f.write(f"{ticker}\n")
            st.success(f"Added {ticker}.")
            st.rerun()
    except Exception as e:
        st.error(f"{ticker}: failed to load ({e})")
    if st.button("Close details", key="close_mover_detail"):
        st.session_state.selected_mover = None
        st.rerun()


def suggest_tickers(searchterm: str) -> list:
    if not searchterm:
        return []
    matches = cached_search(searchterm)
    return [(f"{m['symbol']} - {m['name']} ({m['exchange']}, {m['type']})", m["symbol"]) for m in matches]


# ---- Hero ----
_, refresh_col = st.columns([6, 1])
with refresh_col:
    if st.button("Refresh now", icon=":material/refresh:"):
        st.cache_data.clear()

st.markdown(
    "<p style='text-align:center; color:#2D6B40; margin-top:-0.8rem; "
    "font-family: \"Bebas Neue\", sans-serif; "
    "font-size: 1.6rem; letter-spacing: 1.5px;'>"
    "The intelligence layer for global markets"
    "</p>",
    unsafe_allow_html=True,
)

with st.expander(":material/help: What do these symbols mean?"):
    st.markdown(
        """
- **Ticker** (e.g. `AAPL`) is always the big bold text at the top of a card — the company name is the smaller line underneath it.
- **$$$$ / $$$ / $$ / $** — company size: 4 filled = mega cap, 3 = large cap, 2 = mid cap, 1 = small cap. Gray dollar signs are unfilled.
- **Green** generally means bullish / positive / buy-weighted. **Red** means bearish / negative / no-buy-weighted.
- **Buy-weight scale** (green/red bar in a stock's "Show details") compares its analyst-target upside against its estimated risk — heavier green means a bigger upside for the risk, heavier red means the risk isn't worth the small upside. It's a formula, not investment advice.
- **Sentiment score** ranges from -1 (very negative news) to +1 (very positive news), based on recent headlines.
- **"Show details"** on any stock card reveals the analyst target, buy-weight scale, sentiment, and recent headlines - collapsed by default to keep things easy to scan.
        """
    )

# ---- Search ----
st.header(":material/search: Search any stock")

selected = st_searchbox(
    suggest_tickers,
    placeholder="Start typing a ticker or company name (e.g. MSFT or Microsoft)...",
    key="stock_searchbox",
)

if selected:
    try:
        render_stock_card(selected)
        current_watchlist = load_watchlist(WATCHLIST_FILE)
        if selected in current_watchlist:
            st.caption(f"{selected} is already in your watchlist.")
        elif st.button(f"Add {selected} to my watchlist", icon=":material/add:", key=f"add_{selected}"):
            with open(WATCHLIST_FILE, "a") as f:
                f.write(f"{selected}\n")
            st.success(f"Added {selected}.")
            st.rerun()
    except Exception as e:
        st.error(f"{selected}: failed to load ({e})")

st.divider()

# ---- Today's bullish & bearish ----
movers_header_col, movers_refresh_col = st.columns([5, 1])
with movers_header_col:
    st.header(":material/insights: Today's bullish & bearish stocks")
with movers_refresh_col:
    st.write("")
    if st.button("Recompute now", icon=":material/refresh:", key="recompute_movers"):
        with st.spinner("Scanning ~100 stocks for today's picks (about a minute)..."):
            compute_daily_movers(force=True)
        st.rerun()

movers_data = load_daily_movers()
if not movers_data:
    st.info("Daily picks haven't been computed yet - click \"Recompute now\" above, or wait for the scheduled job to run.")
else:
    st.caption(
        f"As of {movers_data['date']} · mixed across mega/large/mid/small cap · a pick stays on the "
        "list day-to-day while it's still bullish/bearish, only swapped when it flips direction. "
        "This reflects today's news sentiment, not a forecast."
    )

    if "show_all_movers" not in st.session_state:
        st.session_state.show_all_movers = False
    if "selected_mover" not in st.session_state:
        st.session_state.selected_mover = None

    limit = None if st.session_state.show_all_movers else 4
    bull_col, bear_col = st.columns(2)
    with bull_col:
        st.subheader(":material/trending_up: :green[Bullish]")
        for m in movers_data["bullish"][:limit]:
            render_mover_row(m, "bullish")
    with bear_col:
        st.subheader(":material/trending_down: :red[Bearish]")
        for m in movers_data["bearish"][:limit]:
            render_mover_row(m, "bearish")

    if st.button("Show less" if st.session_state.show_all_movers else "See more"):
        st.session_state.show_all_movers = not st.session_state.show_all_movers
        st.rerun()

    if st.session_state.selected_mover:
        render_mover_detail(st.session_state.selected_mover)

st.divider()

# ---- Gold & silver ----
st.header(":material/paid: Gold & silver")
commodity_cols = st.columns(len(load_commodities(COMMODITIES_FILE)))
for col, (ticker, label) in zip(commodity_cols, load_commodities(COMMODITIES_FILE)):
    try:
        price = cached_commodity_report(ticker, label)["price"]
        with col:
            st.metric(label, f"${price['price']}", f"{price['change_pct']:+.2f}%")
    except Exception as e:
        with col:
            st.error(f"{label}: failed to load ({e})")
