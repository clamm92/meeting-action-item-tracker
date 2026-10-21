# Design Review: MCP Server Design

## What we reviewed

The design doc for the two tools, `read_meeting_note` and `save_action_items`.

## Security choices

- Notes can live in subfolders, but every path is checked. No `..`, no absolute paths, no backslashes.
- Symlinks are rejected, so a link cannot point outside the notes folder.
- Notes over 1 MB are rejected.
- Errors are short and never show full file paths.

## Open risks

- The model sets the `approved` flag, so it is only a safety net. Jordan said the host's per-tool approval prompt is the real control.
- A note could contain hidden instructions meant for the model (prompt injection). The tools only read and append, which limits the damage.
- Two saves at the same time are not handled in version 1.

## Decisions

- Due dates must be in YYYY-MM-DD format.
- `source_file` is required on every saved item.
- If one item in a save is bad, nothing is written.

## Action items

- Jordan will check that the MCP Inspector command works with our setup by 2026-10-28.
- Priya will add tests for symlinked folders by 2026-10-29.
- Sam will write the save tool by 2026-10-30.
- Alex will update the design doc with these decisions by 2026-10-27.
