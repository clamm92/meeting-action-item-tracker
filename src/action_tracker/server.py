# MCP wrapper: exposes read_meeting_note and save_action_items.
# This file is thin on purpose. All real logic lives in notes.py and tasks.py.
# It is the only file that knows about MCP and about the transport (stdio).

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import StrictBool

from action_tracker.notes import NoteError, read_note
from action_tracker.tasks import TasksError, save_items

server = MCPServer("action-tracker")


@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def read_meeting_note(filename: str) -> dict:
    """Read one meeting note (.md or .txt) from the notes folder.

    filename is a relative path inside the notes folder, such as
    "planning/kickoff.md". Returns the filename and the note text.
    """
    try:
        return read_note(filename)
    except NoteError as error:
        raise ToolError(str(error)) from None  # message is short and safe to show


@server.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False))
def save_action_items(items: list[dict[str, Any]], approved: StrictBool = False) -> dict:
    """Append action items to tasks.json. Nothing is saved unless approved is true.

    Only set approved to true after the user has said yes to saving these items.

    Each item is an object with:
    - task (required): text, 1 to 500 characters
    - owner (optional): text, up to 100 characters
    - due_date (optional): YYYY-MM-DD, a real date
    - source_file (required): the note it came from, such as "planning/kickoff.md"

    Send between 1 and 50 items. If any item is invalid, nothing is saved.
    """
    try:
        return save_items(items, approved=approved)
    except TasksError as error:
        raise ToolError(str(error)) from None  # message is short and safe to show


def main() -> None:
    server.run()  # stdio by default. Switching transports later only changes this line.


if __name__ == "__main__":
    main()
