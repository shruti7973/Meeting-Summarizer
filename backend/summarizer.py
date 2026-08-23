# File: backend/summarizer.py

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from groq import Groq


# Load the .env file from the project root.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


class SummarizationError(Exception):
    """Raised when summarization fails or the output is invalid."""


def _validate_summary_structure(payload: Any) -> Dict[str, Any]:
    """Validate and normalize the summary data."""

    if not isinstance(payload, dict):
        raise SummarizationError(
            "Summarizer output must be a JSON object."
        )

    required_keys = {
        "summary",
        "key_decisions",
        "action_items",
    }

    missing_keys = sorted(
        required_keys - set(payload.keys())
    )

    if missing_keys:
        raise SummarizationError(
            f"Missing required keys: {missing_keys}"
        )

    summary = payload.get("summary")
    key_decisions = payload.get("key_decisions")
    action_items = payload.get("action_items")

    if not isinstance(summary, str) or not summary.strip():
        raise SummarizationError(
            "Summary must be a non-empty string."
        )

    if not isinstance(key_decisions, list):
        raise SummarizationError(
            "key_decisions must be a list."
        )

    if not isinstance(action_items, list):
        raise SummarizationError(
            "action_items must be a list."
        )

    normalized_decisions: List[str] = []

    for decision in key_decisions:
        if isinstance(decision, str) and decision.strip():
            normalized_decisions.append(
                decision.strip()
            )

    normalized_actions: List[Dict[str, Any]] = []

    for item in action_items:
        if not isinstance(item, dict):
            raise SummarizationError(
                "Each action item must be a JSON object."
            )

        task = item.get("task")
        owner = item.get("owner")
        due_date = item.get("due_date")

        if not isinstance(task, str) or not task.strip():
            raise SummarizationError(
                "Each action item must contain a non-empty task."
            )

        if owner is not None and not isinstance(owner, str):
            raise SummarizationError(
                "Action item owner must be a string or null."
            )

        if due_date is not None and not isinstance(
            due_date,
            str,
        ):
            raise SummarizationError(
                "Action item due_date must be a string or null."
            )

        normalized_actions.append(
            {
                "task": task.strip(),
                "owner": (
                    owner.strip()
                    if isinstance(owner, str) and owner.strip()
                    else None
                ),
                "due_date": (
                    due_date.strip()
                    if isinstance(due_date, str)
                    and due_date.strip()
                    else None
                ),
            }
        )

    return {
        "summary": summary.strip(),
        "key_decisions": normalized_decisions,
        "action_items": normalized_actions,
    }


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    """Extract and parse a JSON object from model output."""

    if not isinstance(raw_text, str) or not raw_text.strip():
        raise SummarizationError(
            "The model returned an empty response."
        )

    cleaned = raw_text.strip()

    # Attempt 1: Direct JSON.
    try:
        return _validate_summary_structure(
            json.loads(cleaned)
        )
    except json.JSONDecodeError:
        pass

    # Attempt 2: Remove Markdown code fences.
    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    ).strip()

    try:
        return _validate_summary_structure(
            json.loads(cleaned)
        )
    except json.JSONDecodeError:
        pass

    # Attempt 3: Find JSON object.
    start_index = cleaned.find("{")
    end_index = cleaned.rfind("}")

    if (
        start_index != -1
        and end_index != -1
        and end_index > start_index
    ):
        json_candidate = cleaned[
            start_index:end_index + 1
        ]

        try:
            return _validate_summary_structure(
                json.loads(json_candidate)
            )
        except json.JSONDecodeError as exc:
            raise SummarizationError(
                "The model returned malformed JSON."
            ) from exc

    raise SummarizationError(
        "Failed to parse the model output as valid JSON."
    )


def summarize(transcript: str) -> Dict[str, Any]:
    """Generate a structured meeting summary using Groq."""

    if not isinstance(transcript, str) or not transcript.strip():
        raise SummarizationError(
            "Transcript is empty or invalid."
        )

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise SummarizationError(
            "GROQ_API_KEY is not set. "
            "Please configure it in your .env file."
        )

    system_prompt = """
You summarize meeting transcripts accurately.

Use ONLY information explicitly stated in the transcript.

Do not invent decisions, tasks, owners, due dates,
facts, or agreements.

A key decision must be explicitly made or agreed upon.

An action item must be an explicitly assigned or agreed task.

Return exactly one JSON object with these keys:
summary
key_decisions
action_items
""".strip()

    user_prompt = f"""
Return this exact JSON structure:

{{
  "summary": "Concise meeting summary",
  "key_decisions": [],
  "action_items": []
}}

For each action item use:

{{
  "task": "Task description",
  "owner": null,
  "due_date": null
}}

Use null if owner or due_date was not explicitly stated.

Meeting transcript:

{transcript}
""".strip()

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0,
            max_completion_tokens=3000,
        )

        if not response.choices:
            raise SummarizationError(
                "Groq returned no completion choices."
            )

        choice = response.choices[0]
        message = choice.message

        # Get only the final answer.
        raw_output = message.content

        if not raw_output or not raw_output.strip():
            raise SummarizationError(
                "Groq returned an empty response. "
                f"Finish reason: {choice.finish_reason}"
            )

        # TEMPORARY DEBUG OUTPUT
        print("\n========== GROQ RAW RESPONSE ==========")
        print(raw_output)
        print("=======================================\n")

        return _extract_json_object(raw_output)

    except SummarizationError:
        raise

    except Exception as exc:
        raise SummarizationError(
            f"Groq summarization failed: {exc}"
        ) from exc