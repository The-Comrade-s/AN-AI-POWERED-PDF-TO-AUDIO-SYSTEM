"""
General utility helpers: time formatting, session state management, file paths.
"""
import os
import streamlit as st


def format_duration(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    seconds = int(seconds or 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_duration_long(seconds: float) -> str:
    """Format seconds as e.g. '15h 42m'."""
    seconds = int(seconds or 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def format_filesize(kb: float) -> str:
    if kb >= 1024:
        return f"{kb / 1024:.1f} MB"
    return f"{kb:.0f} KB"


def format_date(dt) -> str:
    if not dt:
        return ""
    return dt.strftime("%b %d, %Y")


def format_datetime(dt) -> str:
    if not dt:
        return ""
    return dt.strftime("%b %d, %Y · %I:%M %p")


def init_session_state():
    """Initialize all required session state keys with defaults."""
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user_name": None,
        "user_email": None,
        "current_page": "Dashboard",
        "auth_view": "login",  # login, register, forgot_password
        "now_playing_audio_id": None,
        "theme": "dark",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout():
    """Clear session state related to the logged-in user."""
    for key in ["logged_in", "user_id", "user_name", "user_email", "now_playing_audio_id"]:
        st.session_state[key] = None if key != "logged_in" else False
    st.session_state["current_page"] = "Dashboard"
    st.session_state["auth_view"] = "login"


def ensure_dirs():
    for d in ["uploads", "generated_audio", "assets/thumbnails"]:
        os.makedirs(d, exist_ok=True)


def user_upload_dir(user_id: int) -> str:
    path = os.path.join("uploads", str(user_id))
    os.makedirs(path, exist_ok=True)
    return path


def user_audio_dir(user_id: int) -> str:
    path = os.path.join("generated_audio", str(user_id))
    os.makedirs(path, exist_ok=True)
    return path


def user_thumb_dir(user_id: int) -> str:
    path = os.path.join("assets", "thumbnails", str(user_id))
    os.makedirs(path, exist_ok=True)
    return path
