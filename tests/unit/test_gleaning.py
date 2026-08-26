"""Tests for gleaning (multi-pass extraction)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from engram.config import EngramConfig
from engram.ingestion.extractor import Extractor


def _make_fact_json(subject: str, obj: str, predicate: str = "related_to") -> str:
    return json.dumps([{
        "subject": subject,
        "subject_type": "concept",
        "predicate": predicate,
        "object": obj,
        "object_type": "concept",
        "confidence": 0.9,
        "is_update": False,
        "reasoning": "test fact",
    }])


@pytest.fixture
def config_no_glean() -> EngramConfig:
    return EngramConfig(
        extraction_api_key="test-key",
        max_glean_rounds=0,
    )


@pytest.fixture
def config_one_glean() -> EngramConfig:
    return EngramConfig(
        extraction_api_key="test-key",
        max_glean_rounds=1,
    )


@pytest.fixture
def config_two_gleans() -> EngramConfig:
    return EngramConfig(
        extraction_api_key="test-key",
        max_glean_rounds=2,
    )


async def test_no_gleaning_when_disabled(config_no_glean):
    extractor = Extractor(config_no_glean)
    initial_facts = _make_fact_json("A", "B")

    with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = initial_facts
        facts = await extractor.extract_facts("some text")

    assert len(facts) == 1
    assert mock_llm.call_count == 1  # Only initial call, no gleaning


async def test_gleaning_adds_new_facts(config_one_glean):
    extractor = Extractor(config_one_glean)
    initial_facts = _make_fact_json("A", "B")
    glean_facts = _make_fact_json("C", "D")

    with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = [initial_facts, glean_facts]
        facts = await extractor.extract_facts("some dense text")

    assert len(facts) == 2
    assert facts[0].subject == "A"
    assert facts[1].subject == "C"
    assert mock_llm.call_count == 2


async def test_gleaning_early_termination_on_empty(config_one_glean):
    extractor = Extractor(config_one_glean)
    initial_facts = _make_fact_json("A", "B")

    with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = [initial_facts, "[]"]
        facts = await extractor.extract_facts("some text")

    assert len(facts) == 1
    assert mock_llm.call_count == 2  # Called but returned empty


async def test_gleaning_skipped_when_initial_empty(config_one_glean):
    extractor = Extractor(config_one_glean)

    with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "[]"
        facts = await extractor.extract_facts("some text")

    assert len(facts) == 0
    assert mock_llm.call_count == 1  # No gleaning attempted


async def test_multiple_glean_rounds(config_two_gleans):
    extractor = Extractor(config_two_gleans)
    round0 = _make_fact_json("A", "B")
    round1 = _make_fact_json("C", "D")
    round2 = _make_fact_json("E", "F")

    with patch.object(extractor, "_call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = [round0, round1, round2]
        facts = await extractor.extract_facts("very dense text")

    assert len(facts) == 3
    assert mock_llm.call_count == 3


async def test_empty_text_skips_everything(config_one_glean):
    extractor = Extractor(config_one_glean)
    facts = await extractor.extract_facts("   ")
    assert facts == []
