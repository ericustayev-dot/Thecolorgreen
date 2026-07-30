"""Macro/geopolitical headlines, with a note on what that TYPE of event has
historically tended to mean for markets - not a prediction for this event."""

import streamlit as st

from cached import cached_world_news
from market_vitals import get_latest_vitals

st.header(":material/public: World news")

if st.button("Refresh now", icon=":material/refresh:"):
    st.cache_data.clear()

# ---- Market vitals ----
st.subheader(":material/monitor_heart: Market vitals")
st.caption(
    "Gold, silver, and oil price moves from the most recent scheduled run, paired with any "
    "geopolitical/monetary/trade headlines logged in that same run. This shows correlation - "
    "things that happened around the same time - not proven causation. Plenty else moves these "
    "prices too (supply/demand, currency swings), and that has nothing to do with the headline."
)

vitals = get_latest_vitals()
if not vitals:
    st.info("No commodity history logged yet - this fills in once the scheduled job runs.")
else:
    cols = st.columns(len(vitals["commodities"]))
    for col, c in zip(cols, vitals["commodities"]):
        change_pct = float(c["change_pct"])
        color = "#2D6B40" if change_pct >= 0 else "#A32D2D"
        magnitude = min(abs(change_pct) / 5.0 * 100, 100)  # a 5% move fills the bar
        with col:
            st.markdown(f"**{c['label']}**")
            st.markdown(f"${float(c['price']):,.2f} :{'green' if change_pct >= 0 else 'red'}[({change_pct:+.2f}%)]")
            st.markdown(
                f"""
                <div style="height:10px; border-radius:5px; background-color:#EDEDED; overflow:hidden;">
                    <div style="width:{magnitude}%; height:100%; background-color:{color};"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if vitals["headlines"]:
        st.write("")
        st.markdown("**In the news during this same session:**")
        for h in vitals["headlines"]:
            st.markdown(f"- [{h['title']}]({h['link']}) ({h['source']}) · _{h['category']}_")
    else:
        st.caption("No geopolitical/monetary/trade headlines logged in this same session.")

st.divider()

# ---- Headlines ----
st.subheader(":material/newspaper: Headlines")
st.caption("Category notes are general historical patterns for this TYPE of event, not a prediction of what happens this time.")
try:
    for h in cached_world_news():
        st.markdown(f"**[{h['title']}]({h['link']})** ({h['source']})")
        st.caption(f"{h['category']}: {h['explanation']}")
except Exception as e:
    st.error(f"Failed to load world news: {e}")
