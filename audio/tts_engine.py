"""
Text-to-speech generation using Edge-TTS, with pydub for speed adjustment
and format conversion (mp3/wav).

Edge-TTS requires an active internet connection (it streams from
Microsoft's edge read-aloud service). This is a reasonable tradeoff for a
free tool with natural-sounding neural voices; gTTS is a lower-quality
offline-friendlier fallback but produces far more robotic speech.
"""
import asyncio
import os
import uuid

import edge_tts
from pydub import AudioSegment

# A curated subset of Edge-TTS neural voices covering different genders/accents
VOICE_OPTIONS = {
    "Female (US)": "en-US-JennyNeural",
    "Male (US)": "en-US-GuyNeural",
    "Female (UK)": "en-GB-SoniaNeural",
    "Male (UK)": "en-GB-RyanNeural",
    "Female (Australia)": "en-AU-NatashaNeural",
    "Male (Australia)": "en-AU-WilliamNeural",
    "Female (India)": "en-IN-NeerjaNeural",
    "Male (India)": "en-IN-PrabhatNeural",
}

SPEED_OPTIONS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]


async def _generate_speech_async(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_speech(text: str, voice: str, output_dir: str, base_filename: str | None = None) -> str:
    """
    Generate speech audio (mp3) from text using Edge-TTS.
    Returns the path to the generated mp3 file.
    Raises RuntimeError with a friendly message on failure (e.g. no internet).
    """
    if not text or not text.strip():
        raise ValueError("No text provided for speech generation.")

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{base_filename or uuid.uuid4().hex}.mp3"
    output_path = os.path.join(output_dir, filename)

    try:
        asyncio.run(_generate_speech_async(text, voice, output_path))
    except Exception as exc:
        raise RuntimeError(
            "Audio generation failed. This usually means there is no internet "
            f"connection available, or the TTS service is temporarily unavailable. ({exc})"
        )

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError("Audio generation failed: no audio data was produced.")

    return output_path


def change_speed(input_path: str, speed: float, output_path: str) -> str:
    """
    Adjust playback speed of an audio file without changing pitch drastically
    (uses pydub's frame-rate trick, standard for speech speed adjustment).
    """
    audio = AudioSegment.from_file(input_path)
    if speed == 1.0:
        audio.export(output_path, format=os.path.splitext(output_path)[1].strip(".") or "mp3")
        return output_path

    new_frame_rate = int(audio.frame_rate * speed)
    adjusted = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
    adjusted = adjusted.set_frame_rate(audio.frame_rate)

    export_format = os.path.splitext(output_path)[1].strip(".") or "mp3"
    adjusted.export(output_path, format=export_format)
    return output_path


def convert_format(input_path: str, output_path: str) -> str:
    """Convert between mp3/wav using pydub."""
    audio = AudioSegment.from_file(input_path)
    export_format = os.path.splitext(output_path)[1].strip(".") or "mp3"
    audio.export(output_path, format=export_format)
    return output_path


def get_duration_seconds(audio_path: str) -> float:
    """Return audio duration in seconds."""
    try:
        audio = AudioSegment.from_file(audio_path)
        return round(len(audio) / 1000.0, 2)
    except Exception:
        return 0.0


def list_available_voices() -> dict:
    return VOICE_OPTIONS
