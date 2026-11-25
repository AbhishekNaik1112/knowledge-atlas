# Authoring OKF Markdown Docs (`demo/web-dev-atlas`)

This guide explains **where** to place new `.md` files and **what format** they must follow so GitHub webhook syncs and CI validation stay green.

---

## 1. Where to Add Files

Place new concept files under `demo/web-dev-atlas/<folder>/<concept-name>.md` (matching `GITHUB_SYNC_SUBDIR=demo/web-dev-atlas` on Render).

The relative path (minus `.md`) becomes the concept's **ID** and URL (`/ui/concepts/<id>`):
- `demo/web-dev-atlas/security/cors.md` → ID `security/cors`

### Existing Folders
| Folder | Use for |
|---|---|
| `ai-systems/` | LLM wikis, embeddings, MCP patterns, prompt caching, agent sandboxing |
| `architecture/` | System design patterns, gateways, circuit breakers, event-driven flows |
| `backend/` | APIs, RPC, middleware, job queues, logging, schemas |
| `database/` | Postgres, indexing, pooling, transactions, Redis caching |
| `devops/` | Docker, Nginx, health probes, deployments, tracing, feature flags |
| `frontend/` | Browser rendering, JS event loop, workers, CSS, SSR, accessibility |
| `http/` | HTTP/2, HTTP/3, caching, cookies, compression, webhooks, REST |
| `patterns/` | Cross-cutting engineering patterns (e.g. rate limiting) |
| `performance/` | Core Web Vitals, CDN, code splitting, image optimization, profiling |
| `realtime/` | WebSockets, Server-Sent Events (SSE), streaming |
| `security/` | CORS, CSP, CSRF, XSS, JWT, OAuth2/PKCE, Argon2id, SQLi, TLS |
| `testing/` | Unit, integration, contract, and E2E testing |

You can also create a new subfolder under `demo/web-dev-atlas/` if a topic doesn't fit any existing folder.  
`index.md` and `log.md` are treated as structural navigation files and skipped during ingest.  
Concepts can also be created directly via the hosted `/mcp` endpoint (`bundle="mcp"`) using Antigravity.

---

## 2. Required `.md` Format (YAML Frontmatter + Body)

Every concept file **must** start with YAML frontmatter containing a non-empty `type` field:

```markdown
---
type: technical-note
title: "Short Descriptive Title"
description: "One-sentence summary shown on catalog cards and search excerpts."
tags: [http, caching, performance]
resource: https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching
---

# Short Descriptive Title

Concise explanation, key tradeoffs, and examples.

## Related
- Link to another concept in the same folder: [REST API Design](rest-api-design.md)
- Link to another folder: [CORS](../security/cors.md)
```

### Frontmatter Fields
| Field | Required | Notes |
|---|---|---|
| `type` | **Yes** | Recommended values: `technical-note`, `architecture-guide`, `security-note`, `pattern`, `reference` |
| `title` | Recommended | Quote with `"..."` if it contains `: ` (colon + space) |
| `description` | Recommended | Used on catalog cards and as a search snippet fallback; quote if it contains `: ` |
| `tags` | Optional | YAML list (`[a, b]`); automatically normalized to lowercase |
| `resource` | Optional | External reference URL (shown as `Reference ↗` on the concept page) |
| `timestamp` | Optional | ISO-8601 date/time |
| *(any other key)* | Optional | Preserved as custom metadata in `extra` |

---

## 3. Cross-Linking Rules

- **Same repo:** Use standard relative Markdown links (`[CORS](../security/cors.md)` or `[Caching](caching.md)`). Broken relative targets are flagged as `dangling_link` warnings.
- **Cross-repo (when `NAMESPACE_BY_BUNDLE=true`):** Use `@repo/<path>` (e.g., `[Auth](@backend-api/security/jwt.md)`).

---

## 4. Validate Locally Before Pushing

```powershell
.venv/Scripts/python -c "from app.bundle import read_dir; from app.rules import validate_bundle; _, e = read_dir('demo/web-dev-atlas'); r = validate_bundle([(x.rel_path, x.text) for x in e]); print('concepts:', r.concept_count, 'issues:', r.issues)"
```
