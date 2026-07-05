"""
AI Summary page: browse AI-generated summaries for all uploaded documents.
"""
import streamlit as st

from database.models import get_session, PDFDocument
from summarizer.summarizer import summarize
from pdf_processor.processor import extract_text_by_page, get_full_text
from utils.helpers import format_date


def render_summary_page():
    st.markdown("### AI Summary")
    st.caption("Auto-generated summaries of your documents, powered by an offline extractive summarizer.")

    user_id = st.session_state["user_id"]
    session = get_session()
    try:
        pdfs = session.query(PDFDocument).filter(PDFDocument.user_id == user_id).order_by(PDFDocument.uploaded_at.desc()).all()

        if not pdfs:
            st.info("Upload a PDF first to generate a summary.")
            return

        for pdf in pdfs:
            with st.expander(f"📄 {pdf.title} · {format_date(pdf.uploaded_at)}"):
                if pdf.summary:
                    st.write(pdf.summary)
                else:
                    st.caption("No summary available yet.")

                if st.button("🔄 Regenerate Summary", key=f"regen_{pdf.id}"):
                    with st.spinner("Regenerating summary..."):
                        pages = extract_text_by_page(pdf.file_path)
                        full_text = get_full_text(pages)
                        new_summary = summarize(full_text, sentence_count=5)
                        pdf.summary = new_summary
                        session.commit()
                    st.success("Summary updated.")
                    st.rerun()
    finally:
        session.close()
