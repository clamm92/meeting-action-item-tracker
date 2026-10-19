# Meeting Action Item Tracker: MCP Server Design (v1)

Status: DRAFT. Items marked **(proposed)** are waiting for your OK.
All open questions are now answered (see section 12).

---

## 1. What we are building

A small MCP server with two tools:

1. `read_meeting_note` reads one meeting note from a notes folder.
2. `save_action_items` saves action items to a file, but only after approval.

An AI agent (later) will use these tools. The agent reads a note, finds the action items, and asks the user to approve them. Then it saves them.

## 2. Goals and non-goals

**Goals**
- Two working tools that are safe and easy to test.
- Test everything without an agent.
- Start with stdio. Make it easy to switch to HTTP later.

**Non-goals for v1**
- No agent, no UI.
- No duplicate checking. The user can ask the agent to clean up.
- No tool to read or edit saved tasks.
- No login or user accounts.
- No HTTP.

## 3. How it is organized

Two layers. The real work lives in plain Python functions. The MCP layer is a thin wrapper.

```
MeetingActionItemTracker/
  src/action_tracker/
    notes.py      <- read_note() logic. No MCP code here.
    tasks.py      <- save_items() logic. No MCP code here.
    server.py     <- MCP wrapper. Calls notes.py and tasks.py.
  notes/          <- sample notes about this project (not confidential)
  tests/          <- pytest tests
  tasks.json      <- created on first save (not in git)
  pyproject.toml
  README.md
```

**One rule:** `server.py` imports the other files. They never import MCP. That is why we can test them with plain pytest.

## 4. Settings

| Setting | Default | Meaning |
|---|---|---|
| `NOTES_DIR` | `notes/` in the project folder | Where notes are read from |
| `TASKS_FILE` | `tasks.json` in the project folder | Where tasks are saved |

- Paths are based on the project folder, not the folder the host starts us from. **(proposed)**
- Settings come from environment variables. Nothing is hardcoded.

## 5. Tool 1: `read_meeting_note(filename)`

**What it does:** Returns the text of one note.

**Input:** `filename`, a path inside the notes folder. Subfolders are allowed. Examples: `kickoff.md` or `2025/january/standup.md`.

**Rules (check in this order):**
1. Must be a relative path that uses `/` between folders. Reject these:
   - absolute paths (`/etc/passwd`, `C:\x`)
   - any `..` part
   - any `\`
   - empty parts (`a//b`)
   - empty names
2. Must end in `.md` or `.txt`.
3. Must exist inside the notes folder.
4. Must be a normal file. **Symlinks are rejected, and so is any symlinked folder in the path.**
5. Must be 1 MB or smaller.
6. Must be valid UTF-8 text.
7. As a last safety check, the final real path must still be inside the notes folder.

**Success output** (the `filename` is returned as given, in the same relative form):
```json
{ "filename": "2025/january/standup.md", "content": "..." }
```

**Errors** (short and generic, never show full paths):
| Case | Message |
|---|---|
| Bad name or path escape | `Invalid filename.` |
| Wrong file type | `Only .md and .txt files are allowed.` |
| Missing file | `Note not found.` |
| Symlink or not a file | `Invalid filename.` |
| Too big | `Note is too large (max 1 MB).` |
| Not UTF-8 | `Note is not valid UTF-8 text.` |

## 6. Tool 2: `save_action_items(items, approved)`

**What it does:** Adds action items to `tasks.json`.

**Input:**
- `approved`: must be exactly `true`. Anything else, including missing, means refuse.
- `items`: a list of objects:

| Field | Required? | Rules |
|---|---|---|
| `task` | Yes | Text, 1 to 500 characters |
| `owner` | No | Text, up to 100 characters |
| `due_date` | No | Strict `YYYY-MM-DD` only. Must be a real date (`2025-02-30` is rejected). No free text like "next Friday". |
| `source_file` | Yes | A relative path, same name rules 1 and 2 as Tool 1. It is not checked for existence. |

The **timestamp is added by our code**, not by the agent. It uses UTC in ISO 8601 format, like `2025-01-06T14:30:00Z`. **(proposed)**

**Rules:**
1. If `approved` is not `true`, write nothing and return an error.
2. The list must have 1 to 50 items. **(proposed)**
3. Check every item first. If any item is bad, **write nothing** (all or nothing).
4. Add the new items to the end of the existing list.
5. Duplicates are not checked.

**Success output:**
```json
{ "saved": 3, "total_in_file": 12 }
```

**Errors:**
| Case | Message |
|---|---|
| Not approved | `Not approved. Nothing was saved.` |
| Bad item | `Item 2 is invalid: <short reason>.` |
| Too many or no items | `Provide between 1 and 50 items.` |
| Broken `tasks.json` | `Tasks file is unreadable. Nothing was saved.` |

## 7. The `tasks.json` file

A JSON list. Each saved item looks like this:

```json
{
  "task": "Send the Q1 report",
  "owner": "Sam",
  "due_date": "2025-01-10",
  "source_file": "planning/kickoff.md",
  "created_at": "2025-01-06T14:30:00Z"
}
```

- **File missing:** treat as an empty list. Create it on the first save.
- **File broken** (not valid JSON, or not a list): refuse to save. Never overwrite it.
- **Safe write:** write to a temp file in the same folder, then rename it over `tasks.json`. A crash can't leave a half-written file.
- **Two saves at the same time:** not handled in v1. We assume one user at a time.
- Optional fields that are missing are saved as `null`. **(proposed)**

## 8. Security

| Risk | What we do |
|---|---|
| Path escape (`../secret.txt`, `/etc/passwd`) | Plain-name rule, plus a final real-path check |
| Symlink pointing outside the notes folder | Reject symlinks |
| The model sets `approved` by itself | `approved` is only a safety net. **When we connect a host, turn on its per-tool approval prompt** so you confirm every save. |
| Notes contain hidden instructions (prompt injection) | Treat note text as untrusted data. The tools only read and append, and the approval prompt is the human check. |
| Leaking info in errors | Generic messages only. No stack traces, no absolute paths. Details go to the server log only. |
| Leaking info in logs | Log tool name and result, not note text. Logs go to **stderr**. |
| Secret files committed | `tasks.json` goes in `.gitignore`. Sample notes are non-confidential. |
| Network exposure | stdio only in v1, so there is no network port. If we add HTTP later, bind to `127.0.0.1` only, with TLS 1.2 or higher. |
| Old or abandoned packages | Use the official MCP Python SDK. Pin the latest stable version when we build. Check that it is actively maintained and that the lock file is committed. |

**Important for stdio:** the server must never `print()` to stdout. stdout carries the MCP messages, and extra text breaks the connection. Logging goes to stderr.

## 9. Testing plan

**Layer 1: pytest (no MCP, no agent).** Call the plain functions.

| Test | Expected |
|---|---|
| Read a normal note | Returns the content |
| Missing file | `Note not found.` |
| `../secret.txt` | `Invalid filename.` |
| Absolute path | `Invalid filename.` |
| Symlink to outside file | `Invalid filename.` |
| Wrong extension (`.py`) | Type error |
| File over 1 MB | Too-large error |
| Save with `approved=false` | Refused, file unchanged |
| Save with `approved` missing or a string like `"true"` | Refused |
| Save with a bad item | Nothing written |
| Save OK to a new file | File created with the right JSON |
| Save OK to an existing file | New items added at the end |
| Broken `tasks.json` | Refused, file unchanged |

**Layer 2: MCP Inspector.** Run `npx @modelcontextprotocol/inspector`, point it at the server, and call both tools by hand. We will confirm the exact command in the current MCP docs when we build.

**Layer 3 (optional): tiny client script.** Use the MCP client SDK to connect, list tools, and call them.

The server is ready for an agent when all three layers pass.

## 10. Switching to HTTP later

- Keep tool logic in `notes.py` and `tasks.py`.
- Only `server.py` knows the transport.
- Moving to HTTP should mean changing how `server.py` starts, not the tools.

## 11. Python setup (decided)

- **Python:** the newest stable version, checked when we build.
- **Virtual environment:** `venv` (comes with Python).
- **Installing packages:** `pip`. Package versions go in `pyproject.toml`. The exact installed versions go in a lock file that we commit. We will pick the lock file method when we build.

## 12. Decisions still open

1. **No subfolders in notes.** Is that OK for v1?
2. **Due date format.** Strict `YYYY-MM-DD` only, or allow free text like "next Friday"?
3. **`source_file` required.** Should the agent always have to say which note an item came from?
4. **Sample notes.** How many, and what kind? I suggest 3 short, made-up notes.
