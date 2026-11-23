---
type: pattern
title: "API Contract Testing with OpenAPI"
description: "Preventing breaking changes between frontend clients and backend services using schema contracts."
tags: [testing, api-design, openapi]
resource: https://spec.openapis.org/oas/latest.html
---

# API Contract Testing with OpenAPI

Contract tests verify that API providers and consumers agree on request/response payloads without spinning up full staging environments.

## Workflow
- Validate response models against [OpenAPI schemas](../backend/openapi-schemas.md) on every PR.
- Catch breaking field renames or status code changes before [blue-green deployments](../devops/blue-green-deployments.md).
- Complement with [unit and integration tests](unit-vs-integration-testing.md).
