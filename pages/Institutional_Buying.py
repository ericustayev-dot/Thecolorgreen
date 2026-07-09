"""Shows what well-known hedge funds are buying/selling based on their
quarterly SEC Form 13F filings. Separate page (left sidebar) since this
data behaves very differently from the rest of the site - it's always
weeks-to-months old by law, not live."""

import os

import streamlit as st

from institutional import load_previous, compute_all_institutional_activity

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
LOGO_FILE = os.path.join(PROJECT_ROOT, "logo_transparent.png")
FAVICON_FILE = os.path.join(PROJECT_ROOT, "favicon.png")

st.set_page_config(page_title="The Color Green - Institutional Buying", page_icon=FAVICON_FILE, layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem !important;
        max-width: 1200px !important;
        margin-left: auto !important;
        margin-right: auto !important;
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
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_left, logo_mid, logo_right = st.columns([1, 1, 1])
with logo_mid:
    st.image(LOGO_FILE, width="stretch")

st.header(":material/account_balance: Institutional buying")
st.warning(
    "This is never real-time. Hedge funds have up to 45 days after each calendar quarter ends to "
    "disclose holdings in SEC Form 13F filings - by the time you see this, it reflects a position "
    "already weeks-to-months old. \"Buying\" means a fund's stake was new or larger in its most "
    "recent filing than its previous one, not a trade made today.",
    icon=":material/schedule:",
)

refresh_col1, refresh_col2 = st.columns([4, 2])
with refresh_col2:
    if st.button("Recompute now", icon=":material/refresh:", key="recompute_institutional"):
        with st.spinner("Pulling fresh 13F filings from SEC EDGAR for 10 funds (about 30 seconds)..."):
            compute_all_institutional_activity(force=True)
        st.rerun()

data = load_previous()
if not data:
    st.info("No data yet - click \"Recompute now\" above to pull the latest 13F filings.")
else:
    st.caption(f"Last computed {data['computed_date']} · tracking {len(data['funds'])} well-known funds")

    for fund in data["funds"]:
        with st.container(border=True):
            st.subheader(fund["fund"])

            if fund.get("error"):
                st.error(f"Couldn't load this fund's filing: {fund['error']}")
                continue
            if not fund.get("filing_date"):
                st.info("No 13F filing found for this fund.")
                continue

            st.caption(
                f"Filed {fund['filing_date']}"
                + (f" · compared to previous filing on {fund['previous_filing_date']}" if fund.get("previous_filing_date") else "")
            )

            buys = fund["buys"]
            sells = fund["sells"]

            buy_col, sell_col = st.columns(2)
            with buy_col:
                st.markdown(":green[**Buying**]")
                if not buys:
                    st.caption("No new or increased positions this filing.")
                for m in buys[:5]:
                    label = "New position" if m["action"] == "new" else f"Increased {m['change_pct']:+.0f}%"
                    st.write(f"**{m['name'].title()}** - {label}")
                    st.caption(f"${m['value_usd']:,} reported value")
            with sell_col:
                st.markdown(":red[**Selling**]")
                if not sells:
                    st.caption("No reduced or exited positions this filing.")
                for m in sells[:5]:
                    label = "Sold out" if m["action"] == "sold_out" else f"Reduced {m['change_pct']:+.0f}%"
                    st.write(f"**{m['name'].title()}** - {label}")
                    st.caption(f"${m['value_usd']:,} reported value")

            if len(buys) > 5 or len(sells) > 5:
                with st.expander(f"See all {len(buys)} buys and {len(sells)} sells"):
                    for m in buys[5:]:
                        st.write(f":green[{m['name'].title()} - New/increased position (${m['value_usd']:,})]")
                    for m in sells[5:]:
                        st.write(f":red[{m['name'].title()} - Reduced/sold position (${m['value_usd']:,})]")
