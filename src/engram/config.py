"""Configuration management for Engram."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EngramConfig:
    """Global configuration, resolved from kwargs → env vars → defaults."""

    # Mode
    local: bool = True
    api_key: str | None = None
    api_base_url: str = "https://api.engram.dev"

    # Storage paths (local mode)
    storage_path: str = "./engram_data"

    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"  # local default
    embedding_dim: int = 384
    cloud_embedding_model: str = "text-embedding-3-small"
    cloud_embedding_dim: int = 1536

    # Google (multimodal embeddings)
    google_api_key: str | None = None

    # LLM for extraction
    extraction_model: str = "gpt-4.1-nano"
    extraction_api_key: str | None = None

    # Database (cloud mode)
    database_url: str | None = None  # PostgreSQL connection string

    # Retrieval defaults
    default_top_k: int = 10
    default_token_budget: int = 4000
    max_hops: int = 3

    # Entity resolution
    dedup_similarity_threshold: float = 0.92
    dedup_fuzzy_threshold: float = 0.85

    # Temporal
    recency_decay_rate: float = 0.02  # half-life ~35 hours
    recency_window_days: int = 7
    reference_window_days: int = 3

    # Gleaning (multi-pass extraction)
    max_glean_rounds: int = 1  # 0 = no gleaning, 1+ = additional extraction passes

    # Reranker (optional cross-encoder)
    reranker_model: str | None = None  # e.g., "BAAI/bge-reranker-v2-m3"
    reranker_top_k: int = 30

    @classmethod
    def from_env(cls, **overrides) -> EngramConfig:
        """Build config from environment variables with explicit overrides taking priority."""
        env_map = {
            "api_key": "ENGRAM_API_KEY",
            "api_base_url": "ENGRAM_API_BASE_URL",
            "storage_path": "ENGRAM_STORAGE_PATH",
            "embedding_model": "ENGRAM_EMBEDDING_MODEL",
            "extraction_model": "ENGRAM_EXTRACTION_MODEL",
            "extraction_api_key": "ENGRAM_EXTRACTION_API_KEY",
            "google_api_key": "ENGRAM_GOOGLE_API_KEY",
            "database_url": "ENGRAM_DATABASE_URL",
        }

        kwargs: dict = {}
        for field_name, env_var in env_map.items():
            val = os.environ.get(env_var)
            if val is not None:
                kwargs[field_name] = val

        # Overrides take priority over env vars
        kwargs.update(overrides)

        # If api_key is set, default to cloud mode
        if kwargs.get("api_key") and "local" not in overrides:
            kwargs["local"] = False

        # Also check GOOGLE_API_KEY as fallback
        if not kwargs.get("google_api_key"):
            kwargs.setdefault("google_api_key", os.environ.get("GOOGLE_API_KEY"))

        # Resolve embedding dim based on model
        model = kwargs.get("embedding_model", "")
        if model == "text-embedding-3-small":
            kwargs.setdefault("embedding_dim", 1536)
        elif model.startswith("models/") or model.startswith("gemini"):
            kwargs.setdefault("embedding_dim", 3072)

        return cls(**kwargs)

    @property
    def kuzu_path(self) -> Path:
        return Path(self.storage_path) / "kuzu"

    @property
    def lancedb_path(self) -> Path:
        return Path(self.storage_path) / "lancedb"

    @property
    def sqlite_path(self) -> Path:
        return Path(self.storage_path) / "metadata.db"

    @property
    def sqlite_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.sqlite_path}"

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return self.sqlite_url
