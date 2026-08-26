"""Context assembly — greedy token-budget packing of formatted memory blocks."""

from __future__ import annotations

from engram.storage.kuzu_backend import KuzuBackend
from engram.types import ContextBlock, Entity, MemoryContext, Fact
from engram.utils import count_tokens, format_timestamp


def format_entity_block(entity: Entity, relationships: list) -> str:
    """Format an entity and its active relationships as a text block."""
    lines = [f"{entity.name} ({entity.entity_type})"]

    if entity.summary and entity.summary != f"{entity.name} ({entity.entity_type})":
        lines.append(f"  {entity.summary}")

    for rel in relationships:
        ts = format_timestamp(rel.valid_from) if rel.valid_from else ""
        lines.append(f"  - {rel.summary} ({ts})")

    return "\n".join(lines)


async def assemble_context(
    ranked_nodes: list[tuple[str, float]],
    graph: KuzuBackend,
    token_budget: int = 4000,
) -> MemoryContext:
    """Pack ranked entities into a token-budget-constrained context block."""
    blocks: list[ContextBlock] = []
    facts: list[Fact] = []
    tokens_used = 0
    text_parts: list[str] = []

    for node_id, score in ranked_nodes:
        entity = await graph.get_entity(node_id)
        if entity is None:
            continue

        relationships = await graph.get_active_relationships(node_id)
        block_text = format_entity_block(entity, relationships)
        block_tokens = count_tokens(block_text)

        if tokens_used + block_tokens > token_budget:
            break

        blocks.append(ContextBlock(
            content=block_text,
            node_id=node_id,
            score=score,
            timestamp=entity.created_at,
        ))
        text_parts.append(block_text)
        tokens_used += block_tokens

        # Convert relationships to facts for structured output
        for rel in relationships:
            facts.append(Fact(
                subject=entity.name,
                subject_type=entity.entity_type,
                predicate=rel.rel_type.value if hasattr(rel.rel_type, "value") else str(rel.rel_type),
                object="",  # Would need the target entity name
                confidence=rel.confidence,
                valid_from=rel.valid_from,
                source_session_id=rel.source_session_id,
            ))

        # Update reference time
        await graph.update_entity_reference(node_id)

    return MemoryContext(
        text="\n\n".join(text_parts),
        blocks=blocks,
        facts=facts,
        total_tokens=tokens_used,
        retrieval_metadata={
            "candidates_considered": len(ranked_nodes),
            "blocks_returned": len(blocks),
        },
    )
