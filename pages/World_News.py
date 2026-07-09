"""Macro/geopolitical headlines, with a note on what that TYPE of event has
historically tended to mean for markets - not a prediction for this event."""

import streamlit as st

from cached import cached_world_news

st.header(":material/public: World news")

if st.button("Refresh now", icon=":material/refresh:"):
    st.cache_data.clear()

st.caption("Category notes are general historical patterns for this TYPE of event, not a prediction of what happens this time.")
try:
    for h in cached_world_news():
        st.markdown(f"**[{h['title']}]({h['link']})** ({h['source']})")
        st.caption(f"{h['category']}: {h['explanation']}")
except Exception as e:
    st.error(f"Failed to load world news: {e}")
