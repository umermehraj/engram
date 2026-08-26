"""Text preprocessing — chunking, deduplication, normalization."""

from __future__ import annotations


def preprocess_messages(messages: list[dict[str, str]]) -> str:
    """Convert a list of chat messages into a single text block for extraction."""
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def preprocess_document(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    """Chunk a long document into overlapping segments."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap

    return chunks


def normalize_text(text: str) -> str:
    """Basic text normalization."""
    # Collapse whitespace
    import re

    text = re.sub(r"\s+", " ", text).strip()
    return text
