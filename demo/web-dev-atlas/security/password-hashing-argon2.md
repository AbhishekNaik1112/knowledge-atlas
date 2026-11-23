---
type: security-note
title: "Password Hashing with Argon2id"
description: "Why memory-hard KDFs like Argon2id beat fast hashes and bcrypt for credential storage."
tags: [security, auth, cryptography]
resource: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
---

# Password Hashing with Argon2id

Never store plaintext passwords or use fast hashes (`SHA-256`). Use a salted, memory-hard Key Derivation Function.

## Recommendations
- **Argon2id:** Default choice (resists both GPU/ASIC cracking and side-channel attacks).
- **Rate Limiting:** Protect login endpoints with [API rate limiting](../patterns/rate-limiting.md) to slow online brute force.
