from __future__ import annotations

import json
from fastapi.testclient import TestClient
from app.main import create_app


def test_conversation_crud_and_messages_listing():
    app = create_app()
    client = TestClient(app)

    # Create conversation
    r = client.post("/api/conversations", json={"title": "t1"})
    assert r.status_code == 200
    conv = r.json()
    conv_id = conv["id"]

    # Send chat message associated to conversation
    r = client.post("/api/chat", json={"message": "hello", "conversation_id": conv_id})
    assert r.status_code == 200

    # List messages
    r = client.get(f"/api/conversations/{conv_id}/messages")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) >= 1


def test_search_and_raw():
    app = create_app()
    client = TestClient(app)

    # Create chat and then search
    r = client.post("/api/chat", json={"message": "searchable phrase"})
    assert r.status_code == 200

    r = client.get("/api/search/messages", params={"q": "searchable"})
    assert r.status_code == 200
    results = r.json()
    assert isinstance(results, list)
    if results:
        mid = results[0]["id"]
        rr = client.get(f"/api/messages/{mid}/raw")
        assert rr.status_code == 200

