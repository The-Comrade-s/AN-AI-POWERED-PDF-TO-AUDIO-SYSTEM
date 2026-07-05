"""
Dashboard page: overview stat cards, upload CTA, recent files, listening streak.
"""
import streamlit as st
from sqlalchemy import func

from database.models import get_session, PDFDocument, AudioFile, Download, ListeningHistory
from utils.helpers import format_duration_long, format_date


def _stat_card(icon, value, label, color="#a855f7"):
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-icon" style="background:{color}22; color:{color};">{icon}</div>
            <p class="stat-value">{value}</p>
            <p class="stat-label">{label}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard():
    user_id = st.session_state["user_id"]
    name = st.session_state.get("user_name", "there").split(" ")[0]

    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown(f"### Welcome back, {name} 👋")
        st.caption("Convert PDFs to natural-sounding audio and pick up right where you left off.")
    with col_btn:
        st.write("")
        if st.button("＋ Upload PDF", use_container_width=True):
            st.session_state["current_page"] = "Upload PDF"
            st.rerun()

    session = get_session()
    try:
        pdf_count = session.query(func.count(PDFDocument.id)).filter(PDFDocument.user_id == user_id).scalar() or 0
        audio_count = session.query(func.count(AudioFile.id)).filter(AudioFile.user_id == user_id).scalar() or 0
        download_count = session.query(func.count(Download.id)).filter(Download.user_id == user_id).scalar() or 0
        total_listened = session.query(func.sum(ListeningHistory.total_listened_seconds)).filter(
            ListeningHistory.user_id == user_id
        ).scalar() or 0

        st.write("")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            _stat_card("📄", pdf_count, "PDFs Uploaded", "#a855f7")
        with c2:
            _stat_card("🎧", audio_count, "Audio Files", "#22c55e")
        with c3:
            _stat_card("⏱️", format_duration_long(total_listened), "Listening Time", "#f472b6")
        with c4:
            _stat_card("⬇️", download_count, "Downloads", "#60a5fa")

        st.write("")

        # Resume listening banner
        recent_history = (
            session.query(ListeningHistory)
            .filter(ListeningHistory.user_id == user_id, ListeningHistory.completed == False)  # noqa: E712
            .order_by(ListeningHistory.last_played_at.desc())
            .first()
        )
        if recent_history:
            pdf = session.query(PDFDocument).filter(PDFDocument.id == recent_history.pdf_id).first()
            if pdf:
                from utils.helpers import format_duration
                st.markdown(
                    f"""
                    <div class="glass-card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
                        <div>
                            <div style="font-size:12px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.05em;">Continue Listening</div>
                            <div style="font-size:16px; font-weight:600; margin-top:4px;">{pdf.title}</div>
                            <div style="font-size:13px; color:var(--text-secondary); margin-top:2px;">Resume from {format_duration(recent_history.last_position_seconds)}</div>
                        </div>
                        <div style="font-size:30px;">▶️</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Upload CTA card if no PDFs yet
        if pdf_count == 0:
            st.markdown(
                """
                <div class="glass-card" style="text-align:center; padding: 40px;">
                    <div style="font-size:40px;">📥</div>
                    <div style="font-size:18px; font-weight:600; margin-top:10px;">Upload a PDF to get started</div>
                    <div style="color:var(--text-secondary); margin-top:6px;">Drag & drop your PDF file, or click the button below to browse and convert it to natural audio.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

        st.markdown("#### Recent Files")
        recent_pdfs = (
            session.query(PDFDocument)
            .filter(PDFDocument.user_id == user_id)
            .order_by(PDFDocument.uploaded_at.desc())
            .limit(5)
            .all()
        )

        if not recent_pdfs:
            st.info("No files yet. Upload your first PDF to see it here.")
        else:
            for pdf in recent_pdfs:
                status_color = {"converted": "#22c55e", "processing": "#f59e0b", "uploaded": "#60a5fa", "failed": "#ef4444"}.get(pdf.status, "#a855f7")
                cols = st.columns([0.5, 3, 1.5, 1, 1])
                with cols[0]:
                    st.markdown("📄")
                with cols[1]:
                    st.markdown(f"**{pdf.title}**")
                    st.caption(f"{pdf.page_count} pages · {format_date(pdf.uploaded_at)}")
                with cols[2]:
                    st.markdown(
                        f'<span class="badge" style="background:{status_color}22;color:{status_color};">{pdf.status.title()}</span>',
                        unsafe_allow_html=True,
                    )
                with cols[3]:
                    if st.button("Open", key=f"open_{pdf.id}"):
                        st.session_state["selected_pdf_id"] = pdf.id
                        st.session_state["current_page"] = "My Library"
                        st.rerun()
                with cols[4]:
                    pass
    finally:
        session.close()
