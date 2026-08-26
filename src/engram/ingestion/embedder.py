"""Embedding generation — local, OpenAI, or Google Gemini (multimodal)."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Any

from engram.config import EngramConfig


class Embedder:
    """
    Unified embedder supporting three providers:
    - local: sentence-transformers (text only, free, 384-dim)
    - openai: text-embedding-3-small (text only, 1536-dim)
    - google: gemini-embedding-2-preview (multimodal: text + images + video + audio + PDFs, 3072-dim)
    """

    def __init__(self, config: EngramConfig) -> None:
        self.config = config
        self._local_model = None
        self._openai_client = None
        self._google_client = None

    @property
    def provider(self) -> str:
        """Which embedding provider is active."""
        model = self.config.embedding_model
        if model.startswith("models/") or model.startswith("gemini"):
            return "google"
        if model.startswith("text-embedding"):
            return "openai"
        return "local"

    # ── Public API ────────────────────────────────────────────────────────

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        p = self.provider
        if p == "google":
            return await self._embed_google_text(text)
        if p == "openai":
            return await self._embed_openai(text)
        return await self._embed_local(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""
        p = self.provider
        if p == "google":
            return await self._embed_google_text_batch(texts)
        if p == "openai":
            return await self._embed_openai_batch(texts)
        return await self._embed_local_batch(texts)

    async def embed_image(self, image_path: str) -> list[float]:
        """Embed an image file (Google Gemini multimodal only)."""
        if self.provider != "google":
            raise NotImplementedError(
                "Image embedding requires Google Gemini. "
                "Set embedding_model='gemini-embedding-2-preview'"
            )
        return await self._embed_google_image(image_path)

    async def embed_file(self, file_path: str) -> list[float]:
        """Embed any supported file: image, video, audio, PDF (Google Gemini only).

        Supported formats:
        - Images: PNG, JPEG, GIF, WebP
        - Video: MP4, MOV, AVI (up to 120s)
        - Audio: MP3, WAV, FLAC (up to 80s)
        - Documents: PDF (up to 6 pages)
        """
        if self.provider != "google":
            raise NotImplementedError(
                "File embedding requires Google Gemini. "
                "Set embedding_model='gemini-embedding-2-preview'"
            )
        return await self._embed_google_image(file_path)  # same API handles all file types

    async def embed_multimodal(
        self, text: str | None = None, file_path: str | None = None
    ) -> list[float]:
        """Embed text + file together as a single multimodal embedding (Google Gemini only).

        The file can be an image, video, audio, or PDF.
        """
        if self.provider != "google":
            raise NotImplementedError(
                "Multimodal embedding requires Google Gemini. "
                "Set embedding_model='gemini-embedding-2-preview'"
            )
        return await self._embed_google_multimodal(text, file_path)

    # ── Local (sentence-transformers) ─────────────────────────────────────

    def _ensure_local_model(self):
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(self.config.embedding_model)

    async def _embed_local(self, text: str) -> list[float]:
        def _encode():
            self._ensure_local_model()
            return self._local_model.encode(text, normalize_embeddings=True).tolist()
        return await asyncio.get_event_loop().run_in_executor(None, _encode)

    async def _embed_local_batch(self, texts: list[str]) -> list[list[float]]:
        def _encode():
            self._ensure_local_model()
            embeddings = self._local_model.encode(
                texts, normalize_embeddings=True, batch_size=64
            )
            return [e.tolist() for e in embeddings]
        return await asyncio.get_event_loop().run_in_executor(None, _encode)

    # ── OpenAI ────────────────────────────────────────────────────────────

    async def _embed_openai(self, text: str) -> list[float]:
        results = await self._embed_openai_batch([text])
        return results[0]

    async def _embed_openai_batch(self, texts: list[str]) -> list[list[float]]:
        import openai
        if self._openai_client is None:
            self._openai_client = openai.AsyncOpenAI(
                api_key=self.config.extraction_api_key or self.config.api_key
            )
        response = await self._openai_client.embeddings.create(
            model=self.config.cloud_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    # ── Google Gemini (multimodal) ────────────────────────────────────────

    def _ensure_google_client(self):
        if self._google_client is None:
            from google import genai
            api_key = self.config.google_api_key or self.config.extraction_api_key
            if not api_key:
                raise ValueError(
                    "Google API key required for Gemini embeddings. "
                    "Set ENGRAM_GOOGLE_API_KEY or GOOGLE_API_KEY."
                )
            self._google_client = genai.Client(api_key=api_key)

    async def _embed_google_text(self, text: str) -> list[float]:
        def _call():
            self._ensure_google_client()
            result = self._google_client.models.embed_content(
                model=self.config.embedding_model,
                contents=text,
            )
            return list(result.embeddings[0].values)
        return await asyncio.get_event_loop().run_in_executor(None, _call)

    async def _embed_google_text_batch(self, texts: list[str]) -> list[list[float]]:
        def _call():
            self._ensure_google_client()
            result = self._google_client.models.embed_content(
                model=self.config.embedding_model,
                contents=texts,
            )
            return [list(emb.values) for emb in result.embeddings]
        return await asyncio.get_event_loop().run_in_executor(None, _call)

    async def _embed_google_image(self, image_path: str) -> list[float]:
        def _call():
            from google.genai import types
            self._ensure_google_client()

            path = Path(image_path)
            image_bytes = path.read_bytes()
            mime = _guess_mime(path)

            part = types.Part.from_bytes(data=image_bytes, mime_type=mime)
            result = self._google_client.models.embed_content(
                model=self.config.embedding_model,
                contents=part,
            )
            return list(result.embeddings[0].values)
        return await asyncio.get_event_loop().run_in_executor(None, _call)

    async def _embed_google_multimodal(
        self, text: str | None, image_path: str | None
    ) -> list[float]:
        """Embed text + image together as a single multimodal embedding."""
        def _call():
            from google.genai import types
            self._ensure_google_client()

            parts = []
            if text:
                parts.append(text)
            if image_path:
                path = Path(image_path)
                image_bytes = path.read_bytes()
                mime = _guess_mime(path)
                parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime))

            if not parts:
                raise ValueError("At least one of text or image_path must be provided")

            result = self._google_client.models.embed_content(
                model=self.config.embedding_model,
                contents=parts,
            )
            return list(result.embeddings[0].values)
        return await asyncio.get_event_loop().run_in_executor(None, _call)


def _guess_mime(path: Path) -> str:
    """Guess MIME type from file extension."""
    suffix = path.suffix.lower()
    return {
        # Images
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        # Documents
        ".pdf": "application/pdf",
        # Video
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm",
        # Audio
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
    }.get(suffix, "application/octet-stream")
