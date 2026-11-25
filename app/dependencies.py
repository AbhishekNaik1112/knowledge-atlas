"""Composition root: wire concrete repositories/services into request handlers.

FastAPI caches `get_session` per request, so every repo/service below shares one session
(one transaction / unit of work per request)."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.embeddings import Embedder, get_embedder
from app.ingest import IngestService
from app.repository import (
    SqlConceptRepository,
    SqlEdgeRepository,
    SqlSearchRepository,
    SqlSyncEventRepository,
)
from app.services import ConceptService
from app.webhook import RepoSyncer


def get_concept_repo(session: Session = Depends(get_session)) -> SqlConceptRepository:
    return SqlConceptRepository(session)


def get_edge_repo(session: Session = Depends(get_session)) -> SqlEdgeRepository:
    return SqlEdgeRepository(session)


def get_search_repo(session: Session = Depends(get_session)) -> SqlSearchRepository:
    return SqlSearchRepository(session)


def get_concept_service(
    session: Session = Depends(get_session),
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    edges: SqlEdgeRepository = Depends(get_edge_repo),
    settings: Settings = Depends(get_settings),
    embedder: Embedder = Depends(get_embedder),
) -> ConceptService:
    return ConceptService(
        concepts, edges, session, embedder=embedder if settings.embeddings_enabled else None
    )


def get_ingest_service(
    session: Session = Depends(get_session),
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    edges: SqlEdgeRepository = Depends(get_edge_repo),
    settings: Settings = Depends(get_settings),
    embedder: Embedder = Depends(get_embedder),
) -> IngestService:
    return IngestService(
        concepts, edges, session, embedder=embedder if settings.embeddings_enabled else None
    )


def get_sync_repo(session: Session = Depends(get_session)) -> SqlSyncEventRepository:
    return SqlSyncEventRepository(session)


def get_repo_syncer(
    settings: Settings = Depends(get_settings),
    embedder: Embedder = Depends(get_embedder),
) -> RepoSyncer:
    return RepoSyncer(
        embedder=embedder if settings.embeddings_enabled else None,
        sync_subdir=settings.github_sync_subdir,
        sync_branch=settings.github_sync_branch,
        github_token=settings.github_token,
        namespace_by_bundle=settings.namespace_by_bundle,
        repos_config=settings.github_repos_config,
        cloud_mode=settings.private_mode,
    )
