"""Test Handshake — first-time setup + idempotent repeat."""


def test_first_handshake(client):
    resp = client.post("/api/v1/handshake", json={"user_id": "fresh_user"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["credits"] == 500
    assert data["default_gameplay"] == "structured_reflection"


def test_handshake_creates_credits(client):
    client.post("/api/v1/handshake", json={"user_id": "hs_user"})
    resp = client.get("/api/v1/credits/hs_user/balance")
    assert resp.json()["balance"] == 500


def test_handshake_creates_local_gameplay(client):
    client.post("/api/v1/handshake", json={"user_id": "hs_user2"})
    resp = client.get("/api/v1/gameplays/hs_user2/current")
    assert resp.status_code == 200
    assert resp.json()["gameplay"]["id"] == "structured_reflection"
    assert resp.json()["version"] == 1


def test_handshake_idempotent(client):
    resp1 = client.post("/api/v1/handshake", json={"user_id": "repeat_user"})
    assert resp1.json()["credits"] == 500
    resp2 = client.post("/api/v1/handshake", json={"user_id": "repeat_user"})
    assert resp2.json()["credits"] == 500
    resp3 = client.get("/api/v1/credits/repeat_user/balance")
    assert resp3.json()["balance"] == 500


def test_handshake_idempotent_local(client):
    client.post("/api/v1/handshake", json={"user_id": "repeat_user2"})
    client.post("/api/v1/handshake", json={"user_id": "repeat_user2"})
    resp = client.get("/api/v1/gameplays/repeat_user2/current")
    assert resp.json()["version"] == 1
