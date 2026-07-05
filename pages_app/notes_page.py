"""
Notes page: view, search, and delete notes taken while listening.
"""
import streamlit as st

from database.models import get_session, Note, PDFDocument
from utils.helpers import format_duration, format_datetime


def render_notes_page():
    st.markdown("### Notes")
    st.caption("Everything you've jotted down while listening.")

    user_id = st.session_state["user_id"]
    query = st.text_input("Search notes", placeholder="🔍 Search notes...", label_visibility="collapsed")

    session = get_session()
    try:
        notes = (
            session.query(Note, PDFDocument)
            .join(PDFDocument, Note.pdf_id == PDFDocument.id)
            .filter(Note.user_id == user_id)
            .order_by(Note.created_at.desc())
            .all()
        )

        if query:
            notes = [n for n in notes if query.lower() in n[0].text.lower() or query.lower() in n[1].title.lower()]

        if not notes:
            st.info("No notes yet. Add one from the Now Playing page while listening.")
            return

        for note, pdf in notes:
            st.markdown('<div class="glass-card" style="margin-bottom:10px;">', unsafe_allow_html=True)
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"**{pdf.title}** · {format_duration(note.timestamp_seconds)}")
                st.write(note.text)
                st.caption(format_datetime(note.created_at))
            with cols[1]:
                if st.button("🗑️", key=f"del_note_{note.id}"):
                    session.delete(note)
                    session.commit()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    finally:
        session.close()
