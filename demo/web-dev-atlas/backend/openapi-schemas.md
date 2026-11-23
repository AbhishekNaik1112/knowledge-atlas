---
type: reference
title: "OpenAPI Contracts and Schema Validation"
description: "Generating typed API docs, client SDKs, and runtime request validation from OpenAPI 3.1."
tags: [backend, api-design, testing]
resource: https://spec.openapis.org/oas/latest.html
---

# OpenAPI Contracts and Schema Validation

OpenAPI defines a machine-readable contract for [REST APIs](../http/rest-api-design.md): paths, parameters, schemas, and status codes.

## Benefits
- **Fail Fast:** Validate types, lengths, and enums at the boundary before hitting business logic or [SQL](../security/sql-injection-prevention.md).
- **Interactive Docs:** Powers Swagger UI and typed TypeScript/Python client generation.
