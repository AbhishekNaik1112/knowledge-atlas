---
type: architecture-guide
title: WebSockets vs Server-Sent Events (SSE)
description: Choosing between full-duplex WebSockets and unidirectional HTTP streaming with SSE.
tags: [realtime, websockets, sse, http]
resource: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
---

# WebSockets vs Server-Sent Events (SSE)

When a web app needs live updates without polling a [REST API](../http/rest-api-design.md), the two primary browser-native transports are **WebSockets** and **Server-Sent Events (SSE)**.

## Comparison
- **WebSockets (`ws://` / `wss://`):** Full-duplex TCP upgrade; ideal for chat, collaborative editing, and multiplayer games where client and server both push messages frequently.
- **Server-Sent Events (`text/event-stream`):** Unidirectional server-to-client streaming over standard HTTP; includes automatic browser reconnection (`EventSource`), `Last-Event-ID` replay, and works cleanly behind standard proxies.

For AI token streaming, live dashboards, and notifications, SSE is simpler to operate and easier to protect with [rate limiting](../patterns/rate-limiting.md).
