---
type: security-note
title: Cross-Origin Resource Sharing (CORS)
description: How browsers enforce the Same-Origin Policy and how servers opt in via CORS headers.
tags: [http, security, browser]
resource: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
---

# Cross-Origin Resource Sharing (CORS)

Browsers enforce the **Same-Origin Policy (SOP)**, blocking JavaScript `fetch()` or `XMLHttpRequest` calls to a different scheme, host, or port unless the server explicitly permits it.

## Simple vs. Preflight Requests
- **Preflight (`OPTIONS`):** Triggered when sending custom headers (like `Authorization` for [JWT authentication](jwt-auth.md)) or non-simple methods (`PUT`, `DELETE`).
- **Response Headers:** `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, and `Access-Control-Allow-Headers` tell the browser which cross-origin [REST API](../http/rest-api-design.md) calls are allowed.
- **Credentials:** Never combine `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`; echo an explicit allowlisted origin instead.
