---
type: security-note
title: "Cross-Site Scripting (XSS) Prevention"
description: "Stopping untrusted script execution with contextual output escaping, sanitization, and CSP."
tags: [security, xss, frontend]
resource: https://owasp.org/www-community/attacks/xss/
---

# Cross-Site Scripting (XSS) Prevention

XSS occurs when untrusted user input is rendered into the DOM as executable JavaScript.

## Defense in Depth
- **Context-Aware Escaping:** Rely on framework auto-escaping; avoid `innerHTML` or `dangerouslySetInnerHTML`.
- **HTML Sanitization:** Strip `<script>` and `on*` attributes when rendering user Markdown/HTML.
- **CSP & HttpOnly:** Enforce a strict [Content Security Policy](csp-headers.md) and mark [cookies HttpOnly](../http/cookies-samesite.md).
