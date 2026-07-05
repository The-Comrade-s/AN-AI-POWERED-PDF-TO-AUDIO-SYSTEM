"""
Bookmarks page: view and manage saved bookmarks across all PDFs.
"""
import streamlit as st

from database.models import get_session, Bookmark, PDFDocument
from utils.helpers import format_duration, format_datetime


def render_bookmarks_page():
    st.markdown("### Bookmarks")
    st.caption("Jump back to the moments that mattered.")

    user_id = st.session_state["user_id"]
    session = get_session()
    try:
        bookmarks = (
            session.query(Bookmark, PDFDocument)
            .join(PDFDocument, Bookmark.pdf_id == PDFDocument.id)
            .filter(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
            .all()
        )

        if not bookmarks:
            st.info("No bookmarks yet. Add one from the Now Playing page while listening.")
            return

        for bookmark, pdf in bookmarks:
            st.markdown('<div class="glass-card" style="margin-bottom:10px;">', unsafe_allow_html=True)
            cols = st.columns([3, 1.5, 1])
            with cols[0]:
                st.markdown(f"**{pdf.title}**")
                st.caption(bookmark.label or "Bookmark")
            with cols[1]:
                st.caption("Position")
                st.write(format_duration(bookmark.position_seconds))
            with cols[2]:
                if st.button("🗑️ Remove", key=f"del_bm_{bookmark.id}"):
                    session.delete(bookmark)
                    session.commit()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    finally:
        session.close()
