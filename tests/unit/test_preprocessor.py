"""Tests for text preprocessor."""

from engram.ingestion.preprocessor import (
    preprocess_messages,
    preprocess_document,
    normalize_text,
)


def test_preprocess_messages():
    msgs = [
        {"role": "user", "content": "I'm switching to FastAPI"},
        {"role": "assistant", "content": "Got it!"},
    ]
    text = preprocess_messages(msgs)
    assert "user: I'm switching to FastAPI" in text
    assert "assistant: Got it!" in text


def test_preprocess_messages_empty():
    assert preprocess_messages([]) == ""
    assert preprocess_messages([{"role": "user", "content": ""}]) == ""


def test_preprocess_document_short():
    text = "Short doc."
    chunks = preprocess_document(text)
    assert len(chunks) == 1
    assert chunks[0] == "Short doc."


def test_preprocess_document_chunking():
    text = "A" * 5000
    chunks = preprocess_document(text, chunk_size=2000, overlap=200)
    assert len(chunks) > 1
    # Each chunk should be <= chunk_size
    for chunk in chunks:
        assert len(chunk) <= 2000


def test_preprocess_document_empty():
    assert preprocess_document("") == []
    assert preprocess_document("   ") == []


def test_normalize_text():
    assert normalize_text("  hello   world  ") == "hello world"
    assert normalize_text("line1\n\nline2") == "line1 line2"
