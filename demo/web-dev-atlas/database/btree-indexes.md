---
type: technical-note
title: "B-Tree, Composite, and GIN Indexes in Postgres"
description: "Choosing the right index structure for equality, range, array, and full-text queries."
tags: [database, postgres, performance]
resource: https://www.postgresql.org/docs/current/indexes-types.html
---

# B-Tree, Composite, and GIN Indexes in Postgres

Indexes trade extra write/storage overhead for orders-of-magnitude faster reads.

## Index Types
- **B-Tree:** Default for `=`, `<`, `>`, `ORDER BY`. In composite `(a, b)` indexes, column order matters (leftmost prefix).
- **GIN:** Inverted index for `TEXT[]` array containment (`@>`) and `tsvector` full-text search.
- **HNSW (pgvector):** Approximate nearest-neighbor graph for semantic embeddings.
