"""M6 — concept CRUD over HTTP: statuses, slash-ids, render, edge sync."""

from app.repository import SqlEdgeRepository


def _payload(**over):
    base = {"id": "a", "type": "Doc", "title": "A", "body": "hello"}
    base.update(over)
    return base


def test_create_201_and_location(client):
    r = client.post("/concepts", json=_payload())
    assert r.status_code == 201
    assert r.headers["location"] == "/concepts/a"
    assert r.json()["id"] == "a"


def test_create_missing_type_422(client):
    r = client.post("/concepts", json={"id": "a", "body": "x"})
    assert r.status_code == 422


def test_create_duplicate_409(client):
    client.post("/concepts", json=_payload())
    r = client.post("/concepts", json=_payload())
    assert r.status_code == 409


def test_create_syncs_edges(client, db_session):
    client.post("/concepts", json=_payload(id="b", body="x"))
    client.post("/concepts", json=_payload(id="a", body="see [B](b.md)"))
    edges = SqlEdgeRepository(db_session).outgoing("a")
    assert [(e.target_id, e.resolved) for e in edges] == [("b", True)]


def test_get_200(client):
    client.post("/concepts", json=_payload())
    r = client.get("/concepts/a")
    assert r.status_code == 200 and r.json()["title"] == "A"


def test_get_concept_with_slash_id(client):
    client.post("/concepts", json=_payload(id="tables/users"))
    r = client.get("/concepts/tables/users")
    assert r.status_code == 200 and r.json()["id"] == "tables/users"


def test_get_missing_404(client):
    assert client.get("/concepts/ghost").status_code == 404


def test_get_render_html(client):
    client.post("/concepts", json=_payload(id="a", body="# Title"))
    r = client.get("/concepts/a", params={"render": "true"})
    assert r.status_code == 200 and "<h1>" in r.json()["html"]


def test_put_updates_200(client):
    client.post("/concepts", json=_payload())
    r = client.put("/concepts/a", json={"type": "Doc", "title": "A2", "body": "y"})
    assert r.status_code == 200 and r.json()["title"] == "A2"


def test_put_missing_404(client):
    r = client.put("/concepts/ghost", json={"type": "Doc", "body": "y"})
    assert r.status_code == 404


def test_delete_204(client):
    client.post("/concepts", json=_payload())
    assert client.delete("/concepts/a").status_code == 204
    assert client.get("/concepts/a").status_code == 404


def test_delete_missing_404(client):
    assert client.delete("/concepts/ghost").status_code == 404


def test_create_and_delete_sync_incoming_edge_resolved(client):
    client.post("/concepts", json={"id": "src", "type": "Doc", "body": "see [tgt](tgt.md)"})
    links1 = client.get("/concepts/src/links").json()
    assert links1["outgoing"][0]["resolved"] is False

    client.post("/concepts", json={"id": "tgt", "type": "Doc", "body": "target"})
    links2 = client.get("/concepts/src/links").json()
    assert links2["outgoing"][0]["resolved"] is True

    client.delete("/concepts/tgt")
    links3 = client.get("/concepts/src/links").json()
    assert links3["outgoing"][0]["resolved"] is False


def test_extra_frontmatter_roundtrip_and_put_preserves(client):
    r = client.post(
        "/concepts",
        json={"id": "fm", "type": "Doc", "extra": {"owner": "alice", "tier": 1}},
    )
    assert r.status_code == 201
    assert r.json()["extra"] == {"owner": "alice", "tier": 1}

    fetched = client.get("/concepts/fm").json()
    assert fetched["extra"] == {"owner": "alice", "tier": 1}

    # PUT without extra preserves existing frontmatter
    upd = client.put("/concepts/fm", json={"type": "Doc", "title": "Updated", "body": "new"})
    assert upd.status_code == 200
    assert upd.json()["extra"] == {"owner": "alice", "tier": 1}
