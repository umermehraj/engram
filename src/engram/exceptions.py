"""Custom exceptions for Engram."""


class EngramError(Exception):
    """Base exception for all Engram errors."""


class StorageError(EngramError):
    """Error in storage layer (Kuzu, LanceDB, or metadata DB)."""


class ExtractionError(EngramError):
    """Error during LLM-based entity/relationship extraction."""


class RetrievalError(EngramError):
    """Error during hybrid retrieval."""


class AuthError(EngramError):
    """Authentication or authorization error."""


class ValidationError(EngramError):
    """Input validation error."""


class ConflictError(EngramError):
    """Temporal conflict during ingestion (informational, not fatal)."""
