"""Text embeddings for semantic search.

Supports both hosted Gemini embeddings (via httpx, zero torch RAM overhead) and local
`sentence-transformers` (lazily imported only when used).
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Any, Protocol

import httpx
from fastapi import Depends

from app.config import Settings, get_settings

EMBED_DIM = 384  # matches pgvector Vector(384)
_GEMINI_BATCH_LIMIT = 100
_GEMINI_TIMEOUT_SECONDS = 15.0


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: Any = None  # loaded on first use

    def encode(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # heavy; deferred

            self._model = SentenceTransformer(self.model_name)
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm <= 0.0:
        return vec
    return [x / norm for x in vec]


def build_embed_text(title: str | None, description: str | None, body: str | None) -> str:
    """Canonical text input used for concept embeddings across ingest, CRUD, and MCP."""
    return " ".join(x for x in (title, description, body) if x)


class GeminiEmbedder:
    """Hosted Gemini embeddings via REST batchEmbedContents (384-dim, L2-normalized)."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-embedding-001",
        output_dim: int = EMBED_DIM,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name.removeprefix("models/")
        self.output_dim = output_dim
        self._client = client

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_name}:batchEmbedContents"
        )
        headers = {"x-goog-api-key": self.api_key}
        out: list[list[float]] = []

        own_client = self._client is None
        client = self._client or httpx.Client(timeout=_GEMINI_TIMEOUT_SECONDS)
        try:
            for start in range(0, len(texts), _GEMINI_BATCH_LIMIT):
                chunk = texts[start : start + _GEMINI_BATCH_LIMIT]
                payload = {
                    "requests": [
                        {
                            "model": f"models/{self.model_name}",
                            "content": {"parts": [{"text": text}]},
                            "outputDimensionality": self.output_dim,
                        }
                        for text in chunk
                    ]
                }
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    raise RuntimeError(
                        f"Gemini embedding request failed with HTTP {resp.status_code}"
                    )
                embeddings = resp.json().get("embeddings", [])
                if len(embeddings) != len(chunk):
                    raise RuntimeError(
                        f"Gemini embedding count mismatch: expected {len(chunk)}, got {len(embeddings)}"
                    )
                for item in embeddings:
                    out.append(_l2_normalize([float(x) for x in item["values"]]))
        finally:
            if own_client:
                client.close()
        return out


@lru_cache
def _default_embedder(model_name: str) -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(model_name=model_name)


@lru_cache
def _gemini_embedder(api_key: str, model_name: str) -> GeminiEmbedder:
    return GeminiEmbedder(api_key=api_key, model_name=model_name)


def get_embedder(settings: Settings = Depends(get_settings)) -> Embedder:
    """FastAPI dependency. Selects Gemini when GEMINI_API_KEY is set, else local ST."""
    if settings.gemini_api_key:
        return _gemini_embedder(settings.gemini_api_key, settings.gemini_embedding_model)
    return _default_embedder(settings.embedding_model)
