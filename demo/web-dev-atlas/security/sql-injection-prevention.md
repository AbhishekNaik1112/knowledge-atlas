---
type: security-note
title: "SQL Injection Prevention"
description: "Eliminating SQL injection using parameterized queries, bound variables, and least-privilege DB roles."
tags: [security, database, backend]
resource: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
---

# SQL Injection Prevention

SQL injection happens when untrusted strings are concatenated directly into SQL statements.

## Safe Patterns
- **Parameterized Queries:** Always use bound parameters (`$1`, `:param`) via drivers or ORM query builders.
- **Allowlists for Identifiers:** Validate dynamic `ORDER BY` column names against a fixed map.
- **Schema Validation:** Validate incoming payloads with [OpenAPI / Pydantic schemas](../backend/openapi-schemas.md).
