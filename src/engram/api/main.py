"""FastAPI application factory for Engram REST API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from engram.api.auth import get_client_from_request
from engram.api.routes import health, memories, search, users
from engram.client import MemoryClient
from engram.config import EngramConfig
from engram.exceptions import AuthError, EngramError, ValidationError

# Global client instance (set during lifespan)
_client: MemoryClient | None = None


def get_client() -> MemoryClient:
    assert _client is not None, "Server not initialized"
    return _client


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    config = EngramConfig.from_env(local=True)
    _client = MemoryClient(config=config)
    await _client._ensure_initialized()
    yield
    await _client.close()
    _client = None


def create_app() -> FastAPI:
    app = FastAPI(
        title="Engram",
        description="Hybrid memory layer for AI agents",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError):
        return JSONResponse(status_code=401, content={"error": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(EngramError)
    async def engram_error_handler(request: Request, exc: EngramError):
        return JSONResponse(status_code=500, content={"error": str(exc)})

    # Register routers
    app.include_router(health.router, prefix="/v1", tags=["health"])
    app.include_router(memories.router, prefix="/v1", tags=["memories"])
    app.include_router(search.router, prefix="/v1", tags=["search"])
    app.include_router(users.router, prefix="/v1", tags=["users"])

    return app


app = create_app()
