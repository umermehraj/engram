"""Global/thematic search — find high-connectivity entities across the graph."""

from __future__ import annotations

from engram.storage.kuzu_backend import KuzuBackend
from engram.types import ScoredNode


async def global_search(
    user_id: str,
    tenant_id: str,
    graph: KuzuBackend,
    top_k: int = 50,
    entity_type_filter: str | None = None,
) -> list[ScoredNode]:
    """Find most-connected and recently-active entities.

    Scores entities by degree centrality (number of active relationships),
    with recency as a tiebreaker. Useful for "overview" and "themes" queries.
    """
    type_filter = ""
    params: dict = {"user_id": user_id, "tenant_id": tenant_id, "top_k": top_k}

    if entity_type_filter:
        type_filter = "AND e.entity_type = $entity_type"
        params["entity_type"] = entity_type_filter

    df = await graph.execute_cypher(
        f"""
        MATCH (e:Entity)
        WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id {type_filter}
        OPTIONAL MATCH (e)-[r:Rel]-()
        WHERE r.invalid_from IS NULL
        WITH e, COUNT(r) AS degree
        RETURN e.id AS id, degree
        ORDER BY degree DESC, e.last_referenced_at DESC
        LIMIT $top_k
        """,
        params,
    )

    if df.empty:
        return []

    max_degree = df["degree"].max() or 1

    return [
        ScoredNode(
            node_id=row["id"],
            score=row["degree"] / max_degree,
            source="global",
        )
        for _, row in df.iterrows()
    ]
