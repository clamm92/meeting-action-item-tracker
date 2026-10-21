# scripts/demo_client.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=["-m", "action_tracker.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. List available tools
            tools = await session.list_tools()
            print("Discovered tools:", [t.name for t in tools.tools])

            # 2. Read a real meeting note
            note = await session.call_tool("read_meeting_note", {"filename": "planning/kickoff.md"})
            print("\nRead Note Result:\n", note.content[0].text)

            # 3. Save action items with approval
            items_to_save = [
                {
                    "task": "Alex will set up the Python project and venv",
                    "owner": "Alex",
                    "due_date": "2026-10-21",
                    "source_file": "planning/kickoff.md",
                }
            ]
            save_result = await session.call_tool(
                "save_action_items", {"items": items_to_save, "approved": True}
            )
            print("\nSave Result:\n", save_result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())