"""
History page: listening history with search and resume actions.
"""
import streamlit as st

from database.models import get_session, ListeningHistory, PDFDocument
from utils.helpers import format_duration, format_datetime


def render_history_page():
    st.markdown("### Listening History")
    st.caption("Everything you've listened to, most recent first.")

    user_id = st.session_state["user_id"]
    query = st.text_input("Search history", placeholder="🔍 Search by title...", label_visibility="collapsed")

    session = get_session()
    try:
        records = (
            session.query(ListeningHistory, PDFDocument)
            .join(PDFDocument, ListeningHistory.pdf_id == PDFDocument.id)
            .filter(ListeningHistory.user_id == user_id)
            .order_by(ListeningHistory.last_played_at.desc())
            .all()
        )

        if query:
            records = [r for r in records if query.lower() in r[1].title.lower()]

        if not records:
            st.info("No listening history yet. Start playing something from your library!")
            return

        for history, pdf in records:
            st.markdown('<div class="file-row">', unsafe_allow_html=True)
            cols = st.columns([3, 1.5, 1.5, 1])
            with cols[0]:
                st.markdown(f"**{pdf.title}**")
                st.caption(f"Last played {format_datetime(history.last_played_at)}")
            with cols[1]:
                st.caption("Position")
                st.write(format_duration(history.last_position_seconds))
            with cols[2]:
                st.caption("Total Listened")
                st.write(format_duration(history.total_listened_seconds))
            with cols[3]:
                status = "✅ Completed" if history.completed else "▶️ In progress"
                st.caption(status)
            st.markdown("</div>", unsafe_allow_html=True)
    finally:
        session.close()
