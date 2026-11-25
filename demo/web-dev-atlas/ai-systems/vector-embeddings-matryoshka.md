---
type: technical-note
title: "Matryoshka Vector Embeddings (384d)"
description: "Truncating high-dimensional embeddings to 384 dimensions to balance semantic recall and low Postgres RAM."
tags: [ai-systems, embeddings, pgvector, performance]
resource: https://ai.google.dev/gemini-api/docs/embeddings
---

# Matryoshka Vector Embeddings (384d)

Matryoshka representation learning packs the most salient semantic signal into the earliest vector dimensions, allowing models like `gemini-embedding-001` to output compact `384`-dimensional embeddings.

## Why 384 Dimensions
- **Lower Memory Footprint:** Fits comfortably in free-tier Postgres alongside [pgvector HNSW indexes](../database/pgvector-semantic-search.md).
- **Zero Model Bloat:** Calling a hosted embedding API over HTTP avoids loading multi-gigabyte PyTorch runtimes in web containers.
- **L2 Normalization:** Always L2-normalize truncated vectors before cosine distance comparisons.
