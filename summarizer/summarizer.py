"""
Summarization module.

Default engine: a lightweight, dependency-free extractive summarizer built
with pure Python (word-frequency scoring, no NLTK/sumy). This was chosen
over sumy/NLTK-based summarization after real deployment testing showed
NLTK's runtime download of tokenizer data (punkt/punkt_tab) can hang or
fail unpredictably on Streamlit Community Cloud's network, causing the
"Process & Convert" step to appear frozen with no visible error. A
zero-dependency approach removes that failure point completely and runs
instantly with no external downloads.

It was also chosen over Hugging Face Transformers (BART/T5) because those
models require large downloads (400MB-1.5GB) and significant RAM, which is
unreliable on free-tier hosts (typically 512MB-1GB RAM).

The `summarize()` function is the single entry point used by the rest of
the app. To upgrade later:
    - Set SUMMARIZER_ENGINE = "transformers" and implement _summarize_transformers()
    - Or set SUMMARIZER_ENGINE = "llm_api" and implement _summarize_llm_api()
      (e.g. call the Anthropic or OpenAI API with your own key)
No other file needs to change.
"""
import os
import re
from collections import Counter

# Options: "simple" (default, offline, zero-dependency), "transformers", "llm_api"
SUMMARIZER_ENGINE = os.environ.get("SUMMARIZER_ENGINE", "simple")

_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", "at", "by",
    "for", "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "once", "here", "there",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s",
    "t", "can", "will", "just", "don", "should", "now", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does", "did",
    "doing", "it", "its", "this", "that", "these", "those", "of", "as", "we",
    "our", "you", "your", "i", "he", "she", "they", "them", "his", "her", "their",
}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")
_WORD_RE = re.compile(r"[A-Za-z']+")


def _split_sentences(text: str) -> list:
    """Split text into sentences using punctuation heuristics (no NLTK needed)."""
    text = text.strip()
    if not text:
        return []
    sentences = _SENTENCE_SPLIT_RE.split(text)
    # Filter out fragments that are too short to be real sentences
    return [s.strip() for s in sentences if len(s.strip()) > 15]


def _summarize_simple(text: str, sentence_count: int = 5) -> str:
    """
    Extractive summary via word-frequency scoring:
    1. Split into sentences
    2. Score words by frequency (excluding stop words)
    3. Score each sentence by the sum of its word scores
    4. Return the top N highest-scoring sentences, in original order
    """
    sentences = _split_sentences(text)
    if not sentences:
        return text[:500]

    if len(sentences) <= sentence_count:
        return " ".join(sentences)

    words = [w.lower() for w in _WORD_RE.findall(text) if w.lower() not in _STOP_WORDS and len(w) > 2]
    if not words:
        return " ".join(sentences[:sentence_count])

    word_freq = Counter(words)
    max_freq = max(word_freq.values())
    for w in word_freq:
        word_freq[w] = word_freq[w] / max_freq

    sentence_scores = []
    for idx, sentence in enumerate(sentences):
        sentence_words = [w.lower() for w in _WORD_RE.findall(sentence)]
        if not sentence_words:
            score = 0.0
        else:
            score = sum(word_freq.get(w, 0.0) for w in sentence_words) / len(sentence_words)
        # Slight boost for earlier sentences (often contain key context)
        position_boost = 1.15 if idx < 3 else 1.0
        sentence_scores.append((idx, sentence, score * position_boost))

    top_sentences = sorted(sentence_scores, key=lambda x: x[2], reverse=True)[:sentence_count]
    top_sentences.sort(key=lambda x: x[0])  # restore original order

    return " ".join(s[1] for s in top_sentences)


def _summarize_transformers(text: str, sentence_count: int = 5) -> str:
    """
    Placeholder for a Hugging Face Transformers (e.g. facebook/bart-large-cnn)
    summarization pipeline. Not used by default due to model size / RAM
    constraints on free hosting tiers. Implement this if deploying on a host
    with sufficient resources (e.g. >2GB RAM, GPU optional).
    """
    raise NotImplementedError(
        "Transformer-based summarization is not enabled by default. "
        "Install `transformers` + `torch` and implement this function to use it."
    )


def _summarize_llm_api(text: str, sentence_count: int = 5) -> str:
    """
    Placeholder for a real LLM-based summary (OpenAI, Anthropic, etc).
    Implement this with your own API key, e.g.:

        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": f"Summarize:\n\n{text}"}]
        )
        return response.content[0].text
    """
    raise NotImplementedError(
        "LLM API summarization is not configured. Set SUMMARIZER_ENGINE='llm_api' "
        "and implement _summarize_llm_api() with your API credentials."
    )


def summarize(text: str, sentence_count: int = 5) -> str:
    """
    Generate a short extractive summary of the given text.
    Falls back to a simple truncation if the text is too short to summarize
    meaningfully, or if the chosen engine fails for any reason.
    """
    text = (text or "").strip()
    if not text:
        return "No content available to summarize."

    word_total = len(text.split())
    if word_total < 40:
        return text  # Too short to meaningfully summarize

    try:
        if SUMMARIZER_ENGINE == "transformers":
            return _summarize_transformers(text, sentence_count)
        elif SUMMARIZER_ENGINE == "llm_api":
            return _summarize_llm_api(text, sentence_count)
        else:
            return _summarize_simple(text, sentence_count)
    except Exception:
        # Safe fallback: first few sentences
        sentences = text.split(". ")
        return ". ".join(sentences[:3]).strip() + ("." if not text.endswith(".") else "")
