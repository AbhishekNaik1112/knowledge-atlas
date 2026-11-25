"""Export stored OKF concepts as a portable Markdown `.zip` bundle."""

from __future__ import annotations

import io
import zipfile
from typing import Any

import yaml
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.db import Concept
from app.dependencies import get_concept_repo
from app.repository import SqlConceptRepository
from app.security import require_private_access

router = APIRouter(tags=["export"], dependencies=[Depends(require_private_access)])


def _concept_to_markdown(c: Concept) -> str:
    meta: dict[str, Any] = {"type": c.type}
    if c.title is not None:
        meta["title"] = c.title
    if c.description is not None:
        meta["description"] = c.description
    if c.resource is not None:
        meta["resource"] = c.resource
    if c.timestamp is not None:
        meta["timestamp"] = c.timestamp.isoformat()
    if c.tags:
        meta["tags"] = list(c.tags)
    if c.frontmatter:
        for k, v in c.frontmatter.items():
            meta.setdefault(k, v)
    header = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()
    body = (c.body or "").lstrip("\n")
    return f"---\n{header}\n---\n\n{body}" if body else f"---\n{header}\n---\n"


@router.get("/export.zip")
def export_zip(
    bundle: str | None = Query(None),
    concepts: SqlConceptRepository = Depends(get_concept_repo),
) -> Response:
    items = [c for c in concepts.all() if bundle is None or c.bundle == bundle]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for c in items:
            zf.writestr(f"{c.id}.md", _concept_to_markdown(c))
    safe_bundle = "".join(ch for ch in (bundle or "all") if ch.isalnum() or ch in ("-", "_")) or "all"
    filename = f"knowledge-atlas-{safe_bundle}.zip"
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
