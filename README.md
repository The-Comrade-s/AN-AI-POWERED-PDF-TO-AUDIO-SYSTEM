# 🎧 PDF to Audio AI

A production-quality AI-powered PDF-to-Audiobook web application built with Streamlit, SQLAlchemy, PyMuPDF, and Edge-TTS. Built as a final-year software engineering project with a commercial SaaS-grade interface.

---

## ✨ Features

- Secure authentication (register, login, forgot password, bcrypt password hashing)
- Drag-and-drop PDF upload with validation (size, corruption, encryption checks)
- Automatic text extraction, cleaning, and chapter/heading detection
- Offline AI summarization (extractive, TextRank via `sumy`)
- Text-to-speech conversion via Edge-TTS (8 neural voices, multiple accents/genders)
- Adjustable playback speed (0.5x–2x), MP3/WAV export
- Full audio player: play/pause, next/previous chapter, seek, volume, download
- Resume listening from last position
- Bookmarks, timestamped notes, listening history
- Personal library with search, sort, and filters
- Per-user data isolation — every user only sees their own content
- Dark, glassmorphism, purple-gradient SaaS-style UI

---

## 🏗️ Architecture

```
pdf2audio/
├── app.py                  # Main entry point & page router
├── auth/                   # Registration, login, password hashing
├── database/               # SQLAlchemy models (Users, PDFs, AudioFiles, etc.)
├── pdf_processor/          # Text extraction, cleaning, chapter detection
├── audio/                  # Edge-TTS speech generation, speed/format conversion
├── summarizer/             # Offline extractive summarization (pluggable)
├── pages_app/              # Streamlit page views (dashboard, library, player...)
├── assets/                 # CSS and thumbnails
├── uploads/                # User-uploaded PDFs (per-user subfolders)
├── generated_audio/        # Generated audio files (per-user subfolders)
├── requirements.txt
├── packages.txt            # System packages (ffmpeg) for deployment
└── .streamlit/config.toml  # Theme & server config
```

---

## ⚙️ Local Installation

**Requirements:** Python 3.10+, ffmpeg installed on your system (required by `pydub` for audio speed/format conversion).

```bash
# 1. Clone / unzip the project
cd pdf2audio

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install ffmpeg (if not already installed)
#    macOS:   brew install ffmpeg
#    Ubuntu:  sudo apt install ffmpeg
#    Windows: choco install ffmpeg   (or download from ffmpeg.org)

# 5. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`. A local SQLite database (`pdf2audio.db`) is created automatically on first run.

---

## ☁️ Deployment

### Option A: Streamlit Community Cloud (recommended, free)

1. Push this project to a public (or private) GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account.
3. Click **New app**, select the repo, branch, and set the main file to `app.py`.
4. Streamlit Cloud automatically installs `requirements.txt` **and** `packages.txt` (which installs `ffmpeg` — required for audio processing).
5. Deploy. Your app gets a public URL like `https://yourapp.streamlit.app`.

**Important:** Streamlit Cloud's free tier has an ephemeral filesystem — uploaded PDFs, generated audio, and the SQLite database are wiped on redeploy/restart. This is fine for a live demo/defense but not for long-term production storage (see "Known Limitations" below).

### Option B: Render

1. Push the project to GitHub.
2. Create a new **Web Service** on [render.com](https://render.com), connect your repo.
3. **Build command:** `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`
4. **Start command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Choose the free instance tier. Same ephemeral-storage caveat as above applies.

---

## 🧠 Engineering Notes & Tradeoffs (useful for your defense)

- **Why SQLite, not PostgreSQL:** Zero-config, file-based, ships with Python, and perfectly sufficient for a single-instance academic demo. The SQLAlchemy ORM layer means swapping to PostgreSQL later only requires changing the `DB_PATH` connection string in `database/models.py` — no other code changes needed.
- **Why Edge-TTS over gTTS:** Edge-TTS uses Microsoft's neural voices, which sound significantly more natural than gTTS's basic synthesis, at no cost and no API key. The tradeoff is that it requires an active internet connection (it streams from Microsoft's service) — there is no fully offline neural TTS option that's both free and high quality.
- **Why an offline extractive summarizer (sumy/TextRank) instead of a transformer model (BART/T5):** Transformer summarization models are large (400MB–1.5GB) and need meaningful RAM/CPU to run inference, which is unreliable on free-tier hosts like Streamlit Community Cloud or Render's free plan (~512MB–1GB RAM). `sumy` runs instantly on pure CPU with negligible memory, keeping the app reliably deployable. The summarizer module (`summarizer/summarizer.py`) is written with a pluggable interface — swapping in a Transformers pipeline or an LLM API (OpenAI/Anthropic) later is a one-function change, no other files need to be touched.
- **Chapter detection:** Uses regex heuristics (heading patterns, "Chapter N", all-caps lines) rather than a trained model — fast, dependency-free, and transparent to explain to examiners, though it can miss unconventional formatting.
- **Playback speed without pitch distortion:** Handled via `pydub`'s frame-rate resampling technique, the standard lightweight approach for speech speed changes without needing a full-blown audio DSP library.

## ⚠️ Known Limitations

- Ephemeral storage on free hosting tiers means uploaded files and the database reset on redeploy — acceptable for a live demo, not for production persistence. For true production use, swap SQLite for a managed Postgres instance and file storage for S3/Cloudinary.
- Edge-TTS requires internet access; if the deployment environment blocks outbound requests, audio generation will fail with a clear error message.
- Chapter detection is heuristic-based and works best on documents with conventional heading structures.
- OCR for scanned/image-only PDFs is not included; such files will be rejected with a friendly error message.

---

## 🔑 Default Ports & URLs

- Local: `http://localhost:8501`
- Streamlit Cloud: assigned public `.streamlit.app` URL
- Render: assigned public `.onrender.com` URL

---

Built with Python, Streamlit, SQLAlchemy, PyMuPDF, Edge-TTS, and pydub.
