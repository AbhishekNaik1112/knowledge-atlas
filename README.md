# Knowledge Atlas

*A Knowledge Catalog API for OKF (Open Knowledge Format) bundles — REST + web UI over a Markdown knowledge graph.*

A backend service that ingests **OKF (Open Knowledge Format)** bundles — directories of Markdown files
with YAML frontmatter — into PostgreSQL and exposes them through a REST API and a small web UI: CRUD,
tag/type filtering, full-text and semantic search, a validator, a GitHub auto-sync webhook, and an
interactive cross-link graph.

Built **test-first (TDD)** on an entirely **free / open-source stack**. 172 tests (+2 opt-in real-model), no paid services required.

> OKF is Google's open, vendor-neutral format for knowledge-as-files. Each concept is one Markdown file
> with a small YAML header (`type` is the only required field); concepts cross-link with normal Markdown
> links, forming a graph. Spec: <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md> (Apache-2.0).

---

## Features

- **Ingest** an OKF bundle from a directory or a `.zip` — parses frontmatter, derives concept IDs from
  paths, skips `index.md`/`log.md`, extracts cross-links into a graph, and is idempotent on re-ingest.
- **CRUD** over concepts with slash-containing IDs (e.g. `tables/users`).
- **Filter** by `type` and `tags` (AND semantics via Postgres arrays), paginated.
- **Full-text & semantic search** (`tsvector` + `ts_rank_cd`), with hosted **Gemini Embeddings** (`gemini-embedding-001`, 384-dim via `httpx`, zero PyTorch RAM overhead) or optional local `sentence-transformers` + `pgvector` cosine + **hybrid** reciprocal-rank fusion (with graceful keyword fallback).
- **Link graph** — outgoing links, backlinks, and a whole-catalog `/graph` JSON.
- **Validator** — lint a bundle for missing `type`, duplicate IDs, and dangling links (no persistence).
- **GitHub webhook & embed status** — HMAC-SHA256-verified push → background re-ingest with **prune-on-sync**, branch & `GITHUB_SYNC_SUBDIR` scoping, `sync_events` activity log tracking live `in_progress` / `ok` / `skipped` / `error` embed status + plain-English `embed_detail`, and optional multi-repo namespace isolation (`@repo/path` cross-links).
- **Hosted `/mcp` & Antigravity Second Brain Skill** — Streamable HTTP MCP server at `POST /mcp` (`search_concepts`, `get_concept`, `get_graph`, `upsert_concept`, `list_sync_activity`) paired with `.agents/skills/knowledge-atlas-curator/SKILL.md` for compounding note workflows.
- **Portable `.zip` export** — `GET /export.zip` (optional `?bundle=`) exports stored concepts back into valid OKF Markdown + YAML frontmatter bundles.
- **Private cloud mode & abuse-proof hardening** — open local self-host by default, or set `PRIVATE_MODE=true` for fail-closed GitHub OAuth allowlist UI login (`/auth/github`), signed `HttpOnly` session cookies, Bearer `API_KEY` for `/mcp` & REST, IP rate limiting, security headers (`CSP`, `X-Frame-Options`, `HSTS`), zip-bomb/path-traversal caps, and SSRF protection.
- **Web UI** — Warm Paper / Charcoal light & dark theme toggle, `/` & `⌘K` search shortcut, live hybrid/keyword search, `Recently Updated` / `A–Z` sort, filters, clickable sync & embed activity feed (`/ui/activity`), editorial concept reader, and theme-aware Cytoscape link graph (`/ui/graph`) with live node highlighting.

See [CONTRIBUTING_DOCS.md](CONTRIBUTING_DOCS.md) for where to add `.md` files and the required OKF frontmatter format.

## Architecture

Layered and test-driven: pure functions (`parser`, `links`, `rules`) → repositories (SQL behind a thin
surface) → services (`ConceptService`, `IngestService`) → HTTP routers. One request = one session /
unit of work. See `NOTES.md` for the build log.

```
app/
  main.py            app factory + error handlers        parser.py    frontmatter → ParsedConcept
  db.py              SQLAlchemy models + engine           links.py     markdown link extraction/resolution
  config.py          pydantic-settings                    rules.py     bundle validation
  models.py          Pydantic API DTOs                    bundle.py    dir/zip reader
  repository.py      concept / edge / search repos        ingest.py    IngestService (parse→persist→embed)
  services.py        ConceptService (write + edge sync)   embeddings.py Gemini + local ST embedders
  security.py        API-key + OAuth session guards       webhook.py   HMAC verify + RepoSyncer
  middleware.py      security headers, limits, rate-limit render.py    markdown → HTML
  routers/           auth, concepts, export, graph, ingest, mcp, search, ui, validate, webhooks
  templates/         Jinja + htmx pages
tests/               unit / repo / api  (+ real crypto_bitcoin fixture)
```

---

## Requirements

- Python 3.11+
- Docker (runs the local Postgres + `pgvector` container)

## Quickstart

```bash
# 1. Start Postgres (pgvector) — mapped to host port 5433 to avoid a host Postgres on 5432
docker compose up -d

# 2. Virtualenv + install
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"     # Windows
# .venv/bin/python -m pip install -e ".[dev]"        # macOS/Linux

# 3. Create the schema on the dev database
.venv/Scripts/python -c "from app.db import make_engine, init_db; init_db(make_engine())"

# 4. Run
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Then load some data and open the UI:

```bash
# ingest the bundled Web Dev sample (56 cross-linked concepts)
curl -X POST "http://127.0.0.1:8000/ingest?path=demo/web-dev-atlas"
```

- Web UI:   http://127.0.0.1:8000/ui
- Graph:    http://127.0.0.1:8000/ui/graph
- Swagger:  http://127.0.0.1:8000/docs

## Environment variables

All optional; sensible local defaults. Copy `.env.example` to `.env` to override.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://okf:okf@localhost:5433/okf` | Postgres connection |
| `API_KEY` | *(unset → auth off)* | When set, writes require `X-API-Key` |
| `GITHUB_WEBHOOK_SECRET` | *(unset → webhook 503)* | HMAC secret for `/webhooks/github` |
| `GITHUB_SYNC_SUBDIR` | *(unset → repo root)* | Subfolder to ingest on webhook sync (e.g. `demo/web-dev-atlas`) |
| `GITHUB_SYNC_BRANCH` | *(repo default branch)* | Branch to sync on webhook push |
| `GITHUB_TOKEN` | *(unset)* | Optional PAT for cloning private repos |
| `GITHUB_REPO_URL` | *(unset)* | Enables `Edit on GitHub ↗` links on concept pages |
| `NAMESPACE_BY_BUNDLE` | `false` | Prefix concept IDs with `{bundle}/` for multi-repo isolation |
| `GITHUB_REPOS_CONFIG` | `{}` | JSON map of per-repo `subdir`/`branch`/`namespace` overrides |
| `EMBEDDINGS_ENABLED` | `false` | Compute embeddings on ingest + CRUD + webhook, and enable semantic/hybrid search |
| `GEMINI_API_KEY` | *(unset)* | Use hosted Gemini Embeddings (`384`-dim via `httpx`, no PyTorch needed) |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Gemini embedding model ID |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Fallback local sentence-transformers model (`384`-dim) |
| `PRIVATE_MODE` | `false` | Fail-closed auth across all read, write, UI, and `/mcp` routes; disables `path=` ingest & `/docs` |
| `SESSION_SECRET` | *(unset)* | HMAC secret for signing `ka_session` and OAuth `state` cookies |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | *(unset)* | GitHub OAuth / GitHub App credentials for `/auth/github` |
| `ALLOWED_GITHUB_LOGIN` | *(unset)* | Single GitHub username allowed to sign into `/ui` in private mode |
| `RATE_LIMIT_AUTH_PER_5MIN` / `RATE_LIMIT_API_PER_MIN` | `10` / `120` | Per-IP rate limits in `PRIVATE_MODE=true` |
| `AUTO_INIT_DB` | `false` | Run `init_db()` automatically on app startup |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | `50` / `200` | Default and max `limit` for `/concepts` and `/search` |

---

## API reference

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/ingest?path=<dir>` or multipart `file=<zip>` | Parse bundle → upsert concepts + edges (optional `prune`, `namespace_ids`). *(write: API key)* |
| `GET` | `/concepts?type=&tags=&bundle=&limit=&offset=` | List/filter; repeat `tags` for AND (case-insensitive) |
| `POST` | `/concepts` | Create *(write: API key)* |
| `GET` | `/concepts/{id}?render=true` | Fetch; `render=true` adds HTML |
| `PUT` / `DELETE` | `/concepts/{id}` | Update / delete *(write: API key)* |
| `GET` | `/concepts/{id}/links` | Outgoing links + backlinks |
| `GET` | `/search?q=&mode=&type=&tags=&bundle=` | `mode=keyword` (default) / `semantic` / `hybrid` |
| `POST` | `/validate?path=` or zip | Lint a bundle; returns issues, **does not persist** *(API key when set)* |
| `POST` | `/webhooks/github` | Verify `X-Hub-Signature-256`, background re-ingest + prune |
| `GET` | `/syncs` | Recent GitHub webhook sync events |
| `GET` | `/graph` | `{nodes, edges}` for the whole catalog |
| `POST` | `/mcp` | Hosted Streamable HTTP MCP endpoint for Antigravity *(Bearer `API_KEY`)* |
| `GET` | `/export.zip?bundle=` | Export stored concepts as a valid OKF Markdown `.zip` bundle |
| `GET` | `/auth/login`, `/auth/github` | GitHub OAuth sign-in flow (`POST /auth/logout` signs out) |
| `GET` | `/health` | Liveness |

Concept IDs are the file path within the bundle minus `.md` (e.g. `tables/users`), so every `{id}` route
uses a path converter — slashes work.

## Web UI

Server-rendered (Jinja + htmx), under `/ui`:

- `/ui` — browse all concepts with live search (`/` / `⌘K` shortcut, **hybrid** when `EMBEDDINGS_ENABLED=true`, else **keyword**), `Recently Updated` / `A–Z` sort, `Repo`/`Folder`/`Type`/`Tag` filters, and **Last GitHub sync** banner
- `/ui/activity` — recent GitHub webhook sync history (`+created / ~updated / -deleted`, status, clickable embed details & column tooltips)
- `/ui/concepts/{id}` — editorial Markdown reader, metadata, tags, outgoing links + backlinks, and optional `Edit on GitHub ↗` link
- `/ui/graph` — theme-aware Cytoscape.js graph of cross-links (type-colored nodes, live node filter, hover highlight, fit/re-layout)
- `/export.zip` — one-click portable OKF Markdown bundle download

## Search modes

- **keyword** (default) — Postgres `tsvector`, BM-like `ts_rank_cd` ordering, `ts_headline` snippets.
- **semantic** / **hybrid** — set `EMBEDDINGS_ENABLED=true` and provide `GEMINI_API_KEY` (lightweight HTTP embeddings, ideal for Render) or `pip install -e ".[semantic]"` for local `all-MiniLM-L6-v2`.
  Embeddings are stored in a `pgvector` column with an hnsw cosine index; **hybrid** fuses keyword and vector rankings via reciprocal-rank fusion (and falls back to keyword if embedding fails).

---

## Testing

```bash
docker compose up -d                      # tests use the okf_test database
.venv/Scripts/python -m pytest            # 172 tests (+2 opt-in real-model)
```

Each test runs inside a transaction that rolls back (fast, isolated) against real Postgres. The ingest
suite exercises a trimmed **real** `crypto_bitcoin` OKF bundle. The heavy real-model embedding test is
opt-in:

```bash
pip install -e ".[semantic]"
OKF_REAL_EMBED=1 .venv/Scripts/python -m pytest tests/unit/test_embeddings_real.py
```

---

## Notes & caveats

- **Postgres is on host port 5433** (not 5432) so it doesn't clash with a locally-installed Postgres.
- **SQLite is intentionally not used** — Postgres gives `tsvector`, `pgvector`, and cloud durability.
- **Schema is created via `init_db`** today; Alembic migrations are planned for deployment.
- **`/ingest?path=` reads a server-side directory** — meant for local/self-host use and automatically disabled when `PRIVATE_MODE=true`.
- **Cloud embeddings without PyTorch**: set `GEMINI_API_KEY` + `EMBEDDINGS_ENABLED=true` to use lightweight Gemini Embeddings (`384`-dim via `httpx`) on small/free hosts without installing `torch`.

## Roadmap

Phase A core MVP ✅ · B validator ✅ · C auth + webhook ✅ · D semantic/hybrid search ✅ · E web UI + graph ✅
· **F deploy (Render + Neon) ✅** (`render.yaml` Blueprint + `Dockerfile` + Neon Postgres).

License of the referenced OKF spec/samples: Apache-2.0.
