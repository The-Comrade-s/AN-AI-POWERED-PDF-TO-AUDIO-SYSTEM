"""
PDF processing utilities: text extraction, cleaning, chapter/heading detection,
thumbnail generation, and estimated listening time.
"""
import os
import re
import json

import fitz  # PyMuPDF


def extract_text_by_page(pdf_path: str) -> list[str]:
    """Return a list of raw text strings, one per page."""
    pages = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pages.append(page.get_text("text"))
    return pages


def clean_text(text: str) -> str:
    """Remove broken characters, excess whitespace, and unreadable symbols."""
    if not text:
        return ""
    # Remove control characters / unreadable symbols
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    # Collapse excess spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Fix hyphenated line-break words e.g. "inter-\nnet" -> "internet"
    text = re.sub(r"-\n(\w)", r"\1", text)
    # Normalize remaining single newlines within a paragraph to spaces
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    return text.strip()


HEADING_PATTERN = re.compile(
    r"^\s*(chapter\s+\d+|CHAPTER\s+\d+|Chapter\s+[IVXLC]+|\d{1,2}\.\s+[A-Z][^\n]{2,80}|[A-Z][A-Z\s]{6,60})\s*$",
    re.MULTILINE,
)


def detect_chapters(pages: list[str]) -> list[dict]:
    """
    Detect probable chapter/heading boundaries across the document.
    Returns a list of {title, page_start} dicts. Falls back to a single
    'Full Document' chapter if nothing is detected.
    """
    chapters = []
    for page_num, raw_text in enumerate(pages, start=1):
        for match in HEADING_PATTERN.finditer(raw_text):
            title = match.group(0).strip()
            if 3 <= len(title) <= 80:
                chapters.append({"title": title, "page_start": page_num})

    # De-duplicate consecutive near-identical headings
    deduped = []
    seen_titles = set()
    for ch in chapters:
        key = ch["title"].lower()
        if key not in seen_titles:
            deduped.append(ch)
            seen_titles.add(key)

    if not deduped:
        deduped = [{"title": "Full Document", "page_start": 1}]

    return deduped


def generate_thumbnail(pdf_path: str, output_path: str, zoom: float = 0.6) -> str | None:
    """Render the first page of the PDF as a PNG thumbnail. Returns path or None."""
    try:
        with fitz.open(pdf_path) as doc:
            if len(doc) == 0:
                return None
            page = doc[0]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            pix.save(output_path)
        return output_path
    except Exception:
        return None


def validate_pdf(pdf_path: str) -> tuple[bool, str]:
    """Check the PDF opens correctly and has readable content."""
    try:
        with fitz.open(pdf_path) as doc:
            if len(doc) == 0:
                return False, "The PDF has no pages."
            if doc.is_encrypted:
                return False, "This PDF is password-protected. Please upload an unlocked file."
        return True, "Valid PDF."
    except Exception as exc:
        return False, f"Could not open PDF: it may be corrupted. ({exc})"


def get_full_text(pages: list[str]) -> str:
    """Join and clean all page text into one continuous string."""
    return clean_text("\n\n".join(pages))


def word_count(text: str) -> int:
    return len(text.split())


def estimate_listening_seconds(text: str, words_per_minute: int = 150) -> float:
    """Estimate audio duration in seconds based on word count and speaking rate."""
    wc = word_count(text)
    minutes = wc / words_per_minute if words_per_minute else 0
    return round(minutes * 60, 1)


def estimate_listening_seconds_from_word_count(wc: int, words_per_minute: int = 150) -> float:
    """Estimate audio duration in seconds directly from a known word count."""
    minutes = wc / words_per_minute if words_per_minute else 0
    return round(minutes * 60, 1)


def chapters_to_json(chapters: list[dict]) -> str:
    return json.dumps(chapters)


def chapters_from_json(chapters_json: str) -> list[dict]:
    if not chapters_json:
        return []
    try:
        return json.loads(chapters_json)
    except json.JSONDecodeError:
        return []


def split_text_by_chapters(pages: list[str], chapters: list[dict]) -> list[dict]:
    """
    Given page texts and detected chapter start pages, split full cleaned text
    into per-chapter text blocks. Returns [{title, text}].
    """
    if len(chapters) <= 1:
        return [{"title": chapters[0]["title"] if chapters else "Full Document",
                  "text": get_full_text(pages)}]

    result = []
    sorted_chapters = sorted(chapters, key=lambda c: c["page_start"])
    for i, ch in enumerate(sorted_chapters):
        start_page = ch["page_start"] - 1
        end_page = sorted_chapters[i + 1]["page_start"] - 1 if i + 1 < len(sorted_chapters) else len(pages)
        chunk_pages = pages[start_page:end_page]
        result.append({"title": ch["title"], "text": get_full_text(chunk_pages)})
    return result
