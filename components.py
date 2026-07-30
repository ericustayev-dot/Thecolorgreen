"""Shared render helpers used across multiple pages (Home, Watchlist)."""

import streamlit as st

from main import load_watchlist, WATCHLIST_FILE
from movers import classify_cap
from cached import cached_stock_report, cached_deep_research
from buy_score import compute_buy_weight
from deep_research import fmt_usd_big

SIGNAL_ICON = {
    "good": ":material/check_circle:",
    "bad": ":material/cancel:",
    "caution": ":material/warning:",
    "unknown": ":material/help:",
}
SIGNAL_COLOR = {"good": "green", "bad": "red", "caution": "orange", "unknown": "gray"}

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


def render_deep_research(ticker: str) -> None:
    try:
        dr = cached_deep_research(ticker)
    except Exception as e:
        st.error(f"Deep research report failed to load: {e}")
        return

    st.markdown("##### :material/travel_explore: Deep research report")
    st.caption(
        "Every number below is straight from the company's own reported financials "
        "(via Yahoo Finance) - no AI, no predictions. Each metric is checked against a "
        "fixed threshold applied the same way to every stock."
    )

    rated = [s for s in dr["signals"] if s["signal"] != "unknown"]
    good = sum(1 for s in rated if s["signal"] == "good")
    bad = sum(1 for s in rated if s["signal"] == "bad")
    if rated:
        st.write(f"**{good} of {len(rated)} rated signals are strong, {bad} are weak.**")

    for s in dr["signals"]:
        icon = SIGNAL_ICON[s["signal"]]
        color = SIGNAL_COLOR[s["signal"]]
        st.markdown(f"{icon} **{s['label']}:** :{color}[{s['value']}]")
        if s.get("description"):
            st.caption(s["description"])

    entry = dr.get("entry_price")
    if entry:
        st.divider()
        st.markdown("**Entry price weight scale**")
        if entry["already_attractive"]:
            st.success(
                f"At \\${dr['current_price']:.2f}, this is already at or below the price where the "
                f"reward-vs-risk formula turns attractive (\\${entry['entry_price']:.2f}).",
                icon=":material/check_circle:",
            )
        else:
            st.warning(
                f"Currently \\${dr['current_price']:.2f} - better to buy at \\${entry['entry_price']:.2f} "
                f"or below ({entry['pct_below_current']:.1f}% lower), where upside vs. estimated risk "
                f"turns clearly favorable.",
                icon=":material/schedule:",
            )
        st.caption(
            "Same formula as the buy-weight bar above, solved backwards for the price where it would "
            "read a clear buy - not a prediction that the price will actually get there."
        )

    val = dr["valuation"]
    if val.get("fifty_two_week_low") and val.get("fifty_two_week_high"):
        st.divider()
        st.markdown("**Valuation**")
        st.write(f"52-week range: ${val['fifty_two_week_low']:.2f} - ${val['fifty_two_week_high']:.2f}")
        if val.get("pct_from_52w_high") is not None:
            st.caption(f"{val['pct_from_52w_high']:+.1f}% vs. 52-week high")
        multiples = []
        if val.get("ps_ratio"):
            multiples.append(f"P/S {val['ps_ratio']:.1f}x")
        if val.get("pe_forward"):
            multiples.append(f"forward P/E {val['pe_forward']:.1f}x")
        if val.get("ev_to_ebitda"):
            multiples.append(f"EV/EBITDA {val['ev_to_ebitda']:.1f}x")
        if multiples:
            st.caption(" · ".join(multiples))

    cash = dr["cash_flow"]
    if cash.get("free_cash_flow") is not None:
        st.divider()
        quarter_note = f", quarter ended {cash['quarter_end']}" if cash.get("quarter_end") else ""
        st.markdown(f"**Cash flow** (latest reported quarter{quarter_note})")
        st.write(
            f"Operating cash flow: {fmt_usd_big(cash.get('operating_cash_flow'))} · "
            f"Capex: {fmt_usd_big(cash.get('capital_expenditure'))} · "
            f"Free cash flow: {fmt_usd_big(cash.get('free_cash_flow'))}"
        )


def render_stock_card(ticker: str, key_prefix: str = "") -> None:
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
        render_buy_weight(price, cap)

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

    dr_state_key = f"dr_open_{key_prefix}{ticker}"
    if dr_state_key not in st.session_state:
        st.session_state[dr_state_key] = False

    if st.button(
        "Hide deep research report" if st.session_state[dr_state_key] else "Deep research report",
        icon=":material/close:" if st.session_state[dr_state_key] else ":material/travel_explore:",
        key=f"btn_{dr_state_key}",
    ):
        st.session_state[dr_state_key] = not st.session_state[dr_state_key]
        st.rerun()

    if st.session_state[dr_state_key]:
        render_deep_research(ticker)


def remove_from_watchlist(ticker: str) -> None:
    remaining = [t for t in load_watchlist(WATCHLIST_FILE) if t != ticker]
    with open(WATCHLIST_FILE, "w") as f:
        f.write("\n".join(remaining) + ("\n" if remaining else ""))


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]
