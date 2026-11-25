"""TDD tests for hosted Streamable HTTP /mcp endpoint (Phase 3)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import SyncEvent, get_session
from app.main import create_app


@pytest.fixture
def mcp_client(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        private_mode=True,
        api_key="mcp-secret",
        embeddings_enabled=False,
    )
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _rpc(client: TestClient, method: str, params: dict | None = None, req_id: int | None = 1):
    payload: dict = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        payload["params"] = params
    if req_id is not None:
        payload["id"] = req_id
    return client.post("/mcp", json=payload, headers={"Authorization": "Bearer mcp-secret"})


def test_mcp_requires_auth_in_private_mode(mcp_client):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
    assert mcp_client.post("/mcp", json=payload).status_code == 401
    assert (
        mcp_client.post(
            "/mcp", json=payload, headers={"Authorization": "Bearer wrong"}
        ).status_code
        == 403
    )


def test_mcp_initialize_ping_and_tools_list(mcp_client):
    init_r = _rpc(mcp_client, "initialize", {"protocolVersion": "2025-03-26"})
    assert init_r.status_code == 200
    init_body = init_r.json()["result"]
    assert init_body["serverInfo"]["name"] == "knowledge-atlas"
    assert "tools" in init_body["capabilities"]

    notif_r = _rpc(mcp_client, "notifications/initialized", req_id=None)
    assert notif_r.status_code == 202

    ping_r = _rpc(mcp_client, "ping", req_id=2)
    assert ping_r.status_code == 200
    assert ping_r.json()["result"] == {}

    tools_r = _rpc(mcp_client, "tools/list", req_id=3)
    assert tools_r.status_code == 200
    names = {t["name"] for t in tools_r.json()["result"]["tools"]}
    assert names == {
        "search_concepts",
        "get_concept",
        "get_graph",
        "upsert_concept",
        "list_sync_activity",
    }

    unknown_r = _rpc(mcp_client, "unknown/method", req_id=4)
    assert unknown_r.status_code == 200
    assert unknown_r.json()["error"]["code"] == -32601


def test_mcp_second_brain_workflow_end_to_end(mcp_client, db_session):
    def call_tool(name: str, arguments: dict, req_id: int = 10) -> dict:
        r = _rpc(mcp_client, "tools/call", {"name": name, "arguments": arguments}, req_id=req_id)
        assert r.status_code == 200
        return r.json()["result"]

    r1 = call_tool(
        "upsert_concept",
        {"id": "notes/target", "type": "Doc", "title": "Target", "body": "Target note"},
    )
    assert not r1.get("isError")

    r2 = call_tool(
        "upsert_concept",
        {
            "id": "notes/source",
            "type": "Doc",
            "title": "Source",
            "body": "see [target](target.md)",
        },
    )
    assert not r2.get("isError")

    # Upsert again -> updates without 409 conflict
    r3 = call_tool(
        "upsert_concept",
        {
            "id": "notes/source",
            "type": "Doc",
            "title": "Source Updated",
            "body": "see [target](target.md)",
        },
    )
    assert not r3.get("isError")

    got = call_tool("get_concept", {"id": "notes/source"})
    assert not got.get("isError")
    got_data = json.loads(got["content"][0]["text"])
    assert got_data["title"] == "Source Updated"
    assert got_data["outgoing"][0]["target_id"] == "notes/target"
    assert got_data["outgoing"][0]["resolved"] is True

    missing = call_tool("get_concept", {"id": "missing/id"})
    assert missing.get("isError") is True

    searched = call_tool("search_concepts", {"query": "Target", "mode": "hybrid"})
    assert not searched.get("isError")
    search_data = json.loads(searched["content"][0]["text"])
    assert any(item["id"] == "notes/target" for item in search_data["items"])

    graph_res = call_tool("get_graph", {})
    graph_data = json.loads(graph_res["content"][0]["text"])
    node_ids = {n["id"] for n in graph_data["nodes"]}
    assert {"notes/target", "notes/source"} <= node_ids
    assert any(
        e["source"] == "notes/source" and e["target"] == "notes/target"
        for e in graph_data["edges"]
    )

    db_session.add(SyncEvent(bundle="repo", status="ok", embed_status="ok", embedded_count=2))
    db_session.flush()
    activity = call_tool("list_sync_activity", {"limit": 5})
    activity_data = json.loads(activity["content"][0]["text"])
    assert activity_data[0]["embed_status"] == "ok"
