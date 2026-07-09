"""Local web dashboard for the stock tracker, built with Streamlit.
Run with: streamlit run dashboard.py
It will open automatically in your browser at http://localhost:8501"""

import json
import os

import pandas as pd
import streamlit as st
from streamlit_searchbox import st_searchbox

from main import load_watchlist, load_commodities, WATCHLIST_FILE, COMMODITIES_FILE, HISTORY_FILE, COMMODITIES_HISTORY_FILE, WORLD_NEWS_LOG_FILE
from report import build_stock_report, build_commodity_report, build_world_news_report
from search import search_tickers
from movers import DAILY_MOVERS_FILE, classify_cap, compute_daily_movers

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_FILE = os.path.join(BASE_DIR, "logo_transparent.png")
FAVICON_FILE = os.path.join(BASE_DIR, "favicon.png")

st.set_page_config(page_title="The Color Green", page_icon=FAVICON_FILE, layout="wide")

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
    <style>
    .block-container {
        padding-top: 2rem !important;
        max-width: 1200px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    h1 { letter-spacing: -0.5px; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 10px;
    }
    div[data-testid="stButton"] button {
        border-radius: 6px;
    }
    div[data-testid="stImage"] {
        margin-left: auto;
        margin-right: auto;
        width: fit-content;
    }
    div[data-testid="stImage"] img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    hr { margin: 2.2rem 0 1.4rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


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


CAP_LEVELS = {"mega": 4, "large": 3, "mid": 2, "small": 1}


def cap_indicator(cap: str, color: str = "green") -> str:
    filled = CAP_LEVELS.get(cap, 1)
    return "".join(f":{color}[$]" if i < filled else ":gray[$]" for i in range(4))


def render_stock_card(ticker: str) -> None:
    report = cached_stock_report(ticker)
    price = report["price"]
    sentiment = report["sentiment"]
    bullish = report["bullish_driver"]
    bearish = report["bearish_driver"]
    groups = report["headline_groups"]
    cap = classify_cap(price["market_cap"])

    st.subheader(f"{price['name']} ({price['ticker']})")
    st.metric("Price", f"${price['price']}", f"{price['change_pct']:+.2f}%")
    st.markdown(f"{cap_indicator(cap)} {cap.capitalize()} cap")

    if price["analyst_target_mean"]:
        st.write(
            f"Analyst 12-mo target: **\\${price['analyst_target_mean']:.2f}** "
            f"(\\${price['analyst_target_low']:.2f}-\\${price['analyst_target_high']:.2f})"
        )
        st.caption(f"{price['analyst_count']} analysts · {price['analyst_recommendation']} · not a prediction, just published Wall Street consensus")

    st.write(f"Sentiment: **{sentiment['label']}** ({sentiment['average_score']:+.3f})")
    if bullish:
        st.success(f"Bullish driver: [{bullish['title']}]({bullish['link']}) ({bullish['source']})", icon=":material/trending_up:")
    if bearish:
        st.error(f"Bearish driver: [{bearish['title']}]({bearish['link']}) ({bearish['source']})", icon=":material/trending_down:")

    with st.expander(f"Positive headlines ({len(groups['positive'])})"):
        for h in groups["positive"]:
            st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")
    with st.expander(f"Negative headlines ({len(groups['negative'])})"):
        for h in groups["negative"]:
            st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")


def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


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
        if driver_title:
            box = st.success if direction == "bullish" else st.error
            icon = ":material/trending_up:" if direction == "bullish" else ":material/trending_down:"
            box(f"[{driver_title}]({driver_link}) ({driver_source})", icon=icon)

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


def remove_from_watchlist(ticker: str) -> None:
    remaining = [t for t in load_watchlist(WATCHLIST_FILE) if t != ticker]
    with open(WATCHLIST_FILE, "w") as f:
        f.write("\n".join(remaining) + ("\n" if remaining else ""))


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


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

logo_left, logo_mid, logo_right = st.columns([1, 1, 1])
with logo_mid:
    st.image(LOGO_FILE, width="stretch")
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

# ---- Watchlist ----
st.header(":material/visibility: Watchlist")
tickers = load_watchlist(WATCHLIST_FILE)
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
    progress.progress(min(1.0, ((row_num + 1) * 4) / len(tickers)), text=f"Loaded {min((row_num + 1) * 4, len(tickers))}/{len(tickers)}")

progress.empty()

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

st.divider()

# ---- World news ----
st.header(":material/public: World news")
st.caption("Category notes are general historical patterns for this TYPE of event, not a prediction of what happens this time.")
try:
    for h in cached_world_news():
        st.markdown(f"**[{h['title']}]({h['link']})** ({h['source']})")
        st.caption(f"{h['category']}: {h['explanation']}")
except Exception as e:
    st.error(f"Failed to load world news: {e}")

st.divider()

# ---- History ----
st.header(":material/history: History")
history_df = load_csv(HISTORY_FILE)
if history_df.empty:
    st.info("No logged history yet. History builds up as the tracker runs over time (e.g. via the cron schedule).")
else:
    tab1, tab2 = st.tabs(["Price over time", "Sentiment over time"])
    with tab1:
        price_pivot = history_df.pivot_table(index="timestamp", columns="ticker", values="price")
        st.line_chart(price_pivot)
    with tab2:
        sentiment_pivot = history_df.pivot_table(index="timestamp", columns="ticker", values="sentiment_score")
        st.line_chart(sentiment_pivot)

    st.subheader("Raw log")
    st.dataframe(history_df.sort_values("timestamp", ascending=False), width="stretch")

commodities_df = load_csv(COMMODITIES_HISTORY_FILE)
if not commodities_df.empty:
    st.subheader("Gold & silver history")
    commodity_pivot = commodities_df.pivot_table(index="timestamp", columns="label", values="price")
    st.line_chart(commodity_pivot)
