"""
My Library page: displays uploaded PDFs as cards with actions to convert to
audio, play, download, or delete. Also handles the voice/speed selection
modal-like flow for conversion.
"""
import os

import streamlit as st

from database.models import get_session, PDFDocument, AudioFile
from pdf_processor.processor import (
    extract_text_by_page, chapters_from_json, split_text_by_chapters, get_full_text,
)
from audio.tts_engine import generate_speech, get_duration_seconds, list_available_voices, SPEED_OPTIONS, change_speed
from utils.helpers import format_date, format_filesize, user_audio_dir, format_duration_long
from pdf_processor.processor import estimate_listening_seconds_from_word_count


def render_library_page():
    st.markdown("### My Library")
    st.caption("All your uploaded documents in one place.")

    user_id = st.session_state["user_id"]
    session = get_session()
    try:
        search_col, filter_col = st.columns([3, 1])
        with search_col:
            query = st.text_input("Search your library", placeholder="🔍 Search PDFs by title...", label_visibility="collapsed")
        with filter_col:
            sort_option = st.selectbox(
                "Sort", ["Newest", "Oldest", "Longest", "Shortest"], label_visibility="collapsed"
            )

        pdfs_query = session.query(PDFDocument).filter(PDFDocument.user_id == user_id)
        if query:
            pdfs_query = pdfs_query.filter(PDFDocument.title.ilike(f"%{query}%"))

        pdfs = pdfs_query.all()

        if sort_option == "Newest":
            pdfs.sort(key=lambda p: p.uploaded_at, reverse=True)
        elif sort_option == "Oldest":
            pdfs.sort(key=lambda p: p.uploaded_at)
        elif sort_option == "Longest":
            pdfs.sort(key=lambda p: p.word_count, reverse=True)
        elif sort_option == "Shortest":
            pdfs.sort(key=lambda p: p.word_count)

        if not pdfs:
            st.info("No PDFs found. Upload one from the **Upload PDF** page.")
            return

        for pdf in pdfs:
            _render_pdf_card(pdf, session, user_id)

    finally:
        session.close()


def _render_pdf_card(pdf: PDFDocument, session, user_id: int):
    est_seconds = estimate_listening_seconds_from_word_count(pdf.word_count)
    audio_files = session.query(AudioFile).filter(AudioFile.pdf_id == pdf.id).all()
    has_audio = len(audio_files) > 0

    with st.container():
        st.markdown('<div class="glass-card" style="margin-bottom:14px;">', unsafe_allow_html=True)
        cols = st.columns([1, 3, 1, 1, 1, 1])

        with cols[0]:
            if pdf.thumbnail_path and os.path.exists(pdf.thumbnail_path):
                st.image(pdf.thumbnail_path, use_container_width=True)
            else:
                st.markdown(
                    '<div style="font-size:36px; text-align:center;">📄</div>', unsafe_allow_html=True
                )

        with cols[1]:
            st.markdown(f"**{pdf.title}**")
            st.caption(
                f"{pdf.page_count} pages · {format_filesize(pdf.file_size_kb)} · "
                f"Uploaded {format_date(pdf.uploaded_at)} · ~{format_duration_long(est_seconds)} listen"
            )
            status_color = {"converted": "#22c55e", "processing": "#f59e0b", "uploaded": "#60a5fa", "failed": "#ef4444"}.get(pdf.status, "#a855f7")
            st.markdown(
                f'<span class="badge" style="background:{status_color}22;color:{status_color};">{pdf.status.title()}</span>',
                unsafe_allow_html=True,
            )

        with cols[2]:
            if st.button("🎙️ Convert", key=f"convert_{pdf.id}", use_container_width=True):
                st.session_state[f"show_convert_{pdf.id}"] = True

        with cols[3]:
            if has_audio:
                if st.button("▶️ Play", key=f"play_{pdf.id}", use_container_width=True):
                    st.session_state["now_playing_audio_id"] = audio_files[0].id
                    st.session_state["current_page"] = "Now Playing"
                    st.rerun()
            else:
                st.button("▶️ Play", key=f"play_disabled_{pdf.id}", use_container_width=True, disabled=True)

        with cols[4]:
            if has_audio and os.path.exists(audio_files[0].file_path):
                with open(audio_files[0].file_path, "rb") as f:
                    st.download_button(
                        "⬇️", f, file_name=os.path.basename(audio_files[0].file_path),
                        key=f"dl_{pdf.id}", use_container_width=True,
                    )
            else:
                st.button("⬇️", key=f"dl_disabled_{pdf.id}", use_container_width=True, disabled=True)

        with cols[5]:
            if st.button("🗑️", key=f"del_{pdf.id}", use_container_width=True):
                _delete_pdf(pdf, session)
                st.rerun()

        if pdf.summary:
            with st.expander("✨ AI Summary"):
                st.write(pdf.summary)

        if st.session_state.get(f"show_convert_{pdf.id}"):
            _render_conversion_panel(pdf, session, user_id)

        st.markdown("</div>", unsafe_allow_html=True)


def _render_conversion_panel(pdf: PDFDocument, session, user_id: int):
    st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
    st.markdown("**Convert to Audio**")

    voices = list_available_voices()
    col1, col2, col3 = st.columns(3)
    with col1:
        voice_label = st.selectbox("Voice", list(voices.keys()), key=f"voice_{pdf.id}")
    with col2:
        speed = st.selectbox("Speed", SPEED_OPTIONS, index=2, key=f"speed_{pdf.id}")
    with col3:
        audio_format = st.selectbox("Format", ["mp3", "wav"], key=f"format_{pdf.id}")

    by_chapter = st.checkbox("Generate separate audio per chapter", key=f"chapter_{pdf.id}")

    if st.button("Generate Audio", key=f"generate_{pdf.id}", use_container_width=True):
        _generate_audio(pdf, session, user_id, voices[voice_label], speed, audio_format, by_chapter)


def _generate_audio(pdf, session, user_id, voice, speed, audio_format, by_chapter):
    audio_dir = user_audio_dir(user_id)
    progress = st.progress(0, text="Preparing text...")

    try:
        pages = extract_text_by_page(pdf.file_path)
        chapters = chapters_from_json(pdf.chapters_json)

        if by_chapter and len(chapters) > 1:
            chunks = split_text_by_chapters(pages, chapters)
        else:
            chunks = [{"title": None, "text": get_full_text(pages)}]

        total = len(chunks)
        skipped_chapters = []
        generated_count = 0

        for idx, chunk in enumerate(chunks, start=1):
            progress.progress(int((idx - 1) / total * 80) + 10, text=f"Generating speech ({idx}/{total})...")

            chunk_text = (chunk.get("text") or "").strip()
            if len(chunk_text.split()) < 20:
                # Not enough real content to convert (e.g. a heading-only
                # section) — skip it rather than sending blank text to TTS.
                skipped_chapters.append(chunk.get("title") or f"Part {idx}")
                continue

            base_name = f"{pdf.id}_{idx}"
            mp3_path = generate_speech(chunk_text, voice, audio_dir, base_filename=base_name)

            final_path = mp3_path
            if speed != 1.0 or audio_format != "mp3":
                # Use a distinct filename so we never read and write the same
                # file at once (pydub needs the source fully readable first).
                final_path = os.path.join(audio_dir, f"{base_name}_final.{audio_format}")
                change_speed(mp3_path, speed, final_path)
                if os.path.exists(mp3_path) and mp3_path != final_path:
                    try:
                        os.remove(mp3_path)
                    except OSError:
                        pass

            duration = get_duration_seconds(final_path)

            audio_record = AudioFile(
                pdf_id=pdf.id,
                user_id=user_id,
                voice=voice,
                format=audio_format,
                file_path=final_path,
                duration_seconds=duration,
                chapter_title=chunk.get("title"),
                chapter_index=idx,
            )
            session.add(audio_record)
            generated_count += 1

        if generated_count == 0:
            session.rollback()
            st.error("This document doesn't have enough readable text to convert to audio.")
            return

        pdf.status = "converted"
        session.commit()

        progress.progress(100, text="Done!")
        if skipped_chapters:
            st.success(f"Audio generated for {generated_count} section(s). Head to Now Playing to listen.")
            st.info(f"Skipped {len(skipped_chapters)} heading(s) with no body text: {', '.join(skipped_chapters)}")
        else:
            st.success("Audio generated successfully! Head to Now Playing to listen.")
        st.session_state[f"show_convert_{pdf.id}"] = False

    except RuntimeError as exc:
        session.rollback()
        st.error(str(exc))
    except Exception as exc:
        session.rollback()
        st.error(f"Audio generation failed: {exc}")
    finally:
        progress.empty()


def _delete_pdf(pdf: PDFDocument, session):
    try:
        if os.path.exists(pdf.file_path):
            os.remove(pdf.file_path)
        if pdf.thumbnail_path and os.path.exists(pdf.thumbnail_path):
            os.remove(pdf.thumbnail_path)
        for audio in pdf.audio_files:
            if os.path.exists(audio.file_path):
                os.remove(audio.file_path)
        session.delete(pdf)
        session.commit()
    except Exception as exc:
        session.rollback()
        st.error(f"Could not delete file: {exc}")
