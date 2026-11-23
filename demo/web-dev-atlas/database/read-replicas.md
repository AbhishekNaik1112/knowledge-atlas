---
type: architecture-guide
title: "Database Read Replicas and Replication Lag"
description: "Scaling read-heavy workloads while handling eventual consistency and read-your-writes."
tags: [database, postgres, architecture]
resource: https://www.postgresql.org/docs/current/warm-standby.html
---

# Database Read Replicas and Replication Lag

Streaming replication asynchronously copies WAL changes from a primary writer to one or more read replicas.

## Handling Replication Lag
- **Read-Your-Writes:** Route a user's reads to the primary for a few seconds after they perform a write.
- **Offload Analytics/Search:** Send heavy reporting queries to replicas while keeping [ACID writes](acid-transactions.md) on primary.
