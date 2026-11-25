"""Search endpoint — keyword (ts_rank_cd), semantic (pgvector cosine), or hybrid (RRF)."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import Settings, get_settings
from app.dependencies import get_search_repo
from app.embeddings import Embedder, get_embedder
from app.models import Page, SearchHitOut
from app.repository import SqlSearchRepository
from app.security import require_private_access

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/search",
    tags=["search"],
    dependencies=[Depends(require_private_access)],
)


@router.get("", response_model=Page[SearchHitOut])
def search(
    q: str = Query(min_length=1),
    mode: Literal["keyword", "semantic", "hybrid"] = "keyword",
    type: str | None = Query(None),
    tags: list[str] = Query(default=[]),
    bundle: str | None = Query(None),
    limit: int | None = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    repo: SqlSearchRepository = Depends(get_search_repo),
    embedder: Embedder = Depends(get_embedder),
    settings: Settings = Depends(get_settings),
) -> Page[SearchHitOut]:
    effective_limit = settings.default_page_size if limit is None else limit
    if effective_limit > settings.max_page_size:
        raise HTTPException(
            status_code=422, detail=f"limit must be <= {settings.max_page_size}"
        )
    tag_filter = [t.strip().lower() for t in tags if t.strip()] or None

    if mode == "keyword":
        hits, total = repo.search(
            q, type=type, tags=tag_filter, bundle=bundle, limit=effective_limit, offset=offset
        )
    else:
        if not settings.embeddings_enabled:
            raise HTTPException(status_code=400, detail="semantic search is disabled")
        try:
            query_vec = embedder.encode([q])[0]
        except Exception:
            if mode == "hybrid":
                logger.warning("Hybrid query embedding failed; falling back to keyword search")
                hits, total = repo.search(
                    q, type=type, tags=tag_filter, bundle=bundle, limit=effective_limit, offset=offset
                )
            else:
                raise HTTPException(status_code=503, detail="semantic search temporarily unavailable")
        else:
            if mode == "semantic":
                hits, total = repo.semantic(
                    query_vec,
                    type=type,
                    tags=tag_filter,
                    bundle=bundle,
                    limit=effective_limit,
                    offset=offset,
                )
            else:  # hybrid
                hits, total = repo.hybrid(
                    q,
                    query_vec,
                    type=type,
                    tags=tag_filter,
                    bundle=bundle,
                    limit=effective_limit,
                    offset=offset,
                )

    return Page(
        items=[SearchHitOut.model_validate(h) for h in hits],
        total=total,
        limit=effective_limit,
        offset=offset,
    )
