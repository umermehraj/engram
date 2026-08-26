"""API authentication — Bearer token → tenant resolution."""

from __future__ import annotations

import hashlib

from fastapi import Depends, Header

from engram.exceptions import AuthError


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def get_client_from_request(
    authorization: str | None = Header(None),
) -> str:
    """Extract and validate API key, return tenant_id.

    For local/dev mode, returns 'default' tenant.
    """
    if not authorization:
        # Local mode — no auth required
        return "default"

    if not authorization.startswith("Bearer "):
        raise AuthError("Invalid authorization header format")

    token = authorization[7:]
    if not token:
        raise AuthError("Empty API key")

    # In cloud mode, we'd look up the tenant by hashed key.
    # For now, use the key hash as tenant_id.
    return hash_api_key(token)
