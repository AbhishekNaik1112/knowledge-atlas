"""Server-rendered web UI (Jinja + htmx). Browse, view a concept, search, and a graph page."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.db import Concept
from app.dependencies import get_concept_repo, get_edge_repo, get_search_repo, get_sync_repo
from app.embeddings import Embedder, get_embedder
from app.render import render_body_html
from app.repository import (
    SearchHit,
    SqlConceptRepository,
    SqlEdgeRepository,
    SqlSearchRepository,
    SqlSyncEventRepository,
)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
router = APIRouter(tags=["ui"])


@router.get("/ui", response_class=HTMLResponse)
def ui_home(
    request: Request,
    sort: Literal["id", "updated"] = "updated",
    type: str = "",
    tag: str = "",
    folder: str = "",
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    syncs: SqlSyncEventRepository = Depends(get_sync_repo),
) -> HTMLResponse:
    items, _ = concepts.list(
        type=type or None,
        tags=[tag.lower()] if tag else None,
        prefix=folder or None,
        sort=sort,
        limit=200,
    )
    types, tags, folders = concepts.distinct_facets()
    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={
            "concepts": items,
            "types": types,
            "tags": tags,
            "folders": folders,
            "selected_sort": sort,
            "selected_type": type,
            "selected_tag": tag,
            "selected_folder": folder,
            "latest_sync": syncs.latest(),
        },
    )


@router.get("/ui/search", response_class=HTMLResponse)
def ui_search(
    request: Request,
    q: str = "",
    type: str = "",
    tag: str = "",
    folder: str = "",
    sort: Literal["id", "updated"] = "updated",
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    search: SqlSearchRepository = Depends(get_search_repo),
    settings: Settings = Depends(get_settings),
    embedder: Embedder = Depends(get_embedder),
) -> HTMLResponse:
    type_f = type or None
    tag_f = [tag.lower()] if tag else None
    prefix_f = folder or None
    rows: list[Concept] | list[SearchHit]
    if q.strip():
        if settings.embeddings_enabled:
            rows, _ = search.hybrid(
                q, embedder.encode([q])[0], type=type_f, tags=tag_f, prefix=prefix_f, limit=50
            )
        else:
            rows, _ = search.search(
                q, type=type_f, tags=tag_f, prefix=prefix_f, limit=50
            )
    else:
        rows, _ = concepts.list(
            type=type_f, tags=tag_f, prefix=prefix_f, sort=sort, limit=200
        )
    return templates.TemplateResponse(
        request=request, name="concept_rows.html", context={"concepts": rows}
    )


@router.get("/ui/activity", response_class=HTMLResponse)
def ui_activity(
    request: Request,
    syncs: SqlSyncEventRepository = Depends(get_sync_repo),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="activity.html",
        context={"events": syncs.list(limit=30)},
    )


@router.get("/ui/graph", response_class=HTMLResponse)
def ui_graph(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="graph.html", context={})


@router.get("/ui/concepts/{concept_id:path}", response_class=HTMLResponse)
def ui_concept(
    request: Request,
    concept_id: str,
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    edges: SqlEdgeRepository = Depends(get_edge_repo),
) -> HTMLResponse:
    obj = concepts.get(concept_id)
    if obj is None:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={"concept_id": concept_id},
            status_code=404,
        )
    return templates.TemplateResponse(
        request=request,
        name="concept.html",
        context={
            "c": obj,
            "html": render_body_html(obj.body, concept_id),
            "outgoing": edges.outgoing(concept_id),
            "backlinks": edges.backlinks(concept_id),
        },
    )
