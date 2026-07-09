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
    with st.container(border=True):
        if st.button(f"{m['ticker']} · {m['name']}", key=f"mover_{m['ticker']}"):
            st.session_state.selected_mover = m["ticker"]

        st.markdown(f"{cap_indicator(m['cap'], color)} :{color}[{m['cap'].capitalize()} cap]")
        st.write(f"${m['price']} ({m['change_pct']:+.2f}%) · sentiment {m['sentiment_score']:+.3f}")

        if m.get("analyst_target_mean"):
            st.caption(
                f"Analyst target: \\${m['analyst_target_mean']:.2f} "
                f"(\\${m['analyst_target_low']:.2f}-\\${m['analyst_target_high']:.2f}) · "
                f"{m['analyst_count']} analysts · {m['analyst_recommendation']}"
            )

        driver_title = m.get(f"{direction}_driver")
        driver_source = m.get(f"{direction}_driver_source")
        driver_link = m.get(f"{direction}_driver_link")
        driver_category = m.get(f"{direction}_driver_category")
        driver_explanation = m.get(f"{direction}_driver_explanation")
        if driver_title:
            box = st.success if direction == "bullish" else st.error
            icon = ":material/trending_up:" if direction == "bullish" else ":material/trending_down:"
            box(f"[{driver_title}]({driver_link}) ({driver_source})", icon=icon)
            if driver_category:
                st.caption(f"{driver_category}: {driver_explanation}")

        st.caption(f"{m['positive_headlines']} positive · {m['negative_headlines']} negative headlines")


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
