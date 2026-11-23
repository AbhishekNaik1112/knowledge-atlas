---
type: technical-note
title: "Unit vs Integration Testing in Web APIs"
description: "Balancing fast isolated unit tests against real-database integration tests."
tags: [testing, backend, quality]
resource: https://martinfowler.com/bliki/TestPyramid.html
---

# Unit vs Integration Testing in Web APIs

Reliable web services combine fast unit tests for pure logic with transaction-isolated integration tests against real databases.

## Guidelines
- **Unit Tests:** Exercise pure parsers, validators, and link resolvers with zero I/O.
- **Integration Tests:** Run HTTP routes and SQL queries against real Postgres inside rolled-back transactions, avoiding mocks for SQL behavior like [full-text search](../database/btree-indexes.md) and [ACID transactions](../database/acid-transactions.md).
- Pair with [API contract testing](contract-testing-apis.md) and [E2E tests](e2e-playwright-testing.md).
