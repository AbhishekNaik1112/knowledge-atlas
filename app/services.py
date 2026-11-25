"""Application services — orchestrate repositories into a unit of work.

ConceptService owns the write path: persist a concept, re-derive its outgoing edges from the
markdown body, then commit atomically. Reused by the CRUD router, ingest, and MCP.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db import Concept
from app.embeddings import Embedder, build_embed_text, encode_with_task
from app.links import resolved_links
from app.repository import (
    ConceptInput,
    EdgeInput,
    SqlConceptRepository,
    SqlEdgeRepository,
)

logger = logging.getLogger(__name__)


class ConceptService:
    def __init__(
        self,
        concepts: SqlConceptRepository,
        edges: SqlEdgeRepository,
        session: Session,
        embedder: Embedder | None = None,
    ) -> None:
        self.concepts = concepts
        self.edges = edges
        self.session = session
        self.embedder = embedder

    def get(self, concept_id: str) -> Concept | None:
        return self.concepts.get(concept_id)

    def list(self, **kwargs) -> tuple[list[Concept], int]:
        return self.concepts.list(**kwargs)

    def create(self, data: ConceptInput) -> Concept:
        obj = self.concepts.create(data)
        self._sync_edges(obj.id, obj.body)
        self.edges.mark_resolved_for_target(obj.id, True)
        self._sync_embedding(obj)
        self.session.commit()
        return obj

    def update(self, concept_id: str, data: ConceptInput) -> Concept:
        obj = self.concepts.update(concept_id, data)
        self._sync_edges(concept_id, obj.body)
        self._sync_embedding(obj)
        self.session.commit()
        return obj

    def upsert(self, data: ConceptInput) -> Concept:
        if self.concepts.get(data.id) is not None:
            return self.update(data.id, data)
        return self.create(data)

    def delete(self, concept_id: str) -> None:
        self.concepts.delete(concept_id)
        self.edges.mark_resolved_for_target(concept_id, False)
        self.session.commit()

    def _sync_embedding(self, obj: Concept) -> None:
        if self.embedder is None:
            return
        text = build_embed_text(obj.title, obj.description, obj.body)
        if not text:
            return
        try:
            vector = encode_with_task(self.embedder, [text], "RETRIEVAL_DOCUMENT")[0]
            self.concepts.set_embedding(obj.id, list(vector))
        except Exception:
            logger.warning("Embedding failed for concept %s; preserving DB write", obj.id)

    def _sync_edges(self, source_id: str, body: str) -> None:
        links = resolved_links(source_id, body)
        known = self.concepts.existing_ids(target for target, _ in links)
        edges = [
            EdgeInput(
                target_id=target,
                anchor_text=anchor,
                resolved=target in known,
            )
            for target, anchor in links
        ]
        self.edges.replace_for_source(source_id, edges)
