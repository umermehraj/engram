"""Optional cross-encoder reranker for post-fusion precision boost."""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import Any

from engram.config import EngramConfig
from engram.storage.kuzu_backend import KuzuBackend

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, config: EngramConfig) -> None:
        self.config = config
        self._model: Any = None

    async def _get_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(CrossEncoder, self.config.reranker_model),
            )
        return self._model

    async def rerank(
        self,
        query: str,
        candidates: list[tuple[str, float]],
        graph: KuzuBackend,
        top_k: int | None = None,
    ) -> list[tuple[str, float]]:
        """Re-score candidates using a cross-encoder model.

        Fetches entity summaries from the graph, scores (query, summary) pairs,
        then returns candidates sorted by reranker score. Candidates beyond
        reranker_top_k are appended in their original order.
        """
        if not candidates:
            return candidates

        pairs: list[tuple[str, str]] = []
        valid_ids: list[str] = []

        for node_id, _ in candidates[: self.config.reranker_top_k]:
            entity = await graph.get_entity(node_id)
            if entity and entity.summary:
                # Include relationship context for richer scoring
                rels = await graph.get_active_relationships(node_id)
                context = entity.summary
                if rels:
                    rel_texts = [r.summary for r in rels[:3] if r.summary]
                    if rel_texts:
                        context = f"{context}. {'; '.join(rel_texts)}"
                pairs.append((query, context))
                valid_ids.append(node_id)

        if not pairs:
            return candidates

        model = await self._get_model()
        scores = await asyncio.get_event_loop().run_in_executor(
            None,
            partial(model.predict, pairs),
        )

        reranked = sorted(
            zip(valid_ids, (float(s) for s in scores)),
            key=lambda x: x[1],
            reverse=True,
        )

        reranked_ids = set(valid_ids)
        remaining = [(nid, s) for nid, s in candidates if nid not in reranked_ids]
        result = list(reranked) + remaining

        if top_k:
            result = result[:top_k]

        logger.info("Reranked %d candidates (top_k=%s)", len(valid_ids), top_k)
        return result
