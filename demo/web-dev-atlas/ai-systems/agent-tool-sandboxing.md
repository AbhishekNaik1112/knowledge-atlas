---
type: security-note
title: "Agent Tool Sandboxing and Fail-Closed Auth"
description: "Protecting hosted AI agent endpoints against SSRF, path traversal, zip bombs, and unauthenticated abuse."
tags: [ai-systems, security, oauth, sandboxing]
---

# Agent Tool Sandboxing and Fail-Closed Auth

Any HTTP tool endpoint exposed to AI agents must enforce strict boundaries so untrusted inputs cannot reach internal networks or server filesystems.

## Mandatory Guardrails
- **Fail-Closed Auth:** Reject unauthenticated requests when `PRIVATE_MODE` is enabled, pairing [OAuth2 PKCE / Allowlists](../security/oauth2-pkce.md) for UI users with constant-time Bearer keys for tools.
- **Disable Local Path Reads:** Never allow server-side filesystem `path=` ingestion in cloud mode.
- **Rate Limits & Caps:** Bound request body sizes, zip entry counts, and per-IP auth attempts.
