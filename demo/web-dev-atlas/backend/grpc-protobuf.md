---
type: architecture-guide
title: "gRPC and Protocol Buffers"
description: "High-throughput internal service-to-service RPC using HTTP/2 and binary Protobuf schemas."
tags: [backend, grpc, networking]
resource: https://grpc.io/docs/what-is-grpc/introduction/
---

# gRPC and Protocol Buffers

gRPC uses [HTTP/2](../http/http2-multiplexing.md) and binary Protocol Buffers for strongly typed, low-latency service-to-service calls.

## Strengths
- **Compact Payloads & Codegen:** Generates client/server stubs across languages from `.proto` contracts.
- **Streaming:** Supports unary, server, client, and bidirectional streaming.
- For browser clients, pair with gRPC-Web or expose a [REST API](../http/rest-api-design.md) gateway.
