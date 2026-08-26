"""OpenAI Agents SDK integration — memory as tools for agents."""

from __future__ import annotations

import json
from typing import Any

from engram.client import MemoryClient


def memory_tools(client: MemoryClient, user_id: str, tenant_id: str = "default") -> list:
    """
    Create OpenAI Agents SDK Tool objects for memory access.

    Returns tools: search_memory, add_memory, get_history

    Usage:
        from engram.integrations.openai_agents import memory_tools
        tools = memory_tools(client=memory, user_id="user_123")
        agent = Agent(name="assistant", tools=tools)
    """
    try:
        from agents import Tool, function_tool
    except ImportError:
        raise ImportError(
            "OpenAI Agents SDK integration requires openai-agents. "
            "Install with: pip install engram[openai-agents]"
        )

    @function_tool
    async def search_memory(query: str, top_k: int = 10) -> str:
        """Search the user's memory for relevant context. Use this to recall facts, preferences, decisions, and past conversations."""
        ctx = await client.search(
            query, user_id=user_id, tenant_id=tenant_id, top_k=top_k
        )
        return ctx.text or "No relevant memories found."

    @function_tool
    async def add_memory(content: str, session_id: str = "") -> str:
        """Store new information in the user's memory. Use this to remember important facts, decisions, or preferences."""
        result = await client.add(
            text=content,
            user_id=user_id,
            session_id=session_id or None,
            tenant_id=tenant_id,
        )
        return (
            f"Stored: {result.entities_created} entities, "
            f"{result.relationships_created} relationships"
        )

    @function_tool
    async def get_memory_history(entity_name: str = "") -> str:
        """Get the temporal history of an entity — how facts changed over time."""
        versions = await client.history(
            user_id=user_id,
            entity_name=entity_name or None,
            tenant_id=tenant_id,
        )
        if not versions:
            return "No history found."
        lines = []
        for v in versions:
            status = "active" if v.was_active else "superseded"
            lines.append(
                f"- {v.entity_name} {v.rel_type}: {v.relationship_summary} "
                f"(from {v.valid_from.isoformat()}, {status})"
            )
        return "\n".join(lines)

    return [search_memory, add_memory, get_memory_history]
