"""
Sidebar navigation.
"""
import streamlit as st

from utils.helpers import logout

NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Upload PDF", "📤"),
    ("My Library", "📚"),
    ("Now Playing", "🎵"),
    ("History", "🕓"),
    ("Bookmarks", "🔖"),
    ("AI Summary", "✨"),
    ("Notes", "📝"),
    ("Settings", "⚙️"),
]


def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-logo">🎧 <span class="gradient-text">PDF TO AUDIO AI</span></div>',
            unsafe_allow_html=True,
        )

        for label, icon in NAV_ITEMS:
            is_active = st.session_state.get("current_page") == label
            if is_active:
                st.markdown(
                    f'<div class="sidebar-nav-active">{icon} &nbsp;{label}</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(f"{icon}   {label}", key=f"nav_{label}", use_container_width=True):
                    st.session_state["current_page"] = label
                    st.rerun()

        st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

        if st.button("🚪   Logout", key="nav_logout", use_container_width=True):
            logout()
            st.rerun()

        st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
        name = st.session_state.get("user_name", "User")
        email = st.session_state.get("user_email", "")
        initials = "".join([p[0].upper() for p in name.split()[:2]]) if name else "U"
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px; padding: 6px 4px;">
                <div style="width:36px;height:36px;border-radius:50%;
                            background:linear-gradient(135deg,#7c3aed,#c084fc);
                            display:flex;align-items:center;justify-content:center;
                            font-weight:700;font-size:13px;color:white;">{initials}</div>
                <div>
                    <div style="font-size:13px;font-weight:600;">{name}</div>
                    <div style="font-size:11px;color:var(--text-secondary);">{email}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
