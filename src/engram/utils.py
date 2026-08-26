"""Shared utilities for Engram."""

from __future__ import annotations

import uuid
from datetime import datetime


def generate_id(prefix: str = "ent") -> str:
    """Generate a short prefixed unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def count_tokens(text: str) -> int:
    """Approximate token count. Uses tiktoken if available, else len/4 heuristic."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Rough approximation: 1 token ≈ 4 chars
        return len(text) // 4


def format_timestamp(dt: datetime) -> str:
    """Format a datetime for display in memory context blocks."""
    return dt.strftime("%b %d, %Y")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Compute normalized Levenshtein similarity ratio (0.0 - 1.0)."""
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    # Standard DP Levenshtein distance
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
            )

    distance = matrix[len1][len2]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)
