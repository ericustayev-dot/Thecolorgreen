"""Shared render helpers used across multiple pages (Home, Watchlist)."""

import streamlit as st

from main import load_watchlist, WATCHLIST_FILE
from movers import classify_cap
from cached import cached_stock_report
from buy_score import compute_buy_weight

CAP_LEVELS = {"mega": 4, "large": 3, "mid": 2, "small": 1}


def cap_indicator(cap: str, color: str = "green") -> str:
    filled = CAP_LEVELS.get(cap, 1)
    return "".join(f":{color}[$]" if i < filled else ":gray[$]" for i in range(4))


def render_buy_weight(price: dict, cap: str) -> None:
    result = compute_buy_weight(price["price"], price.get("analyst_target_mean"), price.get("beta"), cap)
    if not result:
        return

    buy_pct = result["buy_pct"]
    no_buy_pct = result["no_buy_pct"]
    label_color = "#2D6B40" if buy_pct >= 50 else "#A32D2D"
    label = "Buy-weighted" if buy_pct >= 50 else "No-buy-weighted"

    st.markdown(
        f"""
        <div style="margin: 0.5rem 0;">
            <div style="display:flex; height:16px; border-radius:8px; overflow:hidden; border:1px solid #E5E9E7;">
                <div style="width:{buy_pct}%; background-color:#2D6B40;"></div>
                <div style="width:{no_buy_pct}%; background-color:#A32D2D;"></div>
            </div>
            <p style="text-align:center; font-weight:600; color:{label_color}; margin-top:0.4rem; margin-bottom:0;">
                {label}: {buy_pct}% buy / {no_buy_pct}% no-buy
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    beta_note = " (estimated, no beta on file)" if result["used_default_beta"] else ""
    st.caption(
        f"~{result['upside_pct']:+.1f}% upside to analyst target vs ~{result['volatility_pct']:.0f}% "
        f"estimated risk{beta_note} · a quantitative reward-vs-risk formula, not investment advice."
    )


def render_ticker_header(ticker: str, name: str, price: float, change_pct: float) -> None:
    """Big, bold ticker-forward header - the ticker is the primary thing a
    user scans for, so it leads; everything else is secondary."""
    price_color = "#2D6B40" if change_pct >= 0 else "#A32D2D"
    st.markdown(
        f"""
        <div style="line-height:1.1; margin-bottom:0.1rem;">
            <span style="font-family:'Bebas Neue', sans-serif; font-size:2.2rem; letter-spacing:1px;">{ticker}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(name)
    st.markdown(
        f"<span style='font-size:1.4rem; font-weight:700;'>${price:,.2f}</span> "
        f"<span style='font-size:1.05rem; font-weight:700; color:{price_color};'>({change_pct:+.2f}%)</span>",
        unsafe_allow_html=True,
    )


def render_stock_card(ticker: str) -> None:
    report = cached_stock_report(ticker)
    price = report["price"]
    sentiment = report["sentiment"]
    bullish = report["bullish_driver"]
    bearish = report["bearish_driver"]
    groups = report["headline_groups"]
    cap = classify_cap(price["market_cap"])

    render_ticker_header(price["ticker"], price["name"], price["price"], price["change_pct"])
    st.markdown(f"{cap_indicator(cap)} {cap.capitalize()} cap")

    with st.expander("Show details"):
        if price["analyst_target_mean"]:
            st.write(
                f"Analyst 12-mo target: **\\${price['analyst_target_mean']:.2f}** "
                f"(\\${price['analyst_target_low']:.2f}-\\${price['analyst_target_high']:.2f})"
            )
            st.caption(f"{price['analyst_count']} analysts · {price['analyst_recommendation']} · not a prediction, just published Wall Street consensus")
            render_buy_weight(price, cap)

        st.write(f"Sentiment: **{sentiment['label']}** ({sentiment['average_score']:+.3f})")
        if bullish:
            st.success(f"Bullish driver: [{bullish['title']}]({bullish['link']}) ({bullish['source']})", icon=":material/trending_up:")
            st.caption(f"{bullish['category']}: {bullish['explanation']}")
        if bearish:
            st.error(f"Bearish driver: [{bearish['title']}]({bearish['link']}) ({bearish['source']})", icon=":material/trending_down:")
            st.caption(f"{bearish['category']}: {bearish['explanation']}")

        st.markdown(f"**Positive headlines ({len(groups['positive'])})**")
        if groups["positive"]:
            for h in groups["positive"]:
                st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")
                st.caption(f"{h['category']}: {h['explanation']}")
        else:
            st.caption("None recent.")

        st.markdown(f"**Negative headlines ({len(groups['negative'])})**")
        if groups["negative"]:
            for h in groups["negative"]:
                st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")
                st.caption(f"{h['category']}: {h['explanation']}")
        else:
            st.caption("None recent.")


def remove_from_watchlist(ticker: str) -> None:
    remaining = [t for t in load_watchlist(WATCHLIST_FILE) if t != ticker]
    with open(WATCHLIST_FILE, "w") as f:
        f.write("\n".join(remaining) + ("\n" if remaining else ""))


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]
