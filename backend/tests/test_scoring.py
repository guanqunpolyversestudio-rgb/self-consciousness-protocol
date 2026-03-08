"""Test Scoring — stages, evaluate, current, history, recommend."""


def test_get_stages(client):
    resp = client.get("/api/v1/scoring/stages")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "core_alignment"
    assert data["version"] == "test-v1"
    assert len(data["stages"]) == 5
    assert data["stages"][0]["level"] == "L0"
    assert len(data["scoring_dimensions"]) == 7
    assert data["scoring_dimensions"][0]["id"] == "understanding_depth"
    assert data["scoring_dimensions"][0]["priority"] == 1


def test_evaluate(user_with_credits, client):
    resp = client.post(f"/api/v1/scoring/{user_with_credits}/evaluate", json={
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
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == pytest.approx(41.6)
    assert data["stage"] == "L2"
    assert data["scoring_system_id"] == "core_alignment"
    assert data["scoring_system_version"] == "test-v1"


def test_current(user_with_credits, client):
    # Submit a score first
    client.post(f"/api/v1/scoring/{user_with_credits}/evaluate", json={
        "gameplay_id": "structured_reflection",
        "scores": {
            "understanding_depth": 70,
            "prediction_accuracy": 70,
            "value_resonance": 70,
            "correction_integration": 70,
            "context_consistency": 70,
            "unexpressed_signal_capture": 70,
            "actionability": 70,
        },
    })
    resp = client.get(f"/api/v1/scoring/{user_with_credits}/current")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == pytest.approx(70.0)
    assert data["stage"] == "L3"


def test_current_no_scores(client):
    resp = client.get("/api/v1/scoring/nobody/current")
    assert resp.status_code == 404


def test_history(user_with_credits, client):
    client.post(f"/api/v1/scoring/{user_with_credits}/evaluate", json={
        "gameplay_id": "structured_reflection",
        "scores": {
            "understanding_depth": 30,
            "prediction_accuracy": 30,
            "value_resonance": 30,
            "correction_integration": 30,
            "context_consistency": 30,
            "unexpressed_signal_capture": 30,
            "actionability": 30,
        },
        "date": "2026-03-01",
    })
    client.post(f"/api/v1/scoring/{user_with_credits}/evaluate", json={
        "gameplay_id": "structured_reflection",
        "scores": {
            "understanding_depth": 50,
            "prediction_accuracy": 50,
            "value_resonance": 50,
            "correction_integration": 50,
            "context_consistency": 50,
            "unexpressed_signal_capture": 50,
            "actionability": 50,
        },
        "date": "2026-03-02",
    })
    resp = client.get(f"/api/v1/scoring/{user_with_credits}/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 2


def test_recommend_no_history(user_with_credits, client):
    resp = client.get(f"/api/v1/scoring/{user_with_credits}/recommend")
    assert resp.status_code == 200
    assert resp.json()["reason"] == "no_history"
    assert resp.json()["recommended"]["id"] == "structured_reflection"


def test_recommend_plateau(user_with_credits, client):
    # Submit 7 identical scores to trigger plateau
    for i in range(7):
        client.post(f"/api/v1/scoring/{user_with_credits}/evaluate", json={
            "gameplay_id": "structured_reflection",
            "scores": {
                "understanding_depth": 50,
                "prediction_accuracy": 50,
                "value_resonance": 50,
                "correction_integration": 50,
                "context_consistency": 50,
                "unexpressed_signal_capture": 50,
                "actionability": 50,
            },
            "date": f"2026-03-{i+1:02d}",
        })
    resp = client.get(f"/api/v1/scoring/{user_with_credits}/recommend")
    assert resp.status_code == 200
    assert resp.json()["reason"] == "plateau_detected"
    assert resp.json()["recommended"]["id"] != "structured_reflection"


def test_recommend_weak_dimension(user_with_credits, client):
    # Threshold is 0.4, so score 0.1 should trigger weak dimension
    client.post(f"/api/v1/scoring/{user_with_credits}/evaluate", json={
        "gameplay_id": "structured_reflection",
        "scores": {
            "understanding_depth": 0.1,
            "prediction_accuracy": 0.8,
            "value_resonance": 0.8,
            "correction_integration": 0.8,
            "context_consistency": 0.8,
            "unexpressed_signal_capture": 0.8,
            "actionability": 0.8,
        },
    })
    resp = client.get(f"/api/v1/scoring/{user_with_credits}/recommend")
    assert resp.status_code == 200
    assert resp.json()["reason"] == "weak_dimension:understanding_depth"


import pytest
