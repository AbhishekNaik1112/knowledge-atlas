---
type: architecture-guide
title: "GraphQL vs REST APIs"
description: "Comparing schema-driven GraphQL queries against resource-oriented REST endpoints."
tags: [backend, api-design, graphql, rest]
resource: https://graphql.org/learn/
---

# GraphQL vs REST APIs

While [REST](../http/rest-api-design.md) exposes fixed resource URLs, GraphQL exposes a single typed endpoint where clients specify exact fields.

## Tradeoffs
- **GraphQL Pros:** Eliminates over-fetching/under-fetching across nested relations.
- **GraphQL Cons:** Harder [HTTP caching](../http/caching.md), and requires query depth/complexity limits to prevent [N+1 database queries](../database/n-plus-one-queries.md) and DoS.
