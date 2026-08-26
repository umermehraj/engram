"""Tests for utility functions."""

from engram.utils import (
    generate_id,
    count_tokens,
    format_timestamp,
    cosine_similarity,
    levenshtein_ratio,
)
from datetime import datetime


def test_generate_id_has_prefix():
    id_ = generate_id("ent")
    assert id_.startswith("ent_")
    assert len(id_) == 16  # "ent_" + 12 hex chars


def test_generate_id_unique():
    ids = {generate_id() for _ in range(100)}
    assert len(ids) == 100


def test_count_tokens_approximation():
    text = "Hello world, this is a test sentence."
    tokens = count_tokens(text)
    assert tokens > 0
    assert tokens < len(text)  # tokens < chars


def test_format_timestamp():
    dt = datetime(2026, 3, 1, 10, 30, 0)
    assert format_timestamp(dt) == "Mar 01, 2026"


def test_cosine_similarity_identical():
    v = [1.0, 0.0, 0.0]
    assert cosine_similarity(v, v) == 1.0


def test_cosine_similarity_orthogonal():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert cosine_similarity(a, b) == 0.0


def test_cosine_similarity_zero_vector():
    a = [0.0, 0.0]
    b = [1.0, 1.0]
    assert cosine_similarity(a, b) == 0.0


def test_levenshtein_ratio_identical():
    assert levenshtein_ratio("FastAPI", "FastAPI") == 1.0


def test_levenshtein_ratio_similar():
    ratio = levenshtein_ratio("FastAPI", "fast api")
    assert ratio > 0.5


def test_levenshtein_ratio_different():
    ratio = levenshtein_ratio("Python", "JavaScript")
    assert ratio < 0.5


def test_levenshtein_ratio_empty():
    assert levenshtein_ratio("", "hello") == 0.0
    assert levenshtein_ratio("hello", "") == 0.0
