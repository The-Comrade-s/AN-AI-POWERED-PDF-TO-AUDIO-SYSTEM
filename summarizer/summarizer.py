"""
Summarization module.

Default engine: sumy (TextRank), a lightweight, pure-CPU, offline extractive
summarizer. Chosen over Hugging Face Transformers (BART/T5) because
transformer models require large downloads (400MB-1.5GB) and significant
RAM, which is not reliable on free-tier hosts like Streamlit Community Cloud
or Render's free plan (typically 512MB-1GB RAM). sumy gives fast, "good
enough" summaries with a negligible footprint, keeping the app deployable
out of the box.

The `summarize()` function is the single entry point used by the rest of
the app. To upgrade later:
    - Set SUMMARIZER_ENGINE = "transformers" and implement _summarize_transformers()
    - Or set SUMMARIZER_ENGINE = "llm_api" and implement _summarize_llm_api()
      (e.g. call the Anthropic or OpenAI API with your own key)
No other file needs to change.
"""
import os

import nltk

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words


def _ensure_nltk_data():
    """Download NLTK tokenizer data required by sumy, if not already present."""
    for resource in ["punkt", "punkt_tab"]:
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception:
                pass  # Fails gracefully; summarize() has its own fallback


_ensure_nltk_data()

# Options: "sumy" (default, offline, lightweight), "transformers", "llm_api"
SUMMARIZER_ENGINE = os.environ.get("SUMMARIZER_ENGINE", "sumy")

LANGUAGE = "english"


def _summarize_sumy(text: str, sentence_count: int = 5) -> str:
    if not text or not text.strip():
        return ""
    parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)
    summarizer = TextRankSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(LANGUAGE)

    sentences = summarizer(parser.document, sentence_count)
    return " ".join(str(s) for s in sentences)


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
            messages=[{"role": "user", "content": f"Summarize:\\n\\n{text}"}]
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
            return _summarize_sumy(text, sentence_count)
    except Exception:
        # Safe fallback: first few sentences
        sentences = text.split(". ")
        return ". ".join(sentences[:3]).strip() + ("." if not text.endswith(".") else "")
