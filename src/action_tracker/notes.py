# Tool 1 logic: read_note()
# Plain Python only. No MCP code in this file.
# Rules come from mcp-server-design.md, section 5.

import os
from pathlib import Path

MAX_BYTES = 1_000_000  # 1 MB limit for a note
ALLOWED_EXTENSIONS = {".md", ".txt"}

# Project folder = two levels above this file (src/action_tracker/notes.py)
PROJECT_DIR = Path(__file__).resolve().parents[2]


class NoteError(Exception):
    """Raised when a note cannot be read. The message is safe to show to users."""


def default_notes_dir() -> Path:
    """NOTES_DIR from the environment, or notes/ in the project folder."""
    value = os.environ.get("NOTES_DIR")
    return Path(value) if value else PROJECT_DIR / "notes"


def _check_filename(filename: object) -> list[str]:
    """Rule 1: must be a clean relative path like 'a.md' or 'sub/a.md'."""
    if not isinstance(filename, str) or not filename:
        raise NoteError("Invalid filename.")
    # No backslashes, no drive letters (C:), no null bytes, no leading slash.
    if "\\" in filename or ":" in filename or "\0" in filename:
        raise NoteError("Invalid filename.")
    if filename.startswith("/"):
        raise NoteError("Invalid filename.")
    parts = filename.split("/")
    # Rejects '..', '.', and empty parts such as 'a//b' or a trailing '/'.
    if any(part in ("", ".", "..") for part in parts):
        raise NoteError("Invalid filename.")
    return parts


def read_note(filename: str, notes_dir: Path | None = None) -> dict:
    """Read one .md or .txt note from inside the notes folder."""
    root = (notes_dir if notes_dir is not None else default_notes_dir()).resolve()

    # Rule 1: clean relative path.
    parts = _check_filename(filename)

    # Rule 2: only .md and .txt.
    if Path(parts[-1]).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise NoteError("Only .md and .txt files are allowed.")

    # Rules 3 and 4: walk down one part at a time.
    # Reject symlinks (files or folders) and stop if something is missing.
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise NoteError("Invalid filename.")
        if not current.exists():
            raise NoteError("Note not found.")
    if not current.is_file():
        raise NoteError("Invalid filename.")

    # Rule 7: final safety check. The real path must still be inside the notes folder.
    if not current.resolve().is_relative_to(root):
        raise NoteError("Invalid filename.")

    # Rule 5: size limit.
    if current.stat().st_size > MAX_BYTES:
        raise NoteError("Note is too large (max 1 MB).")

    # Rule 6: must be valid UTF-8 text.
    try:
        content = current.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        raise NoteError("Note is not valid UTF-8 text.") from None

    return {"filename": filename, "content": content}
