"""Graph search — BFS traversal from anchor nodes with edge-type weighting."""

from __future__ import annotations

import re
from collections import deque

from engram.storage.kuzu_backend import KuzuBackend
from engram.types import ScoredNode

# Edge type → base weight (high-signal edges weighted more)
EDGE_WEIGHTS = {
    "decided": 1.0,
    "prefers": 0.95,
    "replaced": 0.9,
    "works_on": 0.85,
    "depends_on": 0.8,
    "believes": 0.8,
    "part_of": 0.7,
    "related_to": 0.5,
    "mentioned": 0.3,
    "asked_about": 0.2,
    "contradicts": 0.4,
    "supersedes": 0.6,
    "derived_from": 0.5,
}

HOP_DECAY = 0.7  # score multiplied by this per hop


def extract_query_entities(query: str) -> list[str]:
    """Lightweight entity extraction from query using simple heuristics."""
    # Remove common stop words and question patterns
    stop_patterns = [
        r"\b(what|who|where|when|how|which|does|did|is|are|was|were|do|the|a|an)\b",
        r"\b(my|our|their|your|his|her|its)\b",
        r"\b(about|with|for|from|into|using|between)\b",
        r"[?.,!;:]",
    ]
    cleaned = query
    for pattern in stop_patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    # Split into meaningful tokens (2+ chars)
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]

    # Also try n-grams (2-word phrases)
    entities = list(tokens)
    for i in range(len(tokens) - 1):
        entities.append(f"{tokens[i]} {tokens[i + 1]}")

    return entities


async def graph_search(
    query: str,
    user_id: str,
    tenant_id: str,
    graph: KuzuBackend,
    max_hops: int = 3,
) -> list[ScoredNode]:
    """BFS graph traversal from anchor entities with weighted scoring."""
    entities = extract_query_entities(query)

    if not entities:
        return []

    # Find anchor nodes
    anchors = []
    for entity_text in entities:
        try:
            df = await graph.execute_cypher(
                """
                MATCH (e:Entity)
                WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id
                  AND (e.name CONTAINS $entity OR e.entity_type CONTAINS $entity)
                RETURN e.id AS id, e.name AS name
                ORDER BY e.last_referenced_at DESC
                LIMIT 5
                """,
                {"user_id": user_id, "tenant_id": tenant_id, "entity": entity_text},
            )
            for _, row in df.iterrows():
                anchors.append((row["id"], row["name"]))
        except Exception:
            continue

    if not anchors:
        return []

    # BFS traversal
    visited: set[str] = set()
    candidates: list[ScoredNode] = []
    queue: deque[tuple[str, int, float]] = deque()

    for anchor_id, _ in anchors:
        queue.append((anchor_id, 0, 1.0))

    while queue:
        node_id, depth, weight = queue.popleft()

        if node_id in visited or depth > max_hops:
            continue
        visited.add(node_id)

        candidates.append(ScoredNode(
            node_id=node_id,
            score=weight * (HOP_DECAY ** depth),
            source="graph",
        ))

        if depth < max_hops:
            try:
                df = await graph.execute_cypher(
                    """
                    MATCH (a:Entity)-[r:Rel]->(b:Entity)
                    WHERE a.id = $node_id AND r.invalid_from IS NULL
                    RETURN r.rel_type AS rel_type, b.id AS neighbor_id
                    """,
                    {"node_id": node_id},
                )
                for _, row in df.iterrows():
                    edge_weight = EDGE_WEIGHTS.get(row["rel_type"], 0.3)
                    queue.append((row["neighbor_id"], depth + 1, weight * edge_weight))
            except Exception:
                continue

    return candidates
