"""Text embeddings for semantic search.

Supports both hosted Gemini embeddings (via httpx, zero torch RAM overhead) and local
`sentence-transformers` (lazily imported only when used).
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from functools import lru_cache
from typing import Any, Protocol

import httpx
from fastapi import Depends

from app.config import Settings, get_settings

EMBED_DIM = 384  # matches pgvector Vector(384)
_GEMINI_BATCH_LIMIT = 15
_MAX_EMBED_CHARS = 6000
_GEMINI_TIMEOUT_SECONDS = 15.0
_MAX_RETRY_DELAY_SECONDS = 30.0


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


def encode_with_task(embedder: Embedder, texts: list[str], task_type: str) -> list[list[float]]:
    """Pass Gemini asymmetric taskType when using GeminiEmbedder; standard encode otherwise."""
    if isinstance(embedder, GeminiEmbedder):
        return embedder.encode(texts, task_type=task_type)
    return embedder.encode(texts)


def _retry_delay(resp: httpx.Response, base: float, attempt: int) -> float:
    raw = resp.headers.get("retry-after")
    if raw is not None:
        try:
            return min(max(float(raw), 0.1), _MAX_RETRY_DELAY_SECONDS)
        except ValueError:
            pass
    return min(base * (2**attempt), _MAX_RETRY_DELAY_SECONDS)


class GeminiEmbedder:
    """Hosted Gemini embeddings via REST batchEmbedContents (384-dim, throttled for free tier)."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-embedding-001",
        output_dim: int = EMBED_DIM,
        client: httpx.Client | None = None,
        max_retries: int = 3,
        backoff_seconds: float = 2.0,
        batch_delay_seconds: float = 0.5,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name.removeprefix("models/")
        self.output_dim = output_dim
        self._client = client
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.batch_delay_seconds = batch_delay_seconds
        self._sleep = sleep_fn

    def _post_batch(
        self,
        client: httpx.Client,
        url: str,
        headers: dict[str, str],
        chunk: list[str],
        *,
        task_type: str | None = None,
    ) -> list[list[float]]:
        requests_payload: list[dict[str, Any]] = []
        for text in chunk:
            item: dict[str, Any] = {
                "model": f"models/{self.model_name}",
                "content": {"parts": [{"text": text[:_MAX_EMBED_CHARS]}]},
                "outputDimensionality": self.output_dim,
            }
            if task_type is not None:
                item["taskType"] = task_type
            requests_payload.append(item)
        payload = {"requests": requests_payload}
        for attempt in range(self.max_retries):
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 429 and attempt < self.max_retries - 1:
                self._sleep(_retry_delay(resp, self.backoff_seconds, attempt))
                continue
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Gemini embedding request failed with HTTP {resp.status_code}"
                )
            embeddings = resp.json().get("embeddings", [])
            if len(embeddings) != len(chunk):
                raise RuntimeError(
                    f"Gemini embedding count mismatch: expected {len(chunk)}, got {len(embeddings)}"
                )
            return [_l2_normalize([float(x) for x in emb["values"]]) for emb in embeddings]
        raise RuntimeError("Gemini embedding request failed with HTTP 429")

    def encode(
        self, texts: list[str], *, task_type: str | None = None
    ) -> list[list[float]]:
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
                if start > 0 and self.batch_delay_seconds > 0:
                    self._sleep(self.batch_delay_seconds)
                chunk = texts[start : start + _GEMINI_BATCH_LIMIT]
                out.extend(self._post_batch(client, url, headers, chunk, task_type=task_type))
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
