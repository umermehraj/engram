"""MCP (Model Context Protocol) server for Engram.

Exposes memory tools for Claude Desktop, Cursor, Windsurf, etc.

Usage:
    engram serve --mcp --port 8765
    # or
    python -m engram.integrations.mcp
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from engram.client import MemoryClient
from engram.config import EngramConfig


async def create_mcp_server(config: EngramConfig | None = None):
    """Create an MCP server exposing Engram memory tools."""
    try:
        from mcp.server import Server
        from mcp.types import Tool, TextContent
    except ImportError:
        raise ImportError(
            "MCP integration requires the mcp package. "
            "Install with: pip install engram[mcp]"
        )

    config = config or EngramConfig.from_env(local=True)
    client = MemoryClient(config=config)
    await client._ensure_initialized()

    server = Server("engram-memory")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="memory_search",
                description=(
                    "Search the user's memory for relevant context. Returns facts, "
                    "decisions, preferences, and conversation history matching the query."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to search for"},
                        "user_id": {"type": "string", "description": "User ID"},
                        "top_k": {"type": "integer", "description": "Max results", "default": 10},
                    },
                    "required": ["query", "user_id"],
                },
            ),
            Tool(
                name="memory_add",
                description=(
                    "Store new information in memory. Extracts entities and relationships "
                    "from the provided text and adds them to the knowledge graph."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Text content to memorize"},
                        "user_id": {"type": "string", "description": "User ID"},
                        "session_id": {"type": "string", "description": "Session ID (optional)"},
                    },
                    "required": ["content", "user_id"],
                },
            ),
            Tool(
                name="memory_history",
                description=(
                    "Get the temporal history of how facts about an entity changed over time."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"},
                        "entity_name": {"type": "string", "description": "Entity to get history for"},
                    },
                    "required": ["user_id"],
                },
            ),
            Tool(
                name="memory_delete",
                description="Delete a specific memory by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "string", "description": "Memory ID to delete"},
                    },
                    "required": ["memory_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list:
        if name == "memory_search":
            ctx = await client.search(
                query=arguments["query"],
                user_id=arguments["user_id"],
                top_k=arguments.get("top_k", 10),
            )
            return [TextContent(type="text", text=ctx.text or "No memories found.")]

        elif name == "memory_add":
            result = await client.add(
                text=arguments["content"],
                user_id=arguments["user_id"],
                session_id=arguments.get("session_id"),
            )
            return [TextContent(
                type="text",
                text=(
                    f"Stored: {result.entities_created} entities, "
                    f"{result.relationships_created} relationships"
                ),
            )]

        elif name == "memory_history":
            versions = await client.history(
                user_id=arguments["user_id"],
                entity_name=arguments.get("entity_name"),
            )
            if not versions:
                return [TextContent(type="text", text="No history found.")]
            lines = []
            for v in versions:
                status = "active" if v.was_active else "superseded"
                lines.append(
                    f"- {v.entity_name} {v.rel_type}: {v.relationship_summary} ({status})"
                )
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "memory_delete":
            await client.delete(memory_id=arguments["memory_id"])
            return [TextContent(type="text", text=f"Deleted memory {arguments['memory_id']}")]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    return server, client


async def run_stdio():
    """Run the MCP server over stdio (for Claude Desktop / Cursor)."""
    from mcp.server.stdio import stdio_server

    server, client = await create_mcp_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

    await client.close()


if __name__ == "__main__":
    asyncio.run(run_stdio())
