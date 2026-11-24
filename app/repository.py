"""Data-access layer. Routers and services depend on these repositories, never on SQL directly,
so a different backend (e.g. Postgres->another store) can be swapped behind the same surface.
"""

from __future__ import annotations

import builtins
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.orm import Session

from app.db import Concept, Edge, SyncEvent
from app.errors import ConflictError, NotFoundError
from app.parser import ParsedConcept


@dataclass
class ConceptInput:
    """Everything needed to persist one concept (maps 1:1 to the concepts table)."""

    id: str
    type: str
    bundle: str = "default"
    title: str | None = None
    description: str | None = None
    resource: str | None = None
    timestamp: datetime | None = None
    tags: list[str] = field(default_factory=list)
    body: str = ""
    frontmatter: dict = field(default_factory=dict)

    @classmethod
    def from_parsed(cls, parsed: ParsedConcept) -> "ConceptInput":
        return cls(
            id=parsed.id,
            type=parsed.type,
            bundle=parsed.bundle,
            title=parsed.title,
            description=parsed.description,
            resource=parsed.resource,
            timestamp=parsed.timestamp,
            tags=list(parsed.tags),
            body=parsed.body,
            frontmatter=dict(parsed.extra),
        )


class SqlConceptRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def get(self, concept_id: str) -> Concept | None:
        return self.s.get(Concept, concept_id)

    def all(self) -> list[Concept]:
        return list(self.s.execute(select(Concept).order_by(Concept.id)).scalars())

    def upsert(self, data: ConceptInput) -> Concept:
        obj = self.s.get(Concept, data.id)
        if obj is None:
            obj = Concept(id=data.id)
            self.s.add(obj)
        self._apply(obj, data)
        self.s.flush()
        return obj

    def create(self, data: ConceptInput) -> Concept:
        if self.s.get(Concept, data.id) is not None:
            raise ConflictError(f"concept {data.id!r} already exists")
        obj = Concept(id=data.id)
        self.s.add(obj)
        self._apply(obj, data)
        self.s.flush()
        return obj

    def update(self, concept_id: str, data: ConceptInput) -> Concept:
        obj = self.s.get(Concept, concept_id)
        if obj is None:
            raise NotFoundError(f"concept {concept_id!r} not found")
        self._apply(obj, data)
        self.s.flush()
        return obj

    def delete(self, concept_id: str) -> None:
        obj = self.s.get(Concept, concept_id)
        if obj is None:
            raise NotFoundError(f"concept {concept_id!r} not found")
        self.s.delete(obj)
        self.s.flush()

    def delete_missing_in_bundle(self, bundle: str, keep_ids: set[str]) -> builtins.list[str]:
        """Delete concepts in `bundle` absent from `keep_ids`. Returns deleted concept IDs."""
        stmt = select(Concept.id).where(Concept.bundle == bundle)
        if keep_ids:
            stmt = stmt.where(Concept.id.notin_(keep_ids))
        missing_ids = builtins.list(self.s.execute(stmt).scalars())
        if missing_ids:
            self.s.execute(delete(Concept).where(Concept.id.in_(missing_ids)))
            self.s.flush()
        return missing_ids

    def distinct_facets(
        self,
    ) -> tuple[builtins.list[str], builtins.list[str], builtins.list[str]]:
        """Return sorted distinct (types, tags, top-level folders) across all concepts."""
        rows = self.s.execute(select(Concept.id, Concept.type, Concept.tags)).all()
        types: set[str] = set()
        tags: set[str] = set()
        folders: set[str] = set()
        for cid, ctype, ctags in rows:
            if ctype:
                types.add(ctype)
            if ctags:
                tags.update(ctags)
            if "/" in cid:
                folders.add(cid.split("/", 1)[0])
        return sorted(types), sorted(tags), sorted(folders)

    def distinct_bundles(self) -> builtins.list[str]:
        rows = self.s.execute(select(Concept.bundle).distinct().order_by(Concept.bundle)).scalars()
        return builtins.list(rows)

    def list(
        self,
        *,
        type: str | None = None,
        tags: builtins.list[str] | None = None,
        bundle: str | None = None,
        prefix: str | None = None,
        sort: Literal["id", "updated"] = "id",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[builtins.list[Concept], int]:
        conditions = []
        if type:
            conditions.append(Concept.type == type)
        if tags:
            conditions.append(Concept.tags.contains(tags))  # array @> => AND semantics
        if bundle:
            conditions.append(Concept.bundle == bundle)
        if prefix:
            clean = prefix.strip("/")
            conditions.append(Concept.id.startswith(f"{clean}/"))

        count_stmt = select(func.count()).select_from(Concept)
        list_stmt = select(Concept)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            list_stmt = list_stmt.where(*conditions)

        total = self.s.execute(count_stmt).scalar_one()
        order = (
            (Concept.updated_at.desc(), Concept.id)
            if sort == "updated"
            else (Concept.id,)
        )
        list_stmt = list_stmt.order_by(*order).limit(limit).offset(offset)
        items = builtins.list(self.s.execute(list_stmt).scalars())
        return items, total

    def set_embedding(self, concept_id: str, vector: builtins.list[float]) -> None:
        obj = self.s.get(Concept, concept_id)
        if obj is not None:
            obj.embedding = vector
            self.s.flush()

    @staticmethod
    def _apply(obj: Concept, d: ConceptInput) -> None:
        obj.type = d.type
        obj.bundle = d.bundle
        obj.title = d.title
        obj.description = d.description
        obj.resource = d.resource
        obj.timestamp = d.timestamp
        obj.tags = list(d.tags)
        obj.body = d.body
        obj.frontmatter = dict(d.frontmatter)


@dataclass
class EdgeInput:
    target_id: str
    anchor_text: str | None = None
    rel_type: str = "link"
    resolved: bool = True


class SqlEdgeRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def replace_for_source(self, source_id: str, edges: list[EdgeInput]) -> None:
        """Replace all edges originating from source_id (idempotent full rewrite)."""
        self.s.execute(delete(Edge).where(Edge.source_id == source_id))
        seen: set[tuple[str, str]] = set()
        for e in edges:
            key = (e.target_id, e.rel_type)
            if key in seen:
                continue
            seen.add(key)
            self.s.add(
                Edge(
                    source_id=source_id,
                    target_id=e.target_id,
                    rel_type=e.rel_type,
                    anchor_text=e.anchor_text,
                    resolved=e.resolved,
                )
            )
        self.s.flush()

    def mark_resolved_for_target(self, target_id: str, resolved: bool) -> None:
        """Update `resolved` on all incoming edges pointing to target_id."""
        self.s.execute(update(Edge).where(Edge.target_id == target_id).values(resolved=resolved))
        self.s.flush()

    def outgoing(self, source_id: str) -> list[Edge]:
        stmt = select(Edge).where(Edge.source_id == source_id).order_by(Edge.target_id)
        return list(self.s.execute(stmt).scalars())

    def backlinks(self, target_id: str) -> list[Edge]:
        stmt = select(Edge).where(Edge.target_id == target_id).order_by(Edge.source_id)
        return list(self.s.execute(stmt).scalars())

    def all(self) -> list[Edge]:
        return list(self.s.execute(select(Edge)).scalars())


@dataclass
class SearchHit:
    id: str
    type: str
    title: str | None
    description: str | None
    score: float
    snippet: str | None


_HEADLINE_OPTS = "StartSel=<mark>, StopSel=</mark>, MaxWords=25, MinWords=8, ShortWord=3"


def _excerpt(description: str | None, body: str | None, max_len: int = 160) -> str | None:
    text = (description or body or "").strip()
    if not text:
        return None
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


class SqlSearchRepository:
    """Full-text search over the generated `search_vector` column (ts_rank_cd ranking)."""

    def __init__(self, session: Session) -> None:
        self.s = session

    @staticmethod
    def _extra_filters(
        type: str | None,
        tags: list[str] | None,
        prefix: str | None = None,
        bundle: str | None = None,
    ) -> list:
        conditions = []
        if type:
            conditions.append(Concept.type == type)
        if tags:
            conditions.append(Concept.tags.contains(tags))
        if bundle:
            conditions.append(Concept.bundle == bundle)
        if prefix:
            conditions.append(Concept.id.startswith(f"{prefix.strip('/')}/"))
        return conditions

    def search(
        self,
        q: str,
        *,
        type: str | None = None,
        tags: list[str] | None = None,
        prefix: str | None = None,
        bundle: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SearchHit], int]:
        tsquery = func.websearch_to_tsquery("english", q)
        score = func.ts_rank_cd(Concept.search_vector, tsquery)
        snippet = func.ts_headline("english", Concept.body, tsquery, _HEADLINE_OPTS)

        conditions = [
            Concept.search_vector.bool_op("@@")(tsquery),
            *self._extra_filters(type, tags, prefix, bundle),
        ]
        where = and_(*conditions)

        total = self.s.execute(
            select(func.count()).select_from(Concept).where(where)
        ).scalar_one()

        rows = self.s.execute(
            select(
                Concept.id,
                Concept.type,
                Concept.title,
                Concept.description,
                score.label("score"),
                snippet.label("snippet"),
            )
            .where(where)
            .order_by(score.desc(), Concept.id)
            .limit(limit)
            .offset(offset)
        ).all()

        hits = [
            SearchHit(
                id=r.id,
                type=r.type,
                title=r.title,
                description=r.description,
                score=float(r.score),
                snippet=r.snippet,
            )
            for r in rows
        ]
        return hits, total

    def semantic(
        self,
        query_vec: list[float],
        *,
        type: str | None = None,
        tags: list[str] | None = None,
        prefix: str | None = None,
        bundle: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SearchHit], int]:
        where = and_(
            Concept.embedding.isnot(None), *self._extra_filters(type, tags, prefix, bundle)
        )
        distance = Concept.embedding.cosine_distance(query_vec)
        total = self.s.execute(
            select(func.count()).select_from(Concept).where(where)
        ).scalar_one()
        rows = self.s.execute(
            select(
                Concept.id,
                Concept.type,
                Concept.title,
                Concept.description,
                Concept.body,
                distance.label("distance"),
            )
            .where(where)
            .order_by(distance)
            .limit(limit)
            .offset(offset)
        ).all()
        hits = [
            SearchHit(
                id=r.id,
                type=r.type,
                title=r.title,
                description=r.description,
                score=1.0 - float(r.distance),  # cosine similarity
                snippet=_excerpt(r.description, r.body),
            )
            for r in rows
        ]
        return hits, total

    def hybrid(
        self,
        q: str,
        query_vec: list[float],
        *,
        type: str | None = None,
        tags: list[str] | None = None,
        prefix: str | None = None,
        bundle: str | None = None,
        limit: int = 50,
        offset: int = 0,
        k: int = 60,
        pool: int = 100,
    ) -> tuple[list[SearchHit], int]:
        """Reciprocal-rank fusion of keyword (ts_rank_cd) and semantic (cosine) rankings."""
        extra = self._extra_filters(type, tags, prefix, bundle)
        tsquery = func.websearch_to_tsquery("english", q)

        keyword_ids = [
            row[0]
            for row in self.s.execute(
                select(Concept.id)
                .where(and_(Concept.search_vector.bool_op("@@")(tsquery), *extra))
                .order_by(func.ts_rank_cd(Concept.search_vector, tsquery).desc())
                .limit(pool)
            )
        ]
        semantic_ids = [
            row[0]
            for row in self.s.execute(
                select(Concept.id)
                .where(and_(Concept.embedding.isnot(None), *extra))
                .order_by(Concept.embedding.cosine_distance(query_vec))
                .limit(pool)
            )
        ]

        scores: dict[str, float] = {}
        for rank, cid in enumerate(keyword_ids):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
        for rank, cid in enumerate(semantic_ids):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)

        ordered = sorted(scores, key=lambda cid: scores[cid], reverse=True)
        total = len(ordered)
        page = ordered[offset : offset + limit]
        rows = {
            c.id: c
            for c in self.s.execute(select(Concept).where(Concept.id.in_(page))).scalars()
        }
        kw_page_ids = [cid for cid in page if cid in keyword_ids]
        kw_snippets: dict[str, str] = {}
        if kw_page_ids:
            headline_expr = func.ts_headline("english", Concept.body, tsquery, _HEADLINE_OPTS)
            for cid, snip in self.s.execute(
                select(Concept.id, headline_expr).where(Concept.id.in_(kw_page_ids))
            ):
                if snip:
                    kw_snippets[cid] = snip
        hits = [
            SearchHit(
                id=cid,
                type=rows[cid].type,
                title=rows[cid].title,
                description=rows[cid].description,
                score=scores[cid],
                snippet=kw_snippets.get(cid) or _excerpt(rows[cid].description, rows[cid].body),
            )
            for cid in page
            if cid in rows
        ]
        return hits, total


class SqlSyncEventRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def record(
        self,
        *,
        bundle: str,
        source: str = "webhook",
        commit_sha: str | None = None,
        commit_message: str | None = None,
        pusher: str | None = None,
        ref: str | None = None,
        created_count: int = 0,
        updated_count: int = 0,
        deleted_count: int = 0,
        error_count: int = 0,
        status: str = "ok",
        embedded_count: int = 0,
        embed_status: str = "skipped",
    ) -> SyncEvent:
        ev = SyncEvent(
            bundle=bundle,
            source=source,
            commit_sha=commit_sha,
            commit_message=commit_message,
            pusher=pusher,
            ref=ref,
            created_count=created_count,
            updated_count=updated_count,
            deleted_count=deleted_count,
            error_count=error_count,
            status=status,
            embedded_count=embedded_count,
            embed_status=embed_status,
        )
        self.s.add(ev)
        self.s.flush()
        return ev

    def latest(self, bundle: str | None = None) -> SyncEvent | None:
        stmt = select(SyncEvent)
        if bundle:
            stmt = stmt.where(SyncEvent.bundle == bundle)
        stmt = stmt.order_by(SyncEvent.synced_at.desc(), SyncEvent.id.desc()).limit(1)
        return self.s.execute(stmt).scalar_one_or_none()

    def list(self, limit: int = 20) -> builtins.list[SyncEvent]:
        stmt = select(SyncEvent).order_by(SyncEvent.synced_at.desc(), SyncEvent.id.desc()).limit(limit)
        return builtins.list(self.s.execute(stmt).scalars())
