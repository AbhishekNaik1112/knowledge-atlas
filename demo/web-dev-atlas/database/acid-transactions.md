---
type: technical-note
title: "ACID Transactions and Isolation Levels"
description: "Understanding Read Committed, Repeatable Read, Serializable, and row locking."
tags: [database, postgres, reliability]
resource: https://www.postgresql.org/docs/current/transaction-iso.html
---

# ACID Transactions and Isolation Levels

Transactions group multiple reads/writes into an atomic unit of work (all commit or all roll back).

## Isolation Levels
- **Read Committed (Postgres default):** Sees committed data per statement; vulnerable to non-repeatable reads.
- **Repeatable Read:** Snapshot at transaction start; prevents non-repeatable reads.
- **Serializable:** Prevents write skew; requires retry logic on serialization failures. Useful with [idempotency keys](../backend/idempotency-keys.md).
