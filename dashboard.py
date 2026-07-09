"""Local web dashboard for the stock tracker, built with Streamlit.
Run with: streamlit run dashboard.py
It will open automatically in your browser at http://localhost:8501"""

import os

import pandas as pd
import streamlit as st

from main import load_watchlist, load_commodities, WATCHLIST_FILE, COMMODITIES_FILE, HISTORY_FILE, COMMODITIES_HISTORY_FILE, WORLD_NEWS_LOG_FILE
from report import build_stock_report, build_commodity_report, build_world_news_report

st.set_page_config(page_title="Stock Tracker", layout="wide")


@st.cache_data(ttl=300)
def cached_stock_report(ticker: str) -> dict:
    return build_stock_report(ticker)


@st.cache_data(ttl=300)
def cached_commodity_report(ticker: str, label: str) -> dict:
    return build_commodity_report(ticker, label)


@st.cache_data(ttl=300)
def cached_world_news() -> list:
    return build_world_news_report(limit=5)


def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


st.title("Stock tracker dashboard")
st.caption("Live snapshot + logged history. Data refreshes at most every 5 minutes.")

if st.button("Refresh now"):
    st.cache_data.clear()

def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


st.header("Watchlist")
tickers = load_watchlist(WATCHLIST_FILE)
progress = st.progress(0.0, text="Loading watchlist...")

for row_num, row in enumerate(chunked(tickers, 4)):
    cols = st.columns(4)
    for col, ticker in zip(cols, row):
        try:
            report = cached_stock_report(ticker)
            price = report["price"]
            sentiment = report["sentiment"]
            bullish = report["bullish_driver"]
            bearish = report["bearish_driver"]
            groups = report["headline_groups"]

            with col:
                st.subheader(f"{price['name']} ({price['ticker']})")
                st.metric("Price", f"${price['price']}", f"{price['change_pct']:+.2f}%")

                if price["analyst_target_mean"]:
                    st.write(
                        f"Analyst 12-mo target: **\\${price['analyst_target_mean']:.2f}** "
                        f"(\\${price['analyst_target_low']:.2f}-\\${price['analyst_target_high']:.2f})"
                    )
                    st.caption(f"{price['analyst_count']} analysts · {price['analyst_recommendation']} · not a prediction, just published Wall Street consensus")

                st.write(f"Sentiment: **{sentiment['label']}** ({sentiment['average_score']:+.3f})")
                if bullish:
                    st.success(f"Bullish driver: {bullish['title']}", icon=":material/trending_up:")
                if bearish:
                    st.error(f"Bearish driver: {bearish['title']}", icon=":material/trending_down:")

                with st.expander(f"Positive headlines ({len(groups['positive'])})"):
                    for h in groups["positive"]:
                        st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")
                with st.expander(f"Negative headlines ({len(groups['negative'])})"):
                    for h in groups["negative"]:
                        st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")
        except Exception as e:
            with col:
                st.error(f"{ticker}: failed to load ({e})")
    progress.progress(min(1.0, ((row_num + 1) * 4) / len(tickers)), text=f"Loaded {min((row_num + 1) * 4, len(tickers))}/{len(tickers)}")

progress.empty()

st.header("Gold & silver")
commodity_cols = st.columns(len(load_commodities(COMMODITIES_FILE)))
for col, (ticker, label) in zip(commodity_cols, load_commodities(COMMODITIES_FILE)):
    try:
        price = cached_commodity_report(ticker, label)["price"]
        with col:
            st.metric(label, f"${price['price']}", f"{price['change_pct']:+.2f}%")
    except Exception as e:
        with col:
            st.error(f"{label}: failed to load ({e})")

st.header("World news")
st.caption("Category notes are general historical patterns for this TYPE of event, not a prediction of what happens this time.")
try:
    for h in cached_world_news():
        st.markdown(f"**[{h['title']}]({h['link']})** ({h['source']})")
        st.caption(f"{h['category']}: {h['explanation']}")
except Exception as e:
    st.error(f"Failed to load world news: {e}")

st.header("History")
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
