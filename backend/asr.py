# File: backend/asr.py

import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq


# Load environment variables from the .env file.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)
print("GROQ key loaded:", bool(os.getenv("GROQ_API_KEY")))

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


class TranscriptionError(Exception):
    """Raised when audio transcription fails or the input is invalid."""


def transcribe(file_path: str) -> str:
    """
    Transcribe an audio file using Groq Whisper.

    Args:
        file_path: Path to the audio file.

    Returns:
        The cleaned transcript text.

    Raises:
        TranscriptionError: If validation, file reading,
        or Groq transcription fails.
    """

    if not file_path:
        raise TranscriptionError(
            "No audio file path was provided."
        )

    if not os.path.isfile(file_path):
        raise TranscriptionError(
            f"Audio file not found: {file_path}"
        )

    try:
        file_size = os.path.getsize(file_path)
    except OSError as exc:
        raise TranscriptionError(
            f"Unable to read the audio file: {exc}"
        ) from exc

    if file_size == 0:
        raise TranscriptionError(
            "Audio file is empty. Please upload a non-empty recording."
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        file_size_mb = file_size / (1024 * 1024)

        raise TranscriptionError(
            f"Audio file size is {file_size_mb:.2f} MB. "
            "Groq Whisper supports files up to 25 MB."
        )

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise TranscriptionError(
            "GROQ_API_KEY is not set. "
            "Please configure it in your .env file."
        )

    try:
        client = Groq(api_key=api_key)

        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                response_format="json",
            )

        text = getattr(transcript, "text", "")

        if not isinstance(text, str) or not text.strip():
            raise TranscriptionError(
                "The transcription completed, "
                "but no speech was detected."
            )

        return text.strip()

    except Exception as exc:
        raise TranscriptionError(
            f"Groq transcription failed: {exc}"
        ) from exc