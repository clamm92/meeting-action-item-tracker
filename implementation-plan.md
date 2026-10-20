# Implementation Plan: MCP Server (v1)

Full rules are in [`mcp-server-design.md`](mcp-server-design.md). The big picture is in [`architecture.md`](architecture.md).

## Overview

Build a small Python MCP server with two tools (`read_meeting_note`, `save_action_items`). The logic lives in plain functions. The MCP layer is thin. We test with pytest first, then MCP Inspector.

Do the sub-tasks one at a time, in order. Wait for the user's OK after each one.

---

## 1. Project setup

- **Intent:** Get an empty project that installs and runs tests.
- **Expected outcomes:** `venv` works, packages install, `pytest` runs (0 tests is fine), secrets are ignored by git.
- **Todo:**
  1. Check the newest stable Python and the latest stable MCP SDK and pytest.
  2. Create the folders from the design doc (section 3).
  3. Add `pyproject.toml` with pinned versions, and a committed lock file.
  4. Add `.gitignore` (`.venv/`, `tasks.json`, `__pycache__/`).
- **Relevant context:** Design doc sections 3 and 11.
- **Status:** [x] done

### Notes for sub-task 2

- **Python:** 3.13.16 (at `.venv/`). Activate with `source .venv/bin/activate`.
- **MCP SDK:** `mcp==2.3.0` (latest stable, uploaded 2026-10-02 — actively maintained).
- **pytest:** `8.4.2` (latest stable).
- **Lock file:** `requirements.lock` — plain `pip freeze` output, committed to git. To regenerate: activate the venv, run `pip freeze > requirements.lock`.
- **Install from scratch:**
  ```
  python3.13 -m venv .venv
  source .venv/bin/activate
  pip install -e ".[dev]"
  ```
- **Run tests:** `pytest` (or `.venv/bin/pytest`). 0 collected is fine until sub-task 2 adds real tests.
- **Folder layout created:** `src/action_tracker/` (with empty `notes.py`, `tasks.py`, `server.py`), `notes/`, `tests/`.

## 2. Read tool logic and sample notes

- **Intent:** Safe note reading, with no MCP code.
- **Expected outcomes:** `read_note()` follows every rule in design section 5. Tests pass.
- **Todo:**
  1. Write the 3 sample notes (design section 12).
  2. Write `notes.py` with `read_note()`.
  3. Write `tests/test_notes.py` for the read cases in design section 9.
- **Relevant context:** `src/action_tracker/notes.py`, `notes/`, design sections 5, 9, 12.
- **Status:** [x] done

## 3. Save tool logic

- **Intent:** Safe, approved saving, with no MCP code.
- **Expected outcomes:** `save_items()` follows every rule in design sections 6 and 7. Tests pass.
- **Todo:**
  1. Write `tasks.py` with `save_items()`.
  2. Write `tests/test_tasks.py` for the save cases in design section 9.
- **Relevant context:** `src/action_tracker/tasks.py`, design sections 6, 7, 9.
- **Status:** [x] done

### Notes for sub-task 4

- `tasks.py` exposes `save_items(items, approved=False, tasks_file=None)` and `TasksError`. It returns `{"saved": n, "total_in_file": m}`.
- `notes.py` exposes `read_note(filename, notes_dir=None)` and `NoteError`.
- Both errors carry messages that are safe to show to users. The MCP wrapper should pass `str(error)` back and nothing else.
- Settings: `default_notes_dir()` reads `NOTES_DIR`, and `default_tasks_file()` reads `TASKS_FILE`.
- `approved` must be the real boolean `True`. The wrapper should pass the value through unchanged and never convert it.
- `tasks.py` imports `_check_filename` from `notes.py` so `source_file` follows the same path rules.
- Run tests with `.venv/bin/pytest -q` (56 pass).

## 4. MCP wrapper

- **Intent:** Expose both functions as MCP tools over stdio.
- **Expected outcomes:** The server starts. Both tools are listed. Nothing is printed to stdout except MCP messages.
- **Todo:**
  1. Write `server.py` with the two tools. It only calls `notes.py` and `tasks.py`.
  2. Read settings from environment variables (design section 4).
  3. Send logs to stderr. Never log note text.
- **Relevant context:** `src/action_tracker/server.py`, design sections 4, 8.
- **Status:** [x] done

### Notes for sub-task 5

- Start the server by hand: `.venv/bin/python -m action_tracker.server` (stdio). It waits silently for MCP messages, which is normal.
- SDK v2 uses `from mcp.server.mcpserver import MCPServer`. `FastMCP` no longer exists.
- `approved` is declared as `StrictBool`. A plain `bool` made the SDK turn `"true"`, `1`, and `"yes"` into `True`. `tests/test_server.py` guards this.
- A real stdio round trip (list tools, read, refused save, approved save) was run with the SDK client and worked. Sub-task 5 can turn it into the optional client script.
- Inspector command is not yet confirmed. Check the current MCP docs first (plan step 5.1).
- Run tests with `.venv/bin/pytest -q` (70 pass).

## 5. Test with MCP Inspector and a client script

- **Intent:** Prove the server works the way an agent will use it.
- **Expected outcomes:** Both tools work by hand in Inspector. An optional script lists and calls them from code.
- **Todo:**
  1. Confirm the Inspector command in the current MCP docs.
  2. Call both tools in Inspector: good inputs and bad inputs.
  3. (Optional) Write a tiny client script in `tests/` or `scripts/`.
- **Relevant context:** Design section 9, layers 2 and 3.
- **Status:** [ ] pending

## 6. README

- **Intent:** Let someone else set up, run, and test the server.
- **Expected outcomes:** The README steps work from a clean checkout.
- **Todo:**
  1. Write setup, run, pytest, and Inspector steps (only commands we have actually run).
  2. Add the host reminder: turn on per-tool approval so you confirm every save.
  3. Link the design doc and the architecture file.
- **Relevant context:** `README.md`.
- **Status:** [ ] pending
