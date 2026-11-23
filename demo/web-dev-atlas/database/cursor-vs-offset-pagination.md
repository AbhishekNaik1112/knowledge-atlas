---
type: pattern
title: "Cursor vs Offset Pagination"
description: "Why keyset (cursor) pagination scales to millions of rows without duplicate or skipped items."
tags: [database, api-design, performance]
resource: https://use-the-index-luke.com/no-offset
---

# Cursor vs Offset Pagination

`OFFSET 100000 LIMIT 20` forces Postgres to scan and discard 100,000 rows and drifts when new rows are inserted.

## Keyset (Cursor) Pagination
- Query `WHERE (created_at, id) < (:cursor_ts, :cursor_id) ORDER BY created_at DESC, id DESC LIMIT 20`.
- Uses a [composite B-Tree index](btree-indexes.md) for constant $O(\log N)$ time at any depth.
- Combine with [REST API conventions](../http/rest-api-design.md).
