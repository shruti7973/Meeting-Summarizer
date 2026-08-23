# File: frontend/app.py

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


# Backend API URL can be configured through an environment variable.
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000",
)

ALLOWED_EXTENSIONS = {
    "mp3",
    "wav",
    "m4a",
}

MAX_AUDIO_SIZE_MB = 25
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024


# -----------------------------------------------------------------------
# Styling
# -----------------------------------------------------------------------

def _inject_custom_css() -> None:
    """
    Inject custom CSS for a clean, product-style look
    (inspired by modern AI-tool landing pages: centered hero,
    a big upload card, and a card grid for past meetings).

    Purely cosmetic — does not touch any app logic.
    """

    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

            :root {
                --accent: #0B7A75;
                --accent-dark: #075A57;
                --accent-soft: #E3F3F0;
                --ink: #142332;
                --muted: #617181;
                --border: #DCE5E8;
                --card-bg: #FFFFFF;
                --surface: #F2F6F5;
                --warm: #F7F3EA;
            }

            .main {
                background: linear-gradient(180deg, #F7FAF9 0%, #FFFFFF 38%);
            }

            .block-container {
                padding: 2.25rem 2rem 4rem;
                max-width: 1160px;
            }

            html, body, [class*="css"] {
                font-family: 'DM Sans', sans-serif;
                color: var(--ink);
            }

            /* ---------- Hero ---------- */
            .hero-wrap {
                text-align: left;
                margin: 1rem 0 2.25rem;
                padding: 0 0.35rem;
            }
            .hero-wrap h1 {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 3.8rem;
                font-weight: 700;
                color: var(--ink);
                margin: 0;
                line-height: 1.03;
                letter-spacing: -0.03em;
            }
            .hero-wrap p {
                color: var(--muted);
                font-size: 1rem;
                max-width: 600px;
                margin: 1rem 0 0;
                line-height: 1.65;
            }

            .upload-caption {
                color: var(--muted);
                font-size: 0.95rem;
                margin-bottom: 1.1rem;
            }
            .format-pill-row {
                display: flex;
                justify-content: center;
                gap: 0.5rem;
                margin-top: 1rem;
                flex-wrap: wrap;
            }
            .format-pill {
                background-color: #FFFFFF;
                border: 1px solid var(--border);
                color: var(--muted);
                font-size: 0.8rem;
                font-weight: 600;
                padding: 0.25rem 0.75rem;
                border-radius: 999px;
            }

            [data-testid="stFileUploaderDropzone"] {
                background-color: #FFFFFF;
                border: 1px solid var(--border);
                border-radius: 12px;
            }

            div.stButton > button {
                border-radius: 9px;
                font-weight: 700;
                min-height: 2.65rem;
                padding: 0.5rem 1.15rem;
                border: 1px solid var(--border);
                transition: all 0.18s ease-in-out;
            }
            div.stButton > button[kind="primary"] {
                background-color: var(--accent);
                border-color: var(--accent);
                box-shadow: 0 5px 12px rgba(11, 122, 117, 0.22);
            }
            div.stButton > button[kind="primary"]:hover {
                background-color: var(--accent-dark);
                border-color: var(--accent-dark);
                transform: translateY(-1px);
            }
            div.stButton > button:hover {
                border-color: var(--accent);
                color: var(--accent-dark);
            }

            /* ---------- Section cards (results) ---------- */
            .section-card {
                background-color: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1.4rem 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 5px 18px rgba(20, 35, 50, 0.045);
            }
            .section-card h3, .section-card h4 {
                margin-top: 0 !important;
            }

            .status-pill {
                display: inline-block;
                padding: 0.15rem 0.65rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
            }
            .status-pill-success {
                background-color: #E6F4EA;
                color: #1E7A34;
            }
            .status-pill-neutral {
                background-color: var(--accent-soft);
                color: var(--accent);
            }

            /* ---------- Past meetings card grid ---------- */
            .meeting-card {
                background-color: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1.15rem;
                margin-bottom: 0.9rem;
                min-height: 148px;
                transition: box-shadow 0.18s ease-in-out, transform 0.18s ease-in-out;
            }
            .meeting-card:hover {
                box-shadow: 0 10px 24px rgba(20, 35, 50, 0.1);
                transform: translateY(-2px);
            }
            .meeting-card-top {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                margin-bottom: 0.6rem;
            }
            .meeting-icon {
                width: 34px;
                height: 34px;
                min-width: 34px;
                border-radius: 9px;
                background: var(--accent-soft);
                color: var(--accent);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }
            .meeting-title {
                font-family: 'Space Grotesk', sans-serif;
                font-weight: 700;
                color: var(--ink);
                font-size: 0.92rem;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            section[data-testid="stSidebar"] {
                background-color: #EDF4F2;
                border-right: 1px solid var(--border);
            }
            section[data-testid="stSidebar"] .block-container {
                padding-top: 1.5rem;
            }

            hr {
                margin: 1.75rem 0;
                border-color: var(--border);
            }

            details {
                border-radius: 9px !important;
                border: 1px solid var(--border) !important;
            }

            @media (max-width: 640px) {
                .block-container {
                    padding: 1.25rem 1rem 3rem;
                }
                .hero-wrap {
                    margin-top: 0.5rem;
                }
                .hero-wrap h1 {
                    font-size: 2.35rem;
                }
                .section-card {
                    padding: 1.1rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section_header(icon: str, title: str) -> None:
    """
    Render a consistent, styled section header used across cards.
    """

    st.markdown(
        f"#### {icon}&nbsp;&nbsp;{title}",
        unsafe_allow_html=False,
    )


# -----------------------------------------------------------------------
# Rendering helpers (logic unchanged — presentation only)
# -----------------------------------------------------------------------

def _display_action_items(
    action_items: List[Dict[str, Any]],
) -> None:
    """
    Display action items in a table.

    Missing owners and due dates are displayed as
    'Not mentioned'.
    """

    if not action_items:
        st.info(
            "No action items were identified in this meeting."
        )
        return

    rows = []

    for item in action_items:
        owner = item.get("owner")
        due_date = item.get("due_date")

        rows.append(
            {
                "Task": item.get("task", ""),
                "Owner": (
                    owner
                    if owner
                    else "Not mentioned"
                ),
                "Due Date": (
                    due_date
                    if due_date
                    else "Not mentioned"
                ),
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )


def _render_meeting_result(
    result: Dict[str, Any],
) -> None:
    """
    Render a meeting's transcript, summary, decisions,
    and action items.

    The same function is used for newly processed meetings
    and previously stored meetings.
    """

    # --- Summary ---
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _section_header("📝", "Summary")

        summary = result.get("summary", "")

        if summary:
            st.write(summary)
        else:
            st.info("No summary is available.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Key Decisions ---
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _section_header("✅", "Key Decisions")

        decisions = (
            result.get("decisions")
            or result.get("key_decisions")
            or []
        )

        if not decisions:
            st.info(
                "No key decisions were identified in this meeting."
            )
        else:
            for decision in decisions:
                st.markdown(f"- {decision}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Action Items ---
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _section_header("📌", "Action Items")

        action_items = (
            result.get("action_items")
            or []
        )

        _display_action_items(action_items)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Full Transcript ---
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        _section_header("📄", "Full Transcript")

        with st.expander(
            "View full transcript",
            expanded=False,
        ):
            transcript = result.get("transcript", "")

            if transcript:
                st.write(transcript)
            else:
                st.info("No transcript is available.")
        st.markdown("</div>", unsafe_allow_html=True)


def _load_meetings() -> List[Dict[str, Any]]:
    """
    Load all previously processed meetings.
    """

    try:
        response = requests.get(
            f"{BACKEND_URL}/meetings",
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:
        st.error(
            f"Could not load past meetings: {exc}"
        )

        return []


def _load_meeting_details(
    meeting_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Load complete details for a selected meeting.
    """

    try:
        response = requests.get(
            f"{BACKEND_URL}/meetings/{meeting_id}",
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:
        st.error(
            f"Could not load meeting details: {exc}"
        )

        return None


def _delete_meeting(meeting_id: int) -> bool:
    """Delete one stored meeting through the backend API."""

    try:
        response = requests.delete(
            f"{BACKEND_URL}/meetings/{meeting_id}",
            timeout=10,
        )

        if response.status_code == 404:
            st.error("That meeting no longer exists.")
            return False

        response.raise_for_status()
        return True

    except requests.RequestException as exc:
        st.error(f"Could not delete meeting: {exc}")
        return False


def _format_meeting_date(value: str) -> str:
    """Format a stored meeting timestamp for the history panel."""

    try:
        meeting_date = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
        formatted_date = meeting_date.strftime(
            "%b %d, %Y at %I:%M %p"
        )
        return formatted_date.replace(" 0", " ").replace(" at 0", " at ")
    except (AttributeError, TypeError, ValueError):
        return "Date unavailable"


def _render_sidebar_history() -> None:
    """Render saved meetings as selectable items in the sidebar."""

    meetings = _load_meetings()

    st.markdown("### Meeting History")

    if not meetings:
        st.caption("No saved meetings yet.")
        return

    st.caption(f"{len(meetings)} saved meeting(s)")

    for meeting in meetings:
        meeting_id = meeting["id"]
        details = _load_meeting_details(meeting_id)
        summary = details.get("summary", "") if details else ""
        preview = " ".join(summary.split())

        if len(preview) > 88:
            preview = f"{preview[:88].rstrip()}..."

        item_col, delete_col = st.columns([5, 1])

        with item_col:
            if st.button(
                f"📄  {meeting['filename']}",
                key=f"sidebar_meeting_{meeting_id}",
                use_container_width=True,
                type=(
                    "primary"
                    if st.session_state.get("selected_meeting", {}).get("id")
                    == meeting_id
                    else "secondary"
                ),
            ):
                if details:
                    st.session_state["selected_meeting"] = details
                    st.session_state.pop("result", None)
                    st.rerun()

            st.caption(
                _format_meeting_date(meeting.get("created_at", ""))
            )
            st.markdown(
                preview or "No summary preview available.",
                unsafe_allow_html=False,
            )

        with delete_col:
            if st.button(
                "🗑️",
                key=f"sidebar_delete_{meeting_id}",
                help="Delete this meeting",
            ):
                st.session_state["confirm_delete_meeting"] = meeting_id
                st.rerun()

        if st.session_state.get("confirm_delete_meeting") == meeting_id:
            st.warning(
                f"Permanently delete {meeting['filename']}?"
            )
            confirm_col, cancel_col = st.columns(2)

            with confirm_col:
                if st.button(
                    "Confirm",
                    key=f"sidebar_confirm_delete_{meeting_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    if _delete_meeting(meeting_id):
                        st.session_state.pop(
                            "confirm_delete_meeting",
                            None,
                        )
                        if (
                            st.session_state.get(
                                "selected_meeting",
                                {},
                            ).get("id")
                            == meeting_id
                        ):
                            st.session_state.pop(
                                "selected_meeting",
                                None,
                            )
                        st.session_state[
                            "deletion_success"
                        ] = "Meeting deleted successfully."
                        st.rerun()

            with cancel_col:
                if st.button(
                    "Cancel",
                    key=f"sidebar_cancel_delete_{meeting_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(
                        "confirm_delete_meeting",
                        None,
                    )
                    st.rerun()


def _render_past_meetings_grid(
    meetings: List[Dict[str, Any]],
) -> None:
    """
    Render past meetings as a card grid (3 columns), each card showing
    the filename, its ID as a badge, and a Load button.

    Uses the same _load_meeting_details() call and the same
    session_state keys as before — only the trigger UI changed
    from a selectbox to per-card buttons.
    """

    st.markdown("### 🕘 Recent Meetings")
    st.caption(f"{len(meetings)} meeting(s) processed so far")

    columns_per_row = 3
    rows_needed = -(-len(meetings) // columns_per_row)  # ceil division

    meeting_iter = iter(meetings)

    for _ in range(rows_needed):
        cols = st.columns(columns_per_row)

        for col in cols:
            try:
                meeting = next(meeting_iter)
            except StopIteration:
                break

            with col:
                st.markdown(
                    f"""
                    <div class="meeting-card">
                        <div class="meeting-card-top">
                            <div class="meeting-icon">🎙️</div>
                            <div class="meeting-title" title="{meeting['filename']}">
                                {meeting['filename']}
                            </div>
                        </div>
                        <span class="status-pill status-pill-neutral">
                            ID: {meeting['id']}
                        </span>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Load",
                    key=f"load_meeting_{meeting['id']}",
                    use_container_width=True,
                ):
                    details = _load_meeting_details(meeting["id"])

                    if details:
                        st.session_state["selected_meeting"] = details

                        # Clear previous processing result so the
                        # UI does not show two unrelated meetings.
                        st.session_state.pop("result", None)

                        st.rerun()

                if st.button(
                    "Delete",
                    key=f"delete_meeting_{meeting['id']}",
                    use_container_width=True,
                ):
                    st.session_state["confirm_delete_meeting"] = meeting["id"]
                    st.rerun()

                if (
                    st.session_state.get("confirm_delete_meeting")
                    == meeting["id"]
                ):
                    st.warning(
                        f"Permanently delete {meeting['filename']}?"
                    )

                    confirm_col, cancel_col = st.columns(2)

                    with confirm_col:
                        if st.button(
                            "Confirm Delete",
                            key=f"confirm_delete_{meeting['id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            if _delete_meeting(meeting["id"]):
                                st.session_state.pop(
                                    "confirm_delete_meeting",
                                    None,
                                )
                                st.session_state.pop(
                                    "selected_meeting",
                                    None,
                                )
                                st.session_state[
                                    "deletion_success"
                                ] = "Meeting deleted successfully."
                                st.rerun()

                    with cancel_col:
                        if st.button(
                            "Cancel",
                            key=f"cancel_delete_{meeting['id']}",
                            use_container_width=True,
                        ):
                            st.session_state.pop(
                                "confirm_delete_meeting",
                                None,
                            )
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    """
    Build and run the Meeting Summarizer interface.
    """

    st.set_page_config(
        page_title="Meeting Summarizer",
        page_icon="🎙️",
        layout="wide",
    )

    _inject_custom_css()

    if "deletion_success" in st.session_state:
        st.success(
            st.session_state.pop("deletion_success")
        )

    # -----------------------------
    # Sidebar: Branding + History
    # -----------------------------

    with st.sidebar:
        st.markdown("## 🎙️ MeetingAI")
        st.caption("Transcribe. Summarize. Act.")
        st.markdown("---")

        if st.button(
            "🆕 New Summary",
            use_container_width=True,
            help="Clear the currently displayed result.",
        ):
            st.session_state.pop("result", None)
            st.session_state.pop("selected_meeting", None)
            st.session_state.pop("confirm_delete_meeting", None)
            st.session_state.pop("meeting_audio_upload", None)
            st.rerun()

        if st.button(
            "🔄 Refresh History",
            use_container_width=True,
            help="Fetch the latest saved meetings.",
        ):
            st.rerun()

        st.markdown("---")
        _render_sidebar_history()

    # -----------------------------
    # Hero
    # -----------------------------

    st.markdown(
        """
        <div class="hero-wrap">
            <h1>Meeting Summarizer</h1>
            <p>
                Upload a meeting recording to automatically generate a
                transcript, summary, key decisions, and action items —
                in seconds.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------
    # Upload Audio
    # -----------------------------

    st.markdown(
        """
        <div class="upload-caption">
            Drop an audio file below, or click to browse
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload an audio file",
        key="meeting_audio_upload",
        type=sorted(ALLOWED_EXTENSIONS),
        accept_multiple_files=False,
        help=(
            "Supported formats: MP3, WAV, and M4A. "
            "Maximum file size supported by the transcription "
            "API is 25 MB."
        ),
        label_visibility="collapsed",
    )

    uploaded_file_bytes = b""

    if uploaded_file is not None:
        uploaded_file_bytes = uploaded_file.getvalue()
        size_mb = len(uploaded_file_bytes) / (1024 * 1024)

        if len(uploaded_file_bytes) > MAX_AUDIO_SIZE_BYTES:
            st.error("Audio file size must be 25 MB or less.")

    st.markdown(
        """
        <div class="format-pill-row">
            <span class="format-pill">MP3</span>
            <span class="format-pill">WAV</span>
            <span class="format-pill">M4A</span>
            <span class="format-pill">Max 25 MB</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if uploaded_file is not None:
        st.markdown(
            f"""
            <div style="margin-top:1rem;">
                <span class="status-pill status-pill-success">
                    ✓ {uploaded_file.name} ({size_mb:.1f} MB)
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    process_button = st.button(
        "▶️  Process Meeting",
        disabled=(
            uploaded_file is None
            or len(uploaded_file_bytes) > MAX_AUDIO_SIZE_BYTES
        ),
        type="primary",
        use_container_width=False,
    )

    # -----------------------------
    # Process Meeting
    # -----------------------------

    if process_button and uploaded_file is not None:

        file_name = uploaded_file.name

        if not file_name:
            st.error(
                "The uploaded file does not have a valid filename."
            )
            return

        extension = os.path.splitext(
            file_name
        )[1].lower().lstrip(".")

        if extension not in ALLOWED_EXTENSIONS:
            st.error(
                "Unsupported file type. "
                "Please choose an MP3, WAV, or M4A file."
            )
            return

        files = {
            "file": (
                file_name,
                uploaded_file_bytes,
                uploaded_file.type
                or "application/octet-stream",
            )
        }

        try:
            with st.spinner(
                "Transcribing and summarizing the meeting..."
            ):

                response = requests.post(
                    f"{BACKEND_URL}/process-meeting",
                    files=files,
                    timeout=180,
                )

            if response.status_code == 400:
                try:
                    error_message = response.json().get(
                        "detail",
                        "Invalid audio upload.",
                    )
                except ValueError:
                    error_message = response.text

                st.error(error_message)
                return

            if response.status_code >= 500:
                try:
                    error_message = response.json().get(
                        "detail",
                        "The backend could not process the meeting.",
                    )
                except ValueError:
                    error_message = response.text

                st.error(error_message)
                return

            response.raise_for_status()

            result = response.json()

            st.session_state["result"] = result

            # Clear any previously selected past meeting.
            st.session_state.pop(
                "selected_meeting",
                None,
            )

            st.success(
                "Meeting processed successfully!"
            )

        except requests.RequestException as exc:
            st.error(
                "Failed to connect to the backend. "
                f"Details: {exc}"
            )
            return

    # -----------------------------
    # Display Newly Processed Result
    # -----------------------------

    if "result" in st.session_state:
        st.divider()

        st.markdown("### 📊 Meeting Results")

        _render_meeting_result(
            st.session_state["result"]
        )

    # -----------------------------
    # Display Selected Past Meeting
    # -----------------------------

    if "selected_meeting" in st.session_state:
        st.divider()

        st.markdown("### 🕘 Selected Past Meeting")

        _render_meeting_result(
            st.session_state["selected_meeting"]
        )

    # -----------------------------
    # Past Meetings Grid
    # -----------------------------

    if (
        "result" not in st.session_state
        and "selected_meeting" not in st.session_state
    ):
        meetings = _load_meetings()

        if meetings:
            st.divider()
            _render_past_meetings_grid(meetings)


if __name__ == "__main__":
    main()