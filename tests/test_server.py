import json

import anyio
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from action_tracker.server import server


def call(tool_name, arguments):
    """Call a tool the way an MCP host would (through the SDK), without a process."""
    async def run():
        return await server.call_tool(tool_name, arguments)
    return anyio.run(run)


def result_json(result):
    """The tool's reply is JSON text in the first content block."""
    return json.loads(result.content[0].text)


def good_item(**changes):
    item = {"task": "Send the report", "owner": "Sam", "due_date": "2025-01-10", "source_file": "a.md"}
    item.update(changes)
    return item


@pytest.fixture
def folders(tmp_path, monkeypatch):
    """Point the server at throwaway folders, never the real notes or tasks.json."""
    notes = tmp_path / "notes"
    notes.mkdir()
    tasks_file = tmp_path / "tasks.json"
    monkeypatch.setenv("NOTES_DIR", str(notes))
    monkeypatch.setenv("TASKS_FILE", str(tasks_file))
    return notes, tasks_file


# ---------- the tools are listed ----------

def test_lists_exactly_the_two_tools():
    async def run():
        return await server.list_tools()
    tools = {tool.name: tool for tool in anyio.run(run)}
    assert set(tools) == {"read_meeting_note", "save_action_items"}


def test_approved_is_advertised_as_a_boolean():
    async def run():
        return await server.list_tools()
    save = next(tool for tool in anyio.run(run) if tool.name == "save_action_items")
    assert save.input_schema["properties"]["approved"]["type"] == "boolean"


# ---------- read_meeting_note ----------

def test_read_tool_returns_the_note(folders):
    notes, _ = folders
    (notes / "hello.md").write_text("hi")
    result = call("read_meeting_note", {"filename": "hello.md"})
    assert result_json(result) == {"filename": "hello.md", "content": "hi"}


def test_read_tool_turns_note_errors_into_tool_errors(folders):
    with pytest.raises(ToolError, match="Note not found"):
        call("read_meeting_note", {"filename": "nope.md"})


def test_read_tool_rejects_path_escape(folders):
    notes, _ = folders
    (notes.parent / "secret.txt").write_text("top secret")
    with pytest.raises(ToolError, match="Invalid filename"):
        call("read_meeting_note", {"filename": "../secret.txt"})


def test_read_error_does_not_leak_the_folder_path(folders):
    notes, _ = folders
    with pytest.raises(ToolError) as caught:
        call("read_meeting_note", {"filename": "nope.md"})
    assert str(notes) not in str(caught.value)


# ---------- save_action_items ----------

def test_save_tool_saves_when_approved(folders):
    _, tasks_file = folders
    result = call("save_action_items", {"items": [good_item()], "approved": True})
    assert result_json(result) == {"saved": 1, "total_in_file": 1}
    assert json.loads(tasks_file.read_text())[0]["task"] == "Send the report"


def test_save_tool_refuses_when_approved_is_false(folders):
    _, tasks_file = folders
    with pytest.raises(ToolError, match="Not approved"):
        call("save_action_items", {"items": [good_item()], "approved": False})
    assert not tasks_file.exists()


def test_save_tool_refuses_when_approved_is_omitted(folders):
    _, tasks_file = folders
    with pytest.raises(ToolError, match="Not approved"):
        call("save_action_items", {"items": [good_item()]})
    assert not tasks_file.exists()


@pytest.mark.parametrize("not_a_real_true", ["true", 1, "yes", None])
def test_save_tool_refuses_values_that_only_look_like_true(folders, not_a_real_true):
    # The SDK would turn these into True for a plain bool. StrictBool must stop them.
    _, tasks_file = folders
    with pytest.raises(ToolError):
        call("save_action_items", {"items": [good_item()], "approved": not_a_real_true})
    assert not tasks_file.exists()


def test_save_tool_turns_item_errors_into_tool_errors(folders):
    _, tasks_file = folders
    with pytest.raises(ToolError, match="Item 1 is invalid: due_date"):
        call("save_action_items", {"items": [good_item(due_date="next Friday")], "approved": True})
    assert not tasks_file.exists()
