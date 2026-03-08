"""Test Visualization — DNA + Evolution curve."""
import app.local_db as local_db_mod


def test_dna_empty(client):
    resp = client.get("/api/v1/viz/nobody/dna")
    assert resp.status_code == 200
    data = resp.json()
    assert data["human_dna"] == {}
    assert data["ai_dna"] == {}


def test_dna_with_data(user_with_credits, client):
    uid = user_with_credits
    # Insert snapshot
    local_db_mod.insert_snapshot(uid, "2026-03-06", "structured_reflection",
                                 {"purpose": 0.7, "direction": 0.5, "constraints": 0.6})
    # Insert AI self-model
    local_db_mod.insert_ai_self_model(uid, {"E_I": 0.6}, {"honesty": 0.9}, "analytical", ["over-optimism"])
    # Insert score
    client.post(f"/api/v1/scoring/{uid}/evaluate", json={
        "gameplay_id": "structured_reflection",
        "scores": {
            "understanding_depth": 40,
            "prediction_accuracy": 50,
            "value_resonance": 60,
            "correction_integration": 30,
            "context_consistency": 40,
            "unexpressed_signal_capture": 20,
            "actionability": 30,
        },
    })
    # Insert accuracy
    local_db_mod.insert_ai_self_accuracy(uid, "empathy", 0.8, 0.5)

    resp = client.get(f"/api/v1/viz/{uid}/dna")
    assert resp.status_code == 200
    data = resp.json()
    assert data["human_dna"]["dimensions"]["purpose"] == 0.7
    assert data["ai_dna"]["personality"]["E_I"] == 0.6
    assert data["alignment"]["stage"] == "L2"
    assert len(data["accuracy_gaps"]) == 1
    import pytest
    assert data["accuracy_gaps"][0]["gap"] == pytest.approx(0.3)


def test_evolution_curve(user_with_credits, client):
    uid = user_with_credits
    for i, score in enumerate([30, 40, 50, 60]):
        client.post(f"/api/v1/scoring/{uid}/evaluate", json={
            "gameplay_id": "structured_reflection",
            "scores": {
                "understanding_depth": score,
                "prediction_accuracy": score,
                "value_resonance": score,
                "correction_integration": score,
                "context_consistency": score,
                "unexpressed_signal_capture": score,
                "actionability": score,
            },
            "date": f"2026-03-{i+1:02d}",
        })

    resp = client.get(f"/api/v1/viz/{uid}/evolution")
    assert resp.status_code == 200
    timeline = resp.json()["timeline"]
    assert len(timeline) == 4
    # Scores should be increasing
    assert timeline[0]["total"] < timeline[-1]["total"]


def test_evolution_empty(client):
    resp = client.get("/api/v1/viz/nobody/evolution")
    assert resp.status_code == 404
