# Tool 2 logic: save_items()
# Plain Python only. No MCP code in this file.
# Rules come from mcp-server-design.md, sections 6 and 7.

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from action_tracker.notes import ALLOWED_EXTENSIONS, PROJECT_DIR, NoteError, _check_filename

MIN_ITEMS = 1
MAX_ITEMS = 50
MAX_TASK_CHARS = 500
MAX_OWNER_CHARS = 100

# Strict YYYY-MM-DD. [0-9] (not \d) so other scripts' digits are not accepted.
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class TasksError(Exception):
    """Raised when items cannot be saved. The message is safe to show to users."""


def default_tasks_file() -> Path:
    """TASKS_FILE from the environment, or tasks.json in the project folder."""
    value = os.environ.get("TASKS_FILE")
    return Path(value) if value else PROJECT_DIR / "tasks.json"


def _validate_item(item: object) -> dict:
    """Check one item. Return a clean copy with only the known fields.

    Raises ValueError with a short reason if the item is bad.
    """
    if not isinstance(item, dict):
        raise ValueError("must be an object")

    task = item.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task is required")
    if len(task) > MAX_TASK_CHARS:
        raise ValueError(f"task is longer than {MAX_TASK_CHARS} characters")

    owner = item.get("owner")
    if owner is not None:
        if not isinstance(owner, str):
            raise ValueError("owner must be text")
        if len(owner) > MAX_OWNER_CHARS:
            raise ValueError(f"owner is longer than {MAX_OWNER_CHARS} characters")

    due_date = item.get("due_date")
    if due_date is not None:
        if not isinstance(due_date, str) or not DATE_PATTERN.fullmatch(due_date):
            raise ValueError("due_date must be YYYY-MM-DD")
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("due_date is not a real date") from None

    source_file = item.get("source_file")
    if not isinstance(source_file, str) or not source_file:
        raise ValueError("source_file is required")
    try:
        parts = _check_filename(source_file)  # same path rules as read_note()
    except NoteError:
        raise ValueError("source_file is not a valid path") from None
    if Path(parts[-1]).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("source_file must end in .md or .txt")

    return {
        "task": task,
        "owner": owner,
        "due_date": due_date,
        "source_file": source_file,
    }


def _load_existing(tasks_file: Path) -> list:
    """Return the saved items. A missing file means an empty list."""
    if not tasks_file.exists():
        return []
    try:
        data = json.loads(tasks_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):  # unreadable, bad JSON, or bad UTF-8
        raise TasksError("Tasks file is unreadable. Nothing was saved.") from None
    if not isinstance(data, list):
        raise TasksError("Tasks file is unreadable. Nothing was saved.")
    return data


def _write_atomically(tasks_file: Path, data: list) -> None:
    """Write to a temp file in the same folder, then rename it over the real file."""
    fd, temp_name = tempfile.mkstemp(dir=tasks_file.parent, prefix=".tasks-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_name, tasks_file)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def save_items(items: list, approved: bool = False, tasks_file: Path | None = None) -> dict:
    """Append action items to tasks.json, but only if approved is exactly True."""
    path = tasks_file if tasks_file is not None else default_tasks_file()

    # Rule 1: approval gate. Only the real boolean True passes ("true" and 1 do not).
    if approved is not True:
        raise TasksError("Not approved. Nothing was saved.")

    # Rule 2: 1 to 50 items.
    if not isinstance(items, list) or not (MIN_ITEMS <= len(items) <= MAX_ITEMS):
        raise TasksError("Provide between 1 and 50 items.")

    # Rule 3: check every item first. One bad item means nothing is written.
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_items = []
    for number, item in enumerate(items, start=1):
        try:
            clean = _validate_item(item)
        except ValueError as error:
            raise TasksError(f"Item {number} is invalid: {error}.") from None
        clean["created_at"] = created_at  # added by our code, not by the agent
        new_items.append(clean)

    # Rule 4: add to the end of the existing list.
    saved = _load_existing(path)
    saved.extend(new_items)
    _write_atomically(path, saved)

    return {"saved": len(new_items), "total_in_file": len(saved)}
