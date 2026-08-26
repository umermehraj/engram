"""Temporal search — session facts, recency decay, recently referenced."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from engram.config import EngramConfig
from engram.storage.kuzu_backend import KuzuBackend
from engram.types import ScoredNode


async def temporal_search(
    query: str,
    user_id: str,
    tenant_id: str,
    graph: KuzuBackend,
    config: EngramConfig,
    session_id: str | None = None,
) -> list[ScoredNode]:
    """Temporal retrieval: session facts + recency decay + recently referenced."""
    candidates: list[ScoredNode] = []
    seen: set[str] = set()
    now = datetime.utcnow()

    # 1. Current session facts (highest score)
    if session_id:
        try:
            df = await graph.execute_cypher(
                """
                MATCH (e:Entity)-[r:Rel]->()
                WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id
                  AND r.source_session_id = $session_id
                  AND r.invalid_from IS NULL
                RETURN DISTINCT e.id AS entity_id
                """,
                {
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                },
            )
            for _, row in df.iterrows():
                eid = row["entity_id"]
                if eid not in seen:
                    candidates.append(ScoredNode(node_id=eid, score=1.0, source="temporal"))
                    seen.add(eid)
        except Exception:
            pass

    # 2. Recent facts (last N days, with exponential decay)
    cutoff = now - timedelta(days=config.recency_window_days)
    try:
        df = await graph.execute_cypher(
            """
            MATCH (e:Entity)-[r:Rel]->()
            WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id
              AND r.valid_from > $cutoff
              AND r.invalid_from IS NULL
            RETURN DISTINCT e.id AS entity_id, r.valid_from AS valid_from
            ORDER BY r.valid_from DESC
            LIMIT 100
            """,
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "cutoff": cutoff,
            },
        )
        for _, row in df.iterrows():
            eid = row["entity_id"]
            if eid not in seen:
                valid_from = row["valid_from"]
                if isinstance(valid_from, datetime):
                    age_hours = (now - valid_from).total_seconds() / 3600
                else:
                    age_hours = 0
                decay = math.exp(-config.recency_decay_rate * age_hours)
                candidates.append(ScoredNode(node_id=eid, score=decay, source="temporal"))
                seen.add(eid)
    except Exception:
        pass

    # 3. Recently referenced entities (even if the fact is old)
    ref_cutoff = now - timedelta(days=config.reference_window_days)
    try:
        df = await graph.execute_cypher(
            """
            MATCH (e:Entity)
            WHERE e.user_id = $user_id AND e.tenant_id = $tenant_id
              AND e.last_referenced_at > $cutoff
            RETURN e.id AS entity_id
            ORDER BY e.last_referenced_at DESC
            LIMIT 50
            """,
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "cutoff": ref_cutoff,
            },
        )
        for _, row in df.iterrows():
            eid = row["entity_id"]
            if eid not in seen:
                candidates.append(ScoredNode(node_id=eid, score=0.6, source="temporal"))
                seen.add(eid)
    except Exception:
        pass

    return candidates
