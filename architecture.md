# Architecture (Short Version)

## The big picture

When the whole system is done, it works like this:

```
 You
  |  "Find the action items in planning/kickoff.md"
  v
 Agent / Host (the app, for example Bob)
  |  sends your request + the list of available tools to the model
  v
 Model (the AI)
  |  decides: "I need read_meeting_note"
  v
 Agent / Host
  |  calls the tool on the MCP server
  v
 MCP Server  <---- WE ARE BUILDING THIS PART
  |  runs the tool, returns the result
  v
 Agent / Host
  |  gives the result back to the model
  v
 Model
  |  reads the note, writes action items, asks you to approve
  v
 You  ("yes, save them")
  |
  v
 Model -> Agent -> MCP Server (save_action_items, approved=true) -> tasks.json
```

## Who does what

| Part | Job |
|---|---|
| **You** | Ask questions. Approve saves. |
| **Agent / Host** | Runs the conversation. Talks to the model. Calls the tools. Can show an approval prompt. |
| **Model** | Thinks. Picks which tool to call. Writes the action items. |
| **MCP server** | Offers tools. Runs them. Returns results. It does not think. |

The model never touches your files directly. It can only ask the server to do one of the two things the tools allow.

## What we build right now: only the MCP server

There is no agent yet. So for now:

```
 pytest / MCP Inspector / small client script
  |
  v
 MCP Server  ->  notes/ (read)   and   tasks.json (write)
```

These three test tools play the role of the agent. They call the tools the same way an agent would.

## Inside the MCP server

```
 server.py   (thin MCP wrapper: names the tools, passes inputs, returns outputs)
    |
    +--> notes.py   read_note()   : checks the path, reads the file
    |
    +--> tasks.py   save_items()  : checks approval, checks items, writes the file
```

- `server.py` only translates between MCP and plain Python.
- `notes.py` and `tasks.py` hold all the real logic and know nothing about MCP.
- That is why we can test them with plain pytest first.

## Why the agent plugs in later without changes

The agent only needs to know how to talk to the server. It does not matter which agent or host it is.

- **Now:** stdio. The host starts the server as a local program.
- **Later:** HTTP, if we need a hosted platform. Only the start-up code in `server.py` changes. The tools stay the same.

See [`mcp-server-design.md`](mcp-server-design.md) for the full rules of each tool.
