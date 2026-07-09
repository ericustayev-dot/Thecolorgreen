"""Shared render helpers used across multiple pages (Home, Watchlist)."""

import streamlit as st

from main import load_watchlist, WATCHLIST_FILE
from movers import classify_cap
from cached import cached_stock_report

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
        st.caption(f"{bullish['category']}: {bullish['explanation']}")
    if bearish:
        st.error(f"Bearish driver: [{bearish['title']}]({bearish['link']}) ({bearish['source']})", icon=":material/trending_down:")
        st.caption(f"{bearish['category']}: {bearish['explanation']}")

    with st.expander(f"Positive headlines ({len(groups['positive'])})"):
        for h in groups["positive"]:
            st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")
            st.caption(f"{h['category']}: {h['explanation']}")
    with st.expander(f"Negative headlines ({len(groups['negative'])})"):
        for h in groups["negative"]:
            st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")
            st.caption(f"{h['category']}: {h['explanation']}")


def remove_from_watchlist(ticker: str) -> None:
    remaining = [t for t in load_watchlist(WATCHLIST_FILE) if t != ticker]
    with open(WATCHLIST_FILE, "w") as f:
        f.write("\n".join(remaining) + ("\n" if remaining else ""))


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]
