"""In-app alerts for your watchlist only: recent headlines (with a plain-
English summary of what each one is about) and earnings dates/results.
This is not a push notification - it's a dedicated page that shows what's
new whenever you visit."""

import streamlit as st

from main import load_watchlist, WATCHLIST_FILE
from cached import cached_stock_report, cached_earnings_summary

st.header(":material/notifications: Notifications")
st.caption("Headlines and earnings for your watchlist only. This page refreshes when you visit it - there's no push notification, since that would need email or browser setup this project doesn't have yet.")

if st.button("Refresh now", icon=":material/refresh:"):
    st.cache_data.clear()

tickers = load_watchlist(WATCHLIST_FILE)
if not tickers:
    st.info("Your watchlist is empty - add stocks from the main dashboard's search bar first.")

for ticker in tickers:
    with st.container(border=True):
        try:
            report = cached_stock_report(ticker)
            price = report["price"]
            st.subheader(f"{price['name']} ({price['ticker']})")

            earnings = cached_earnings_summary(ticker)

            e_col, h_col = st.columns([1, 2])
            with e_col:
                st.markdown("**Earnings**")
                if earnings.get("last"):
                    last = earnings["last"]
                    last_date = last["date"][:10]
                    if last.get("surprise_pct") is not None:
                        label = "Beat" if last["beat"] else "Missed"
                        color = "green" if last["beat"] else "red"
                        st.markdown(f":{color}[{label} estimate by {abs(last['surprise_pct']):.1f}%]")
                        st.caption(f"Reported {last_date}: actual EPS {last['eps_actual']} vs estimate {last['eps_estimate']}")
                    else:
                        st.caption(f"Last reported {last_date} (no estimate on file to compare)")
                else:
                    st.caption("No past earnings on file.")

                if earnings.get("next"):
                    next_e = earnings["next"]
                    st.caption(f"Next: {next_e['date'][:10]}" + (f" (est. EPS {next_e['eps_estimate']})" if next_e.get("eps_estimate") is not None else ""))
                else:
                    st.caption("No upcoming earnings date on file.")

            with h_col:
                st.markdown("**Recent headlines**")
                if not report["headlines"]:
                    st.caption("No recent headlines found.")
                for h in report["headlines"]:
                    st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']})")
                    st.caption(f"{h['category']}: {h['explanation']}")
        except Exception as e:
            st.error(f"{ticker}: failed to load ({e})")
