"""Shared test fixtures for Engram."""

import os
import tempfile
import pytest
import pytest_asyncio

from engram.config import EngramConfig
from engram.client import MemoryClient


@pytest.fixture
def tmp_storage(tmp_path):
    """Temporary storage directory for tests."""
    return str(tmp_path / "engram_test")


@pytest.fixture
def config(tmp_storage):
    """Test configuration with local storage."""
    return EngramConfig(
        local=True,
        storage_path=tmp_storage,
        embedding_model="all-MiniLM-L6-v2",
        embedding_dim=384,
    )


@pytest_asyncio.fixture
async def client(config):
    """Initialized MemoryClient for testing."""
    c = MemoryClient(config=config)
    await c._ensure_initialized()
    yield c
    await c.close()
