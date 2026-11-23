---
type: technical-note
title: "Database Connection Pooling"
description: "Preventing Postgres connection exhaustion with application pools and PgBouncer."
tags: [database, postgres, performance]
resource: https://www.pgbouncer.org/
---

# Database Connection Pooling

Each PostgreSQL connection spawns a backend OS process (~5–10 MB RAM). Opening a new connection per HTTP request causes severe latency and `max_connections` exhaustion.

## Pooling Tiers
- **App-Level Pool:** SQLAlchemy/asyncpg pools reuse TCP+TLS sessions across requests.
- **Transaction Pooling (PgBouncer):** Multiplexes thousands of serverless or [multi-replica](../devops/blue-green-deployments.md) workers onto a small pool of Postgres backends.
