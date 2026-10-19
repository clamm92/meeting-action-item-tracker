# Project Kickoff: Meeting Action Item Tracker

Date: 2026-10-19
Attendees: Alex, Priya, Sam

## Goal

Build a small MCP server that lets an AI agent read meeting notes and save action items. The first version is local only (stdio).

## What is in scope

- A tool to read a meeting note.
- A tool to save action items, only after the user approves.

## What is not in scope

- Duplicate checking.
- A user interface.
- Hosting on a server.

## Discussion

- Alex wants the real logic in plain Python functions, with the MCP layer kept thin.
- Priya asked how we stop the agent from reading files outside the notes folder. We agreed on strict path checks.
- Sam pointed out that the agent decides when to call a tool, so the user must approve each save.

## Action items

- Alex will set up the Python project and the virtual environment by 2026-10-21.
- Priya will write the path safety tests by 2026-10-23.
- Sam will write three sample notes by 2026-10-22.
- Alex will write the read tool by 2026-10-24.
