"""Test Gameplays — CRUD + loop field + pull + contribute."""


def test_list_gameplays(client):
    resp = client.get("/api/v1/gameplays")
    assert resp.status_code == 200
    gps = resp.json()["gameplays"]
    assert len(gps) == 6
    ids = [g["id"] for g in gps]
    assert "structured_reflection" in ids
    assert "belief_interrogation" in ids
    assert "intuition_challenge_30d" in ids
    assert "couple_alignment" in ids
    assert "agent_genesis" in ids
    assert "mbti_alignment" in ids


def test_gameplay_has_consciousness_architecture(client):
    resp = client.get("/api/v1/gameplays/structured_reflection")
    assert resp.status_code == 200
    gp = resp.json()
    assert "consciousness_architecture" in gp
    assert "dimensions" in gp["consciousness_architecture"]
    assert "purpose" in gp["consciousness_architecture"]["dimensions"]
    assert gp["loop"]["cadence"] == "session"
    assert gp["loop"]["phases"][0]["id"] == "user_input"
    assert gp["interfaces"]["user_input"]["type"] == "five_dimension_capture"
    assert gp["interfaces"]["agent_alignment"]["type"] == "five_dimension_alignment_board"
    assert gp["interfaces"]["evaluation"]["type"] == "alignment_metric_test_panel"
    assert gp["interfaces"]["experience"]["type"] == "dimension_experience_switcher"


def test_gameplay_has_loop_and_markdown(client):
    resp = client.get("/api/v1/gameplays/belief_interrogation")
    assert resp.status_code == 200
    gp = resp.json()
    assert "loop" in gp
    assert gp["loop"]["cadence"] == "session"
    assert gp["loop"]["phases"][0]["id"] == "claim"
    assert "markdown" in gp
    assert "# 信念拷问" in gp["markdown"]
    assert gp["required_tools"] == []


def test_gameplay_architecture_can_be_optional(client):
    resp = client.get("/api/v1/gameplays/intuition_challenge_30d")
    assert resp.status_code == 200
    gp = resp.json()
    assert gp["consciousness_architecture"] is None


def test_get_not_found(client):
    resp = client.get("/api/v1/gameplays/nonexistent")
    assert resp.status_code == 404


def test_recommend_default(client):
    resp = client.post("/api/v1/gameplays/recommend", json={"query": ""})
    assert resp.status_code == 200
    assert resp.json()["recommended"]["id"] == "structured_reflection"


def test_recommend_keyword(client):
    resp = client.post("/api/v1/gameplays/recommend", json={"query": "challenging psychological"})
    assert resp.status_code == 200
    assert resp.json()["recommended"]["id"] == "belief_interrogation"


def test_contribute(user_with_credits, client):
    resp = client.post("/api/v1/gameplays/contribute", json={
        "user_id": user_with_credits,
        "gameplay": {
            "id": "gp_custom",
            "name": "Custom Game",
            "summary": "A custom loop-first gameplay",
            "consciousness_architecture": {"dimensions": ["a", "b"]},
            "loop": {
                "cadence": "session",
                "participants": "solo",
                "phases": [{"id": "check_in", "name": "Check In", "goal": "start"}],
            },
            "markdown": "# Custom Game\n\nA custom loop.\n",
        },
    })
    assert resp.status_code == 200
    assert resp.json()["credit_earned"] == 10

    resp2 = client.get("/api/v1/credits/test_user/balance")
    assert resp2.json()["balance"] == 510


def test_contribute_markdown_draft(user_with_credits, client):
    markdown = """---
{
  "id": "gp_markdown",
  "name": "Markdown Game",
  "summary": "A draft published from markdown",
  "loop": {
    "cadence": "session",
    "participants": "solo",
    "phases": [{"id": "play", "name": "Play", "goal": "run"}]
  },
  "interfaces": {
    "capture": {"type": "text_capture"}
  },
  "required_tools": ["image.generate"],
  "tags": ["fun"],
  "created_at": "2026-03-08T00:00:00Z"
}
---

# Markdown Game

Publish me from markdown.
"""
    resp = client.post("/api/v1/gameplays/contribute", json={"user_id": user_with_credits, "markdown": markdown})
    assert resp.status_code == 200

    stored = client.get("/api/v1/gameplays/gp_markdown")
    assert stored.status_code == 200
    assert stored.json()["required_tools"] == ["image.generate"]


def test_pull(user_with_credits, client):
    resp = client.post("/api/v1/gameplays/pull", json={
        "user_id": user_with_credits, "gameplay_id": "belief_interrogation",
    })
    assert resp.status_code == 200
    # Handshake pulled structured_reflection as v1, this is v2
    assert resp.json()["version"] == 2

    resp2 = client.get(f"/api/v1/gameplays/{user_with_credits}/current")
    assert resp2.status_code == 200
    assert resp2.json()["gameplay"]["id"] == "belief_interrogation"


def test_pull_not_found(user_with_credits, client):
    resp = client.post("/api/v1/gameplays/pull", json={
        "user_id": user_with_credits, "gameplay_id": "nonexistent",
    })
    assert resp.status_code == 404


def test_history(user_with_credits, client):
    resp = client.get(f"/api/v1/gameplays/{user_with_credits}/history")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1


def test_iterate_local_gameplay(user_with_credits, client):
    resp = client.post(f"/api/v1/gameplays/{user_with_credits}/iterate", json={
        "updates": {
            "loop": {
                "cadence": "session",
                "phases": [
                    {"id": "mirror", "name": "Mirror", "goal": "reflect directly"},
                    {"id": "score", "name": "Score", "goal": "measure the round"},
                ],
            },
            "tags": ["customized", "deep"],
        },
        "note": "Tune the local gameplay for a more direct style",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["previous_version"] == 1
    assert data["version"] == 2
    assert data["gameplay"]["loop"]["cadence"] == "session"
    assert data["gameplay"]["loop"]["phases"][0]["id"] == "mirror"

    current = client.get(f"/api/v1/gameplays/{user_with_credits}/current")
    assert current.status_code == 200
    assert current.json()["version"] == 2
    assert current.json()["change_note"] == "Tune the local gameplay for a more direct style"
