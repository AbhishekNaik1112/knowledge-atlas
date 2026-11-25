"""Hosted Streamable HTTP MCP endpoint (`/mcp`) for Antigravity Second Brain integration."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from app.config import Settings, get_settings
from app.dependencies import (
    get_concept_repo,
    get_concept_service,
    get_edge_repo,
    get_search_repo,
    get_sync_repo,
)
from app.embeddings import Embedder, encode_with_task, get_embedder
from app.models import ConceptOut, SearchHitOut, SyncEventOut
from app.repository import (
    ConceptInput,
    SqlConceptRepository,
    SqlEdgeRepository,
    SqlSearchRepository,
    SqlSyncEventRepository,
)
from app.security import require_api_key
from app.services import ConceptService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp"], dependencies=[Depends(require_api_key)])

_MCP_PROTOCOL_VERSION = "2025-03-26"
_SERVER_INFO = {"name": "knowledge-atlas", "version": "0.1.0"}


class _SearchArgs(BaseModel):
    query: str = Field(min_length=1)
    mode: str = "hybrid"
    bundle: str | None = None
    type: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class _GetConceptArgs(BaseModel):
    id: str = Field(min_length=1)


class _GetGraphArgs(BaseModel):
    bundle: str | None = None
    limit: int = Field(default=500, ge=1, le=500)


class _UpsertConceptArgs(BaseModel):
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    title: str | None = None
    description: str | None = None
    body: str = ""
    tags: list[str] = Field(default_factory=list)
    bundle: str = "mcp"


class _ListSyncArgs(BaseModel):
    limit: int = Field(default=20, ge=1, le=50)


_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_concepts",
        "description": "Search existing concepts in Knowledge Atlas before creating or updating notes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text."},
                "mode": {
                    "type": "string",
                    "enum": ["keyword", "semantic", "hybrid"],
                    "default": "hybrid",
                },
                "bundle": {"type": "string"},
                "type": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_concept",
        "description": "Read a concept's full metadata, markdown body, and incoming/outgoing links.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Concept ID (bundle path)."}},
            "required": ["id"],
        },
    },
    {
        "name": "get_graph",
        "description": "List concept nodes and resolved cross-link edges for graph inspection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bundle": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 500},
            },
        },
    },
    {
        "name": "upsert_concept",
        "description": "Create or update an atomic OKF concept note and re-resolve its cross-links.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "body": {"type": "string", "default": ""},
                "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                "bundle": {"type": "string", "default": "mcp"},
            },
            "required": ["id", "type"],
        },
    },
    {
        "name": "list_sync_activity",
        "description": "List recent GitHub sync events along with embedding status and details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20}
            },
        },
    },
]


def _rpc_ok(req_id: Any, result: Any) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})


def _rpc_err(req_id: Any, code: int, message: str) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def _tool_result(data: Any, *, is_error: bool = False) -> dict[str, Any]:
    text = data if isinstance(data, str) else json.dumps(data, default=str)
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _run_search(
    args: _SearchArgs,
    search_repo: SqlSearchRepository,
    embedder: Embedder,
    settings: Settings,
) -> dict[str, Any]:
    if args.mode in ("semantic", "hybrid") and settings.embeddings_enabled:
        try:
            vec = encode_with_task(embedder, [args.query], "RETRIEVAL_QUERY")[0]
            if args.mode == "semantic":
                hits, total = search_repo.semantic(
                    vec,
                    type=args.type,
                    bundle=args.bundle,
                    limit=args.limit,
                    min_score=settings.semantic_min_score,
                )
            else:
                hits, total = search_repo.hybrid(
                    args.query,
                    vec,
                    type=args.type,
                    bundle=args.bundle,
                    limit=args.limit,
                    min_score=settings.semantic_min_score,
                )
            return _tool_result(
                {
                    "total": total,
                    "mode_used": args.mode,
                    "items": [SearchHitOut.model_validate(h).model_dump(mode="json") for h in hits],
                }
            )
        except Exception:
            if args.mode == "semantic":
                return _tool_result("semantic search temporarily unavailable", is_error=True)
            logger.warning("MCP hybrid embedding failed; falling back to keyword search")

    hits, total = search_repo.search(
        args.query, type=args.type, bundle=args.bundle, limit=args.limit
    )
    return _tool_result(
        {
            "total": total,
            "mode_used": "keyword",
            "items": [SearchHitOut.model_validate(h).model_dump(mode="json") for h in hits],
        }
    )


@router.post("/mcp")
async def mcp_endpoint(
    request: Request,
    svc: ConceptService = Depends(get_concept_service),
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    edges: SqlEdgeRepository = Depends(get_edge_repo),
    search_repo: SqlSearchRepository = Depends(get_search_repo),
    syncs: SqlSyncEventRepository = Depends(get_sync_repo),
    embedder: Embedder = Depends(get_embedder),
    settings: Settings = Depends(get_settings),
) -> Response:
    try:
        body = await request.json()
    except Exception:
        return _rpc_err(None, -32700, "Parse error")

    if not isinstance(body, dict) or not isinstance(body.get("method"), str):
        return _rpc_err(body.get("id") if isinstance(body, dict) else None, -32600, "Invalid Request")

    method: str = body["method"]
    params: dict[str, Any] = body.get("params") or {}
    if "id" not in body or method.startswith("notifications/"):
        return Response(status_code=202)
    req_id = body["id"]

    if method == "initialize":
        return _rpc_ok(
            req_id,
            {
                "protocolVersion": _MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": _SERVER_INFO,
            },
        )
    if method == "ping":
        return _rpc_ok(req_id, {})
    if method == "tools/list":
        return _rpc_ok(req_id, {"tools": _TOOL_DEFINITIONS})
    if method != "tools/call":
        return _rpc_err(req_id, -32601, f"Method not found: {method}")

    tool_name = params.get("name")
    raw_args = params.get("arguments") or {}
    if not isinstance(tool_name, str) or not isinstance(raw_args, dict):
        return _rpc_err(req_id, -32602, "Invalid params")

    try:
        if tool_name == "search_concepts":
            return _rpc_ok(
                req_id, _run_search(_SearchArgs(**raw_args), search_repo, embedder, settings)
            )
        if tool_name == "get_concept":
            g_args = _GetConceptArgs(**raw_args)
            obj = svc.get(g_args.id)
            if obj is None:
                return _rpc_ok(req_id, _tool_result(f"concept {g_args.id!r} not found", is_error=True))
            out = ConceptOut.model_validate(obj).model_dump(mode="json")
            out["outgoing"] = [
                {
                    "target_id": e.target_id,
                    "anchor_text": e.anchor_text,
                    "resolved": e.resolved,
                }
                for e in edges.outgoing(g_args.id)
            ]
            out["incoming"] = [
                {
                    "source_id": e.source_id,
                    "anchor_text": e.anchor_text,
                    "resolved": e.resolved,
                }
                for e in edges.backlinks(g_args.id)
            ]
            return _rpc_ok(req_id, _tool_result(out))
        if tool_name == "get_graph":
            gr_args = _GetGraphArgs(**raw_args)
            items, _ = concepts.list(bundle=gr_args.bundle, limit=gr_args.limit, sort="id")
            node_ids = {n.id for n in items}
            return _rpc_ok(
                req_id,
                _tool_result(
                    {
                        "nodes": [{"id": n.id, "type": n.type, "title": n.title} for n in items],
                        "edges": [
                            {"source": e.source_id, "target": e.target_id, "resolved": e.resolved}
                            for e in edges.all()
                            if e.source_id in node_ids and e.target_id in node_ids
                        ],
                    }
                ),
            )
        if tool_name == "upsert_concept":
            u_args = _UpsertConceptArgs(**raw_args)
            obj = svc.upsert(
                ConceptInput(
                    id=u_args.id,
                    type=u_args.type,
                    bundle=u_args.bundle,
                    title=u_args.title,
                    description=u_args.description,
                    tags=u_args.tags,
                    body=u_args.body,
                )
            )
            return _rpc_ok(req_id, _tool_result(ConceptOut.model_validate(obj).model_dump(mode="json")))
        if tool_name == "list_sync_activity":
            s_args = _ListSyncArgs(**raw_args)
            events = [
                SyncEventOut.model_validate(e).model_dump(mode="json")
                for e in syncs.list(limit=s_args.limit)
            ]
            return _rpc_ok(req_id, _tool_result(events))
    except ValidationError as exc:
        return _rpc_err(req_id, -32602, f"Invalid tool arguments: {exc}")

    return _rpc_err(req_id, -32601, f"Unknown tool: {tool_name}")
