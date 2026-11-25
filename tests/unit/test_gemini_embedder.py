"""TDD tests for GeminiEmbedder (Phase 1)."""

from __future__ import annotations

import json
import math

import httpx
import pytest


def test_gemini_embedder_sends_header_and_normalizes():
    from app.embeddings import GeminiEmbedder

    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        body = json.loads(request.content.decode())
        assert "batchEmbedContents" in str(request.url)
        assert request.url.query == b""  # never pass API key in URL query
        assert request.headers["x-goog-api-key"] == "gem-secret-key"
        assert len(body["requests"]) == 2
        assert body["requests"][0]["outputDimensionality"] == 384
        return httpx.Response(
            200,
            json={
                "embeddings": [
                    {"values": [3.0, 4.0] + [0.0] * 382},
                    {"values": [0.0, 5.0, 12.0] + [0.0] * 381},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    embedder = GeminiEmbedder(api_key="gem-secret-key", client=client)

    vecs = embedder.encode(["hello", "world"])
    assert len(captured) == 1
    assert len(vecs) == 2
    assert len(vecs[0]) == 384
    assert math.isclose(sum(x * x for x in vecs[0]), 1.0, rel_tol=1e-6)
    assert math.isclose(vecs[0][0], 0.6, rel_tol=1e-6)
    assert math.isclose(vecs[0][1], 0.8, rel_tol=1e-6)
    assert math.isclose(sum(x * x for x in vecs[1]), 1.0, rel_tol=1e-6)


def test_gemini_embedder_empty_input():
    from app.embeddings import GeminiEmbedder

    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    embedder = GeminiEmbedder(
        api_key="gem-secret-key", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    assert embedder.encode([]) == []
    assert not called


def test_gemini_embedder_429_does_not_leak_api_key():
    from app.embeddings import GeminiEmbedder

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "quota exceeded"}})

    embedder = GeminiEmbedder(
        api_key="gem-super-secret-123",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=1,
        sleep_fn=lambda _: None,
    )
    with pytest.raises(RuntimeError) as exc_info:
        embedder.encode(["hello"])
    msg = str(exc_info.value)
    assert "429" in msg
    assert "gem-super-secret-123" not in msg


def test_gemini_embedder_truncates_long_text_and_chunks_by_15():
    from app.embeddings import GeminiEmbedder

    batches: list[list[str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        reqs = body["requests"]
        batches.append([r["content"]["parts"][0]["text"] for r in reqs])
        return httpx.Response(
            200, json={"embeddings": [{"values": [1.0] + [0.0] * 383} for _ in reqs]}
        )

    embedder = GeminiEmbedder(
        api_key="gem-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        batch_delay_seconds=0.0,
    )
    texts = ["x" * 10_000] + [f"doc {i}" for i in range(19)]
    vecs = embedder.encode(texts)
    assert len(vecs) == 20
    assert [len(b) for b in batches] == [15, 5]
    assert len(batches[0][0]) <= 6000


def test_gemini_embedder_retries_on_429_then_succeeds():
    from app.embeddings import GeminiEmbedder

    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "1"}, json={"error": "rate limit"})
        return httpx.Response(200, json={"embeddings": [{"values": [3.0, 4.0] + [0.0] * 382}]})

    embedder = GeminiEmbedder(
        api_key="gem-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep_fn=sleeps.append,
    )
    vecs = embedder.encode(["hello"])
    assert attempts == 2
    assert len(sleeps) == 1 and sleeps[0] == 1.0
    assert math.isclose(vecs[0][0], 0.6, rel_tol=1e-6)
