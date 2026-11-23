"""M16 — web UI pages render concepts, markdown, links, and search."""


def _create(client, id, **over):
    body = {"id": id, "type": "Doc"}
    body.update(over)
    return client.post("/concepts", json=body)


def test_ui_home_lists_concepts(client):
    _create(client, "a", title="Alpha")
    r = client.get("/ui")
    assert r.status_code == 200 and "Alpha" in r.text


def test_ui_concept_renders_markdown(client):
    _create(client, "a", title="Alpha", body="# Heading")
    r = client.get("/ui/concepts/a")
    assert r.status_code == 200 and "<h1>Heading</h1>" in r.text


def test_ui_concept_shows_outgoing_link(client):
    _create(client, "b")
    _create(client, "a", body="see [B](b.md)")
    r = client.get("/ui/concepts/a")
    assert "/ui/concepts/b" in r.text


def test_ui_search_partial_filters(db_session):
    from fastapi.testclient import TestClient
    from app.config import Settings, get_settings
    from app.db import get_session
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(embeddings_enabled=False)
    with TestClient(app) as c:
        _create(c, "a", title="Bitcoin", body="ledger")
        _create(c, "b", title="Banana", body="fruit")
        r = c.get("/ui/search", params={"q": "bitcoin"})
        assert r.status_code == 200 and "Bitcoin" in r.text and "Banana" not in r.text
    app.dependency_overrides.clear()


def test_ui_search_uses_hybrid_when_embeddings_enabled(db_session):
    from fastapi.testclient import TestClient
    from app.config import Settings, get_settings
    from app.db import get_session
    from app.embeddings import get_embedder
    from app.main import create_app
    from tests.api.test_semantic import FakeEmbedder

    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(embeddings_enabled=True)
    app.dependency_overrides[get_embedder] = FakeEmbedder
    with TestClient(app) as c:
        _create(c, "b", title="Banana", body="banana bread recipe")
        _create(c, "a", title="Fast Vehicle", body="the automobile is fast")
        r = c.get("/ui/search", params={"q": "car"})
        assert r.status_code == 200
        assert "Fast Vehicle" in r.text
        assert r.text.index("Fast Vehicle") < r.text.index("Banana")
    app.dependency_overrides.clear()


def test_ui_missing_concept_404(client):
    r = client.get("/ui/concepts/ghost")
    assert r.status_code == 404
    assert "text/html" in r.headers["content-type"]


def test_ui_graph_page_loads_cytoscape(client):
    r = client.get("/ui/graph")
    assert r.status_code == 200 and "cytoscape" in r.text.lower()


def test_root_redirects_to_ui(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/ui"


def test_ui_body_links_rewritten_to_ui_routes(client):
    client.post("/concepts", json={"id": "tables/blocks", "type": "Doc"})
    client.post(
        "/concepts",
        json={"id": "datasets/x", "type": "Doc", "body": "see [blocks](../tables/blocks.md)"},
    )
    r = client.get("/ui/concepts/datasets/x")
    assert "/ui/concepts/tables/blocks" in r.text
    assert "../tables/blocks.md" not in r.text  # raw .md link rewritten


def test_ui_body_external_links_preserved(client):
    client.post("/concepts", json={"id": "a", "type": "Doc", "body": "[docs](https://example.com)"})
    r = client.get("/ui/concepts/a")
    assert "https://example.com" in r.text
