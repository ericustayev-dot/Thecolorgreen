"""Entry point / navigation router for The Color Green.
Run with: streamlit run dashboard.py
It will open automatically in your browser at http://localhost:8501"""

import os

import streamlit as st

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

    /* Bold, elegant sidebar navigation */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #E5E9E7;
    }
    section[data-testid="stSidebar"] li div a {
        font-family: "Bebas Neue", sans-serif;
        font-size: 1.2rem;
        letter-spacing: 1.3px;
        color: #1A1A1A;
        border-radius: 8px;
        padding: 0.55rem 0.9rem;
        margin-bottom: 3px;
        transition: background-color 0.15s ease;
    }
    section[data-testid="stSidebar"] li div a:hover {
        background-color: #EAF3EE;
    }
    section[data-testid="stSidebar"] li div a[aria-current="page"] {
        background-color: #2D6B40 !important;
        background-image: none !important;
        box-shadow: none !important;
        filter: none !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        text-shadow: none !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] li div a[aria-current="page"] * {
        background: transparent !important;
        box-shadow: none !important;
        filter: none !important;
        text-shadow: none !important;
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_left, logo_mid, logo_right = st.columns([1, 1, 1])
with logo_mid:
    st.image(LOGO_FILE, width="stretch")

pg = st.navigation([
    st.Page("home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/Watchlist.py", title="Watchlist", icon=":material/visibility:"),
    st.Page("pages/World_News.py", title="World News", icon=":material/public:"),
    st.Page("pages/Alerts.py", title="Notifications", icon=":material/notifications:"),
    st.Page("pages/Institutional_Buying.py", title="Institutional Buying", icon=":material/account_balance:"),
])
pg.run()
