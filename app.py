"""
AI PDF to Audio System — Main Application Entry Point.

Run with: streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="PDF to Audio AI",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

from assets.styles import inject_css
from database.models import init_db
from utils.helpers import init_session_state, ensure_dirs

from pages_app.auth_page import render_auth_page
from pages_app.sidebar import render_sidebar
from pages_app.dashboard import render_dashboard
from pages_app.upload_page import render_upload_page
from pages_app.library_page import render_library_page
from pages_app.now_playing_page import render_now_playing_page
from pages_app.history_page import render_history_page
from pages_app.bookmarks_page import render_bookmarks_page
from pages_app.summary_page import render_summary_page
from pages_app.notes_page import render_notes_page
from pages_app.settings_page import render_settings_page

# ---- Bootstrap ----
init_db()
ensure_dirs()
init_session_state()
inject_css(st)

# ---- Router ----
if not st.session_state.get("logged_in"):
    render_auth_page()
else:
    render_sidebar()

    page = st.session_state.get("current_page", "Dashboard")

    PAGE_ROUTER = {
        "Dashboard": render_dashboard,
        "Upload PDF": render_upload_page,
        "My Library": render_library_page,
        "Now Playing": render_now_playing_page,
        "History": render_history_page,
        "Bookmarks": render_bookmarks_page,
        "AI Summary": render_summary_page,
        "Notes": render_notes_page,
        "Settings": render_settings_page,
    }

    render_fn = PAGE_ROUTER.get(page, render_dashboard)

    try:
        render_fn()
    except Exception as exc:
        st.error(f"Something went wrong loading this page: {exc}")
        st.caption("Try navigating to another page, or refresh the app.")
