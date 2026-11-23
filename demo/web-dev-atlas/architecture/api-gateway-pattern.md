---
type: architecture-guide
title: "API Gateway Pattern"
description: "Centralizing authentication, rate limiting, routing, and observability at the edge."
tags: [architecture, api-design, backend]
resource: https://microservices.io/patterns/apigateway.html
---

# API Gateway Pattern

An API Gateway acts as a single entry point for client traffic, routing requests to internal [REST](../http/rest-api-design.md) or [gRPC](../backend/grpc-protobuf.md) services.

## Common Responsibilities
- Terminate [TLS 1.3](../security/tls-https-handshakes.md) and enforce [CORS](../security/cors.md) and [rate limiting](../patterns/rate-limiting.md).
- Validate [JWT bearer tokens](../security/jwt-auth.md) before forwarding requests through [middleware pipelines](../backend/middleware-pipelines.md).
- Inject correlation headers for [OpenTelemetry tracing](../devops/opentelemetry-tracing.md).
