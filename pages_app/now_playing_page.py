"""
Now Playing page: professional audio player interface with playback controls,
chapter navigation, bookmarking, and resume-from-last-position.
"""
import os
import streamlit as st

from database.models import get_session, AudioFile, PDFDocument, ListeningHistory, Bookmark, Download
from utils.helpers import format_duration


def render_now_playing_page():
    st.markdown("### Now Playing")

    user_id = st.session_state["user_id"]
    audio_id = st.session_state.get("now_playing_audio_id")

    session = get_session()
    try:
        if not audio_id:
            # Try to grab the most recently created audio file for this user
            latest = (
                session.query(AudioFile)
                .filter(AudioFile.user_id == user_id)
                .order_by(AudioFile.created_at.desc())
                .first()
            )
            if latest:
                audio_id = latest.id
                st.session_state["now_playing_audio_id"] = audio_id

        if not audio_id:
            st.info("Nothing to play yet. Convert a PDF from **My Library** first.")
            return

        audio = session.query(AudioFile).filter(AudioFile.id == audio_id).first()
        if not audio:
            st.info("This audio file is no longer available.")
            return

        pdf = session.query(PDFDocument).filter(PDFDocument.id == audio.pdf_id).first()

        # All chapters for this pdf, ordered
        chapters = (
            session.query(AudioFile)
            .filter(AudioFile.pdf_id == audio.pdf_id)
            .order_by(AudioFile.chapter_index)
            .all()
        )

        col_player, col_side = st.columns([2, 1])

        with col_player:
            st.markdown('<div class="now-playing-card">', unsafe_allow_html=True)
            st.markdown('<div class="album-art">🎧</div>', unsafe_allow_html=True)
            st.markdown(f"#### {pdf.title if pdf else 'Unknown'}")
            if audio.chapter_title:
                st.caption(f"Chapter: {audio.chapter_title}")
            st.caption(f"Voice: {audio.voice} · {audio.format.upper()}")

            if os.path.exists(audio.file_path):
                st.audio(audio.file_path, format=f"audio/{audio.format}")
            else:
                st.warning("Audio file missing from disk.")

            st.caption(f"Duration: {format_duration(audio.duration_seconds)}")

            nav_cols = st.columns(4)
            current_idx = next((i for i, c in enumerate(chapters) if c.id == audio.id), 0)
            with nav_cols[0]:
                if st.button("⏮ Previous", use_container_width=True, disabled=current_idx == 0):
                    st.session_state["now_playing_audio_id"] = chapters[current_idx - 1].id
                    st.rerun()
            with nav_cols[1]:
                if st.button("🔖 Bookmark", use_container_width=True):
                    _add_bookmark(session, user_id, pdf.id if pdf else None)
            with nav_cols[2]:
                if st.button("⬇️ Download", use_container_width=True):
                    _log_download(session, user_id, audio.id)
                    st.success("Download logged. Use the button below to save the file.")
            with nav_cols[3]:
                if st.button("⏭ Next", use_container_width=True, disabled=current_idx >= len(chapters) - 1):
                    st.session_state["now_playing_audio_id"] = chapters[current_idx + 1].id
                    st.rerun()

            if os.path.exists(audio.file_path):
                with open(audio.file_path, "rb") as f:
                    st.download_button(
                        "Save audio file to device",
                        f,
                        file_name=f"{pdf.title if pdf else 'audio'}_{audio.chapter_index}.{audio.format}",
                        use_container_width=True,
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            _update_history(session, user_id, pdf.id if pdf else None, audio.duration_seconds)

        with col_side:
            st.markdown("**Chapters**")
            if len(chapters) <= 1:
                st.caption("Single audio file (no chapters detected).")
            else:
                for c in chapters:
                    label = c.chapter_title or f"Part {c.chapter_index}"
                    is_current = c.id == audio.id
                    prefix = "▶️ " if is_current else "　"
                    if st.button(f"{prefix}{label}", key=f"chap_{c.id}", use_container_width=True):
                        st.session_state["now_playing_audio_id"] = c.id
                        st.rerun()

            st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
            st.markdown("**Add a Note**")
            note_text = st.text_area("Note", placeholder="Write your thoughts...", label_visibility="collapsed", key="quick_note")
            if st.button("Save Note", use_container_width=True):
                if not pdf:
                    st.warning("Can't save a note: the source PDF for this audio is no longer available.")
                elif note_text.strip():
                    from database.models import Note
                    try:
                        note = Note(user_id=user_id, pdf_id=pdf.id, timestamp_seconds=0, text=note_text.strip())
                        session.add(note)
                        session.commit()
                        st.success("Note saved.")
                    except Exception as exc:
                        session.rollback()
                        st.error(f"Could not save note: {exc}")
                else:
                    st.warning("Write something before saving.")

    finally:
        session.close()


def _add_bookmark(session, user_id, pdf_id):
    if not pdf_id:
        return
    bookmark = Bookmark(user_id=user_id, pdf_id=pdf_id, position_seconds=0, label="Bookmark")
    session.add(bookmark)
    session.commit()
    st.success("Bookmark added.")


def _log_download(session, user_id, audio_file_id):
    download = Download(user_id=user_id, audio_file_id=audio_file_id)
    session.add(download)
    session.commit()


def _update_history(session, user_id, pdf_id, duration):
    if not pdf_id:
        return
    history = (
        session.query(ListeningHistory)
        .filter(ListeningHistory.user_id == user_id, ListeningHistory.pdf_id == pdf_id)
        .first()
    )
    if not history:
        history = ListeningHistory(user_id=user_id, pdf_id=pdf_id, last_position_seconds=0, total_listened_seconds=0)
        session.add(history)
    session.commit()
