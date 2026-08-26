"""Tests for query classifier."""

from engram.retrieval.classifier import classify_query
from engram.types import QueryType


def test_temporal_query():
    w, qt = classify_query("When did we last discuss the backend?")
    assert w.temporal > w.vector
    assert w.temporal > w.graph
    assert qt == QueryType.TEMPORAL


def test_factual_query():
    w, qt = classify_query("What is the user's email address?")
    assert w.graph > w.vector
    assert w.graph > w.temporal
    assert qt == QueryType.FACTUAL


def test_preference_query():
    w, qt = classify_query("Does the user prefer dark mode?")
    assert w.vector > w.graph
    assert w.vector > w.temporal
    assert qt == QueryType.PREFERENCE


def test_default_query():
    w, qt = classify_query("Tell me something interesting")
    assert w.vector == 0.35
    assert w.graph == 0.40
    assert w.temporal == 0.25
    assert qt == QueryType.DEFAULT


def test_recently_keyword():
    w, qt = classify_query("What was recently added to the project?")
    assert w.temporal == 0.50
    assert qt == QueryType.TEMPORAL


def test_global_overview_query():
    w, qt = classify_query("Give me an overview of everything")
    assert qt == QueryType.GLOBAL
    assert w.vector == 0.10
    assert w.graph == 0.20


def test_global_themes_query():
    w, qt = classify_query("What are the main topics in this knowledge base?")
    assert qt == QueryType.GLOBAL


def test_global_what_do_you_know():
    w, qt = classify_query("What do you know about this project?")
    assert qt == QueryType.GLOBAL
