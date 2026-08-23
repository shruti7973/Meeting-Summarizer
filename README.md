<<<<<<< HEAD
# Meeting Summarizer

Meeting Summarizer is a full-stack Python application that lets a user upload a meeting recording, transcribe it with OpenAI Whisper, summarize the discussion with GPT-4o-mini, and persist the transcript and structured output in SQLite for later review. It is designed as a practical hiring-assessment project that demonstrates end-to-end AI processing in a simple but production-minded architecture.

## Architecture Overview

```text
Streamlit Frontend
        |
        v
   FastAPI Backend
      /          \
     v            v
 Whisper ASR   GPT-4o-mini
      \          /
       v        v
       SQLite Storage
```

## Setup Instructions

1. Clone or open the repository in your local environment.
2. Create a Python virtual environment in the project root:

   Windows (PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Install frontend dependencies:
   ```bash
   cd ../frontend
   pip install -r requirements.txt
   ```

5. Copy the environment example file and add your API key:
   ```bash
   cd ..
   copy .env.example .env
   ```

   Then open `.env` and set your `OPENAI_API_KEY`.

6. Start the backend from the backend directory:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

7. Start the frontend from the frontend directory in another terminal:
   ```bash
   cd frontend
   streamlit run app.py
   ```

## API Endpoint Documentation

### POST /process-meeting
- Purpose: Upload an audio file, transcribe it, summarize it, and save the result.
- Accepted file types: `.mp3`, `.wav`, `.m4a`
- Request body: multipart form-data with a file field named `file`
- Success response:
  ```json
  {
    "meeting_id": 1,
    "filename": "team-sync.mp3",
    "transcript": "Full transcript text goes here.",
    "summary": "The team aligned on the rollout timing and agreed on next steps.",
    "decisions": ["Launch in Q3", "Finalize onboarding plan"],
    "action_items": [
      {
        "task": "Send the updated roadmap",
        "owner": "Alicia",
        "due_date": "2026-09-01"
      }
    ]
  }
  ```
- Error responses:
  - HTTP 400 for unsupported file types or invalid uploads
  - HTTP 500 for transcription or summarization errors

### GET /meetings
- Purpose: List all stored meetings in reverse chronological order.
- Response shape:
  ```json
  [
    {
      "id": 1,
      "filename": "team-sync.mp3",
      "created_at": "2026-08-21T12:00:00"
    }
  ]
  ```

### GET /meetings/{meeting_id}
- Purpose: Fetch a single meeting’s full transcript and summary payload.
- Response shape:
  ```json
  {
    "id": 1,
    "filename": "team-sync.mp3",
    "created_at": "2026-08-21T12:00:00",
    "transcript": "Full transcript.",
    "summary": "Summary text.",
    "decisions": ["Decision 1"],
    "action_items": [
      {
        "task": "Follow up with vendor",
        "owner": null,
        "due_date": null
      }
    ]
  }
  ```

## Example Meeting Transcript

"Thanks everyone for joining. We reviewed the launch timeline for the new onboarding flow and decided to move the release to September 15. Priya will own the final QA checklist, and Maya will coordinate the customer communication plan. We also agreed to follow up with the sales team on pricing before the final signoff. No additional decisions were made regarding the legal review, and we will revisit that next week."

## Example JSON Output

```json
{
  "summary": "The team agreed to move the onboarding launch to September 15 and confirmed that Priya will own the final QA checklist. Maya will coordinate the customer communication plan, and the sales team will provide pricing feedback before final signoff. The discussion focused on timing, ownership, and decision readiness before launch. No additional decisions were made on the legal review, which will be revisited next week.",
  "key_decisions": [
    "Move the onboarding launch to September 15",
    "Priya owns the final QA checklist",
    "Maya coordinates the customer communication plan"
  ],
  "action_items": [
    {
      "task": "Finalize the QA checklist",
      "owner": "Priya",
      "due_date": null
    },
    {
      "task": "Coordinate customer communication plan",
      "owner": "Maya",
      "due_date": null
    },
    {
      "task": "Follow up with the sales team on pricing",
      "owner": null,
      "due_date": null
    }
  ]
}
```

## Design Decisions

- Whisper API over local or open-source Whisper because it offers the simplest setup and infrastructure requirements for a demo project.
- GPT-4o-mini because it balances quality, speed, and cost for structured summarization tasks.
- SQLite because it requires no external database setup and works well for a hiring-assessment demo app.

## Known Limitations / Future Improvements

- No speaker diarization
- No automatic chunking for files larger than 25 MB
- No authentication or user management
- Could add streaming transcription
- Could add speaker labels and timestamps
- Could add a background task queue for larger meetings

## Troubleshooting

### Missing OPENAI_API_KEY
Ensure the `.env` file exists and contains a valid `OPENAI_API_KEY` value. If it is missing, the backend will fail when attempting transcription or summarization.

### OpenAI API errors
Check your API key, internet connection, and account quota. The backend returns a clear error message when the OpenAI SDK call fails.

### File exceeds 25 MB
The application rejects files larger than 25 MB before sending them to Whisper. Use a shorter recording or reduce the file size.

### Frontend cannot connect to backend
Verify the backend is running with:
```bash
uvicorn main:app --reload
```

Then confirm the frontend is using the correct `BACKEND_URL` value, which defaults to `http://localhost:8000`.

### Unsupported audio format
Upload only `.mp3`, `.wav`, or `.m4a` files. The app explicitly rejects unsupported extensions.

## Demo Notes

This project is intended to be simple, reliable, and easy to demonstrate in a short hiring-assessment presentation. It focuses on the end-to-end workflow: upload audio, transcribe, summarize, save results, and review the history.
=======
# Meeting-Summarizer
>>>>>>> 696dc46d5213af41887e9118bcb67eeafe8dd933
