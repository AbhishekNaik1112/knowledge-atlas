---
type: pattern
title: "Diagnosing and Fixing N+1 Query Problems"
description: "Replacing per-row ORM lazy loads with JOINs, IN-batches, and DataLoaders."
tags: [database, performance, backend]
resource: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
---

# Diagnosing and Fixing N+1 Query Problems

An N+1 problem occurs when fetching 1 parent list (1 query) triggers N separate queries for each item's related rows.

## Fixes
- **Eager Loading:** Use `JOIN` (`joinedload`) or `WHERE id IN (...)` (`selectinload`).
- **GraphQL DataLoader:** Batch and cache per-request lookups in [GraphQL resolvers](../backend/graphql-vs-rest.md).
