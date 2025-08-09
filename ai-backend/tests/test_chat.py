from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.main import create_app


def test_chat_requires_api_key_when_configured(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    app = create_app()
    client = TestClient(app)
    resp = client.post("/api/chat", json={"message": "hi"})
    assert resp.status_code == 401
