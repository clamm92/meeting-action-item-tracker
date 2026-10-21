# Ideas: Future Extensions 

## Ideas after version 1

- A `list_action_items` tool, so the agent can read saved tasks.
- Mark a task as done, or edit and delete tasks.
- Duplicate checking.
- A `list_meeting_notes` tool, so the agent can find notes by itself.
- HTTP transport, so a hosted platform can use the server.
- A real database instead of `tasks.json`.
- Locking, for more than one user or agent at a time.
- Notes from other sources, such as calendar events and transcripts.
- Reminders for tasks that are due soon.

## Discussion

- Priya thinks `list_action_items` should come first, because it makes the agent more useful right away.
- Sam wants HTTP early, since the target platform cannot start a local process.
- Alex warned that HTTP needs a network design review before we build it. The server must only bind to 127.0.0.1 unless we decide otherwise.

## Action items

- Priya will draft the `list_action_items` tool contract by 2026-11-06.
- Sam will find out whether the hosted platform accepts MCP servers by 2026-11-09.
- Alex will write a short HTTP security checklist by 2026-11-13.
