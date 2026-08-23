# File: backend/main.py

import json
import os
import tempfile
import traceback
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from asr import TranscriptionError, transcribe
from database import Base, engine, get_db
from models import Meeting, Summary, Transcript
from summarizer import SummarizationError, summarize


class ActionItem(BaseModel):
    """Represents one action item extracted from a meeting."""

    task: str
    owner: Optional[str] = None
    due_date: Optional[str] = None


class MeetingProcessResponse(BaseModel):
    """Response returned after successfully processing a meeting."""

    meeting_id: int
    filename: str
    transcript: str
    summary: str
    decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)


class MeetingListItem(BaseModel):
    """Summary information shown in the Past Meetings list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    created_at: datetime


class MeetingDetailResponse(BaseModel):
    """Complete details for a previously processed meeting."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    created_at: datetime
    transcript: str
    summary: str
    decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)


app = FastAPI(
    title="Meeting Summarizer API",
    version="1.0.0",
)


# Allow the local Streamlit frontend to access the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    """Create all database tables when the application starts."""

    Base.metadata.create_all(bind=engine)


def _is_supported_audio(filename: str) -> bool:
    """Check whether the uploaded filename has a supported audio extension."""

    allowed_extensions = {
        ".mp3",
        ".wav",
        ".m4a",
    }

    if not filename:
        return False

    extension = os.path.splitext(filename)[1].lower()

    return extension in allowed_extensions


@app.post(
    "/process-meeting",
    response_model=MeetingProcessResponse,
)
async def process_meeting(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Process an uploaded meeting audio file.

    Steps:
    1. Validate the audio file.
    2. Save it temporarily.
    3. Transcribe it using Groq Whisper.
    4. Generate a structured summary.
    5. Save the results in SQLite.
    6. Return the complete result.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No audio file was uploaded.",
        )

    if not _is_supported_audio(file.filename):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Please upload an MP3, WAV, or M4A file."
            ),
        )

    temp_path = None

    try:
        file_extension = os.path.splitext(
            file.filename
        )[1].lower()

        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        # Save the uploaded file temporarily.
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension,
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write(content)

        print("\n========== PROCESSING MEETING ==========")
        print(f"File: {file.filename}")
        print(f"Temporary path: {temp_path}")
        print(f"File size: {len(content)} bytes")

        # ---------------- TRANSCRIPTION ----------------

        print("\nStarting transcription...")

        try:
            transcript = transcribe(temp_path)

            print("Transcription completed successfully.")
            print(f"Transcript length: {len(transcript)} characters")

        except TranscriptionError as exc:
            print("\n========== TRANSCRIPTION ERROR ==========")
            print(f"Error: {exc}")
            traceback.print_exc()
            print("=========================================\n")

            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {exc}",
            ) from exc

        # ---------------- SUMMARIZATION ----------------

        print("\nStarting summarization...")

        try:
            summary_data = summarize(transcript)

            print("Summarization completed successfully.")

        except SummarizationError as exc:
            print("\n========== SUMMARIZATION ERROR ==========")
            print(f"Error: {exc}")
            traceback.print_exc()
            print("=========================================\n")

            raise HTTPException(
                status_code=500,
                detail=f"Summarization failed: {exc}",
            ) from exc

        # ---------------- DATABASE ----------------

        print("\nSaving meeting data to database...")

        try:
            # Create the meeting record.
            meeting = Meeting(
                filename=file.filename,
            )

            db.add(meeting)
            db.flush()

            # Create the transcript record.
            transcript_record = Transcript(
                meeting_id=meeting.id,
                text=transcript,
            )

            db.add(transcript_record)

            # Create the summary record.
            summary_record = Summary(
                meeting_id=meeting.id,
                summary_text=summary_data["summary"],
                decisions_json=json.dumps(
                    summary_data["key_decisions"]
                ),
                action_items_json=json.dumps(
                    summary_data["action_items"]
                ),
            )

            db.add(summary_record)

            db.commit()

            db.refresh(meeting)

            print("Database save completed successfully.")

        except Exception as exc:
            db.rollback()

            print("\n========== DATABASE ERROR ==========")
            print(f"Error: {exc}")
            traceback.print_exc()
            print("====================================\n")

            raise HTTPException(
                status_code=500,
                detail=f"Failed to save meeting data: {exc}",
            ) from exc

        print("\n========== MEETING COMPLETED ==========\n")

        return MeetingProcessResponse(
            meeting_id=meeting.id,
            filename=meeting.filename,
            transcript=transcript,
            summary=summary_data["summary"],
            decisions=summary_data["key_decisions"],
            action_items=[
                ActionItem(
                    task=item["task"],
                    owner=item["owner"],
                    due_date=item["due_date"],
                )
                for item in summary_data["action_items"]
            ],
        )

    except HTTPException:
        raise

    except Exception as exc:
        print("\n========== UNEXPECTED ERROR ==========")
        print(f"Error: {exc}")
        traceback.print_exc()
        print("======================================\n")

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {exc}",
        ) from exc

    finally:
        # Always close the uploaded file.
        await file.close()

        # Always delete the temporary file.
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("Temporary file deleted.")
            except OSError:
                pass


@app.get(
    "/meetings",
    response_model=List[MeetingListItem],
)
def list_meetings(
    db: Session = Depends(get_db),
):
    """
    Return all previously processed meetings,
    ordered from newest to oldest.
    """

    statement = (
        select(Meeting)
        .order_by(
            Meeting.created_at.desc(),
            Meeting.id.desc(),
        )
    )

    meetings = (
        db.execute(statement)
        .scalars()
        .all()
    )

    return meetings


@app.get(
    "/meetings/{meeting_id}",
    response_model=MeetingDetailResponse,
)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
):
    """
    Return the transcript and summary for one meeting.
    """

    meeting = db.get(
        Meeting,
        meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    if meeting.transcript is None:
        transcript_text = ""
    else:
        transcript_text = meeting.transcript.text

    if meeting.summary is None:
        summary_text = ""
        decisions = []
        action_items = []
    else:
        summary_text = meeting.summary.summary_text

        try:
            decisions = json.loads(
                meeting.summary.decisions_json
            )

            action_items = json.loads(
                meeting.summary.action_items_json
            )

        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Stored meeting summary contains "
                    "invalid JSON."
                ),
            ) from exc

    return MeetingDetailResponse(
        id=meeting.id,
        filename=meeting.filename,
        created_at=meeting.created_at,
        transcript=transcript_text,
        summary=summary_text,
        decisions=decisions,
        action_items=[
            ActionItem(
                task=item.get("task", ""),
                owner=item.get("owner"),
                due_date=item.get("due_date"),
            )
            for item in action_items
        ],
    )


@app.delete(
    "/meetings/{meeting_id}",
    status_code=204,
)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete one meeting and its related transcript and summary."""

    meeting = db.get(
        Meeting,
        meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    try:
        db.delete(meeting)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete meeting.",
        ) from exc