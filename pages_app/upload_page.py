"""
Upload PDF page: file upload, validation, text extraction, chapter detection,
summarization, and thumbnail generation.
"""
import os
import time

import streamlit as st

from database.models import get_session, PDFDocument
from pdf_processor.processor import (
    validate_pdf, extract_text_by_page, get_full_text, word_count,
    detect_chapters, chapters_to_json, generate_thumbnail, estimate_listening_seconds,
)
from summarizer.summarizer import summarize
from utils.helpers import user_upload_dir, user_thumb_dir

MAX_FILE_SIZE_MB = 50


def render_upload_page():
    st.markdown("### Upload a PDF")
    st.caption("Drag and drop a PDF below, or browse your files. Maximum size: 50 MB.")

    uploaded_file = st.file_uploader(
        "Drop your PDF here",
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    if uploaded_file is None:
        st.markdown(
            """
            <div class="glass-card" style="text-align:center; padding:50px; border: 2px dashed rgba(255,255,255,0.15);">
                <div style="font-size:44px;">📄</div>
                <div style="font-size:16px; font-weight:600; margin-top:10px;">Drag & drop your PDF here</div>
                <div style="color:var(--text-secondary); font-size:13px; margin-top:4px;">or use the browse button above · PDF only · up to 50MB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"File is too large ({file_size_mb:.1f} MB). Maximum allowed size is {MAX_FILE_SIZE_MB} MB.")
        return

    st.success(f"**{uploaded_file.name}** ready · {file_size_mb:.1f} MB")

    if st.button("Process & Convert", use_container_width=True):
        _process_upload(uploaded_file)


def _process_upload(uploaded_file):
    user_id = st.session_state["user_id"]
    upload_dir = user_upload_dir(user_id)
    thumb_dir = user_thumb_dir(user_id)

    safe_name = uploaded_file.name.replace(" ", "_")
    save_path = os.path.join(upload_dir, f"{int(time.time())}_{safe_name}")

    progress = st.progress(0, text="Saving file...")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    progress.progress(15, text="Validating PDF...")

    is_valid, message = validate_pdf(save_path)
    if not is_valid:
        progress.empty()
        st.error(message)
        os.remove(save_path)
        return

    try:
        progress.progress(30, text="Extracting text...")
        pages = extract_text_by_page(save_path)
        full_text = get_full_text(pages)

        if not full_text or len(full_text.split()) < 5:
            progress.empty()
            st.error("This PDF doesn't appear to contain readable text (it may be a scanned image without OCR).")
            os.remove(save_path)
            return

        progress.progress(50, text="Detecting chapters and headings...")
        chapters = detect_chapters(pages)

        progress.progress(70, text="Generating thumbnail...")
        thumb_path = os.path.join(thumb_dir, f"{int(time.time())}.png")
        generate_thumbnail(save_path, thumb_path)

        progress.progress(85, text="Generating AI summary...")
        summary = summarize(full_text, sentence_count=5)

        progress.progress(95, text="Saving to your library...")
        session = get_session()
        try:
            pdf_doc = PDFDocument(
                user_id=user_id,
                title=os.path.splitext(uploaded_file.name)[0],
                file_path=save_path,
                thumbnail_path=thumb_path if os.path.exists(thumb_path) else None,
                page_count=len(pages),
                word_count=word_count(full_text),
                summary=summary,
                chapters_json=chapters_to_json(chapters),
                file_size_kb=uploaded_file.size / 1024,
                status="uploaded",
            )
            session.add(pdf_doc)
            session.commit()
            new_id = pdf_doc.id
        finally:
            session.close()

        progress.progress(100, text="Done!")
        time.sleep(0.4)
        progress.empty()

        est_seconds = estimate_listening_seconds(full_text)
        st.success(f"'{uploaded_file.name}' processed successfully! Estimated listening time: {int(est_seconds // 60)} minutes.")

        with st.expander("📋 AI Summary", expanded=True):
            st.write(summary)

        st.info(f"Detected {len(chapters)} chapter/section(s). Head to **My Library** to generate audio.")

        st.session_state["selected_pdf_id"] = new_id

    except Exception as exc:
        progress.empty()
        st.error(f"Something went wrong while processing this PDF: {exc}")
        if os.path.exists(save_path):
            os.remove(save_path)
