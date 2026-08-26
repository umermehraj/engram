"""LLM-based entity and relationship extraction."""

from __future__ import annotations

import json
import logging
import httpx

from engram.config import EngramConfig
from engram.exceptions import ExtractionError
from engram.types import Fact

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a memory extraction system. Given a conversation
or document, extract structured facts as JSON.

For each fact, extract:
- subject: the entity performing/holding the fact
- subject_type: person | project | tool | concept | preference | organization
- predicate: the relationship type (decided, prefers, works_on, mentioned, asked_about, related_to, depends_on, part_of, believes, replaced, contradicts, supersedes)
- object: the target entity
- object_type: same types as subject_type
- confidence: 0.0-1.0 how confident you are this is a real fact
- is_update: true if this contradicts or updates a previously known fact
- reasoning: brief explanation of why this fact matters

Rules:
- Extract ONLY facts that would be useful to recall in future conversations
- Preferences > decisions > mentions (prioritize high-signal facts)
- If user corrects themselves, mark is_update=true
- Do NOT extract pleasantries, filler, or meta-conversation
- Output ONLY valid JSON array, no markdown, no preamble

Example output:
[
  {
    "subject": "user",
    "subject_type": "person",
    "predicate": "decided",
    "object": "FastAPI",
    "object_type": "tool",
    "confidence": 0.95,
    "is_update": false,
    "reasoning": "User explicitly stated their tech stack choice"
  }
]"""

GLEANING_SYSTEM_PROMPT = """You previously extracted the following facts from the text below.
Review the text again carefully. Extract any additional facts you MISSED in your first pass.
Focus on:
- Implicit relationships (entity A depends on B, but not stated directly)
- Secondary entities mentioned in passing
- Temporal facts (when things happened or changed)
- Contradictions or updates to previously known facts

Previously extracted facts:
{previous_facts}

Original text:
{original_text}

Return ONLY new facts not already in the list above. Output valid JSON array, no duplicates.
Use the same schema as before (subject, subject_type, predicate, object, object_type, confidence, is_update, reasoning)."""


class Extractor:
    def __init__(self, config: EngramConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def extract_facts(
        self,
        text: str,
        session_id: str | None = None,
    ) -> list[Fact]:
        """Extract structured facts from text using an LLM.

        Supports gleaning: after initial extraction, the LLM is called again
        with its own output to find missed facts. Controlled by config.max_glean_rounds.
        """
        if not text.strip():
            return []

        try:
            raw_json = await self._call_llm(text)
            facts = self._parse_facts(raw_json, session_id)

            for round_num in range(self.config.max_glean_rounds):
                if not facts:
                    break
                glean_prompt = GLEANING_SYSTEM_PROMPT.format(
                    previous_facts=json.dumps(
                        [f.model_dump(exclude={"id"}) for f in facts], default=str
                    ),
                    original_text=text,
                )
                glean_json = await self._call_llm(glean_prompt)
                new_facts = self._parse_facts(glean_json, session_id)
                if not new_facts:
                    break
                facts = [*facts, *new_facts]
                logger.info(
                    "Gleaning round %d: found %d additional facts",
                    round_num + 1,
                    len(new_facts),
                )

            return facts
        except Exception as e:
            logger.warning(f"Extraction failed: {e}")
            raise ExtractionError(f"Failed to extract facts: {e}") from e

    async def _call_llm(self, text: str) -> str:
        """Call the extraction LLM and return raw JSON response."""
        api_key = self.config.extraction_api_key
        if not api_key:
            raise ExtractionError(
                "No extraction API key configured. Set ENGRAM_EXTRACTION_API_KEY "
                "or pass extraction_api_key in config."
            )

        model = self.config.extraction_model
        client = await self._get_client()

        # Use OpenAI-compatible API
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
            },
        )

        if response.status_code != 200:
            raise ExtractionError(
                f"LLM API returned {response.status_code}: {response.text}"
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _parse_facts(self, raw_json: str, session_id: str | None) -> list[Fact]:
        """Parse LLM JSON output into Fact objects."""
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Invalid JSON from LLM: {e}") from e

        # Handle both array and object-with-array responses
        if isinstance(parsed, dict):
            # Try common wrapper keys
            for key in ("facts", "data", "results"):
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                parsed = [parsed]

        if not isinstance(parsed, list):
            raise ExtractionError(f"Expected JSON array, got {type(parsed)}")

        facts = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            try:
                facts.append(Fact(
                    subject=item.get("subject", ""),
                    subject_type=item.get("subject_type", ""),
                    predicate=item.get("predicate", "related_to"),
                    object=item.get("object", ""),
                    object_type=item.get("object_type", ""),
                    confidence=float(item.get("confidence", 0.5)),
                    is_update=bool(item.get("is_update", False)),
                    reasoning=item.get("reasoning", ""),
                    source_session_id=session_id,
                ))
            except Exception as e:
                logger.warning(f"Skipping invalid fact: {e}")
                continue

        return facts

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
