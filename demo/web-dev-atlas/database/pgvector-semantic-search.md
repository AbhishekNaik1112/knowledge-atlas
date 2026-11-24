---
type: technical-note
title: "pgvector Semantic Search and Embedding Sync"
description: "Storing dense vector embeddings in Postgres with HNSW indexes and keeping embedding sync non-fatal."
tags: [database, postgres, pgvector, embeddings]
resource: https://github.com/pgvector/pgvector
---

# pgvector Semantic Search and Embedding Sync

Vector embeddings map text into dense numerical vectors so Postgres can rank results by cosine similarity alongside full-text keyword search.

## Key Practices
- **HNSW Indexing:** Use `vector_cosine_ops` with an HNSW index for fast approximate nearest-neighbor lookup.
- **Non-Fatal Sync:** When syncing documents via [event-driven webhooks](../architecture/event-driven-webhooks.md), commit document upserts independently of embedding generation so rate limits or model failures do not roll back core catalog data.
- **Visibility:** Track `embed_status` (`ok`, `skipped`, `error`) and `embedded_count` per sync event so users know whether semantic search is up to date.
