"""Server-rendered web UI (Jinja + htmx). Browse, view a concept, search, and a graph page."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.db import Concept
from app.dependencies import get_concept_repo, get_edge_repo, get_search_repo
from app.embeddings import Embedder, get_embedder
from app.render import render_body_html
from app.repository import SearchHit, SqlConceptRepository, SqlEdgeRepository, SqlSearchRepository

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
router = APIRouter(tags=["ui"])


@router.get("/ui", response_class=HTMLResponse)
def ui_home(
    request: Request,
    concepts: SqlConceptRepository = Depends(get_concept_repo),
) -> HTMLResponse:
    items, _ = concepts.list(limit=200)
    return templates.TemplateResponse(request=request, name="list.html", context={"concepts": items})


@router.get("/ui/search", response_class=HTMLResponse)
def ui_search(
    request: Request,
    q: str = "",
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    search: SqlSearchRepository = Depends(get_search_repo),
    settings: Settings = Depends(get_settings),
    embedder: Embedder = Depends(get_embedder),
) -> HTMLResponse:
    rows: list[Concept] | list[SearchHit]
    if q.strip():
        if settings.embeddings_enabled:
            rows, _ = search.hybrid(q, embedder.encode([q])[0], limit=50)
        else:
            rows, _ = search.search(q, limit=50)
    else:
        rows, _ = concepts.list(limit=200)
    return templates.TemplateResponse(
        request=request, name="concept_rows.html", context={"concepts": rows}
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
