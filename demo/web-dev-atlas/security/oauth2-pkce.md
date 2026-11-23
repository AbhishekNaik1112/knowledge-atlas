---
type: security-note
title: "OAuth 2.0 Authorization Code Flow with PKCE"
description: "Securing public SPA and mobile OAuth logins using Proof Key for Code Exchange."
tags: [auth, oauth2, security]
resource: https://oauth.net/2/pkce/
---

# OAuth 2.0 Authorization Code Flow with PKCE

PKCE (Proof Key for Code Exchange) prevents authorization code interception in public clients that cannot store a client secret.

## Flow Summary
1. Client generates a random `code_verifier` and sends its SHA-256 `code_challenge`.
2. Authorization server returns an authorization `code`.
3. Client exchanges `code` + `code_verifier` for [JWT](jwt-auth.md) access/refresh tokens.
