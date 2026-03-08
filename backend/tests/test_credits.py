"""Test Credit System — init + balance consistency across operations."""


def test_init_credits(client):
    resp = client.post("/api/v1/credits/new_user/init")
    assert resp.status_code == 200
    assert resp.json()["balance"] == 500


def test_init_idempotent(client):
    client.post("/api/v1/credits/idem_user/init")
    resp2 = client.post("/api/v1/credits/idem_user/init")
    assert resp2.status_code == 200
    assert resp2.json()["message"] == "Already initialized"
    assert resp2.json()["balance"] == 500


def test_balance_zero_for_unknown(client):
    resp = client.get("/api/v1/credits/unknown_user/balance")
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0


def test_balance_after_handshake(user_with_credits, client):
    resp = client.get(f"/api/v1/credits/{user_with_credits}/balance")
    assert resp.json()["balance"] == 500


def test_transactions_after_handshake(user_with_credits, client):
    resp = client.get(f"/api/v1/credits/{user_with_credits}/transactions")
    assert resp.status_code == 200
    txns = resp.json()["transactions"]
    assert len(txns) >= 1
    assert txns[0]["type"] == "init"
    assert txns[0]["amount"] == 500


def test_balance_consistency_multi_ops(user_with_credits, client):
    """Perform multiple operations and verify final balance is consistent."""
    uid = user_with_credits  # starts at 500

    # Create a task (-5) → 495
    client.post("/api/v1/tasks", json={"user_id": uid, "description": "t1"})

    # Contribute a gameplay (+10) → 505
    client.post("/api/v1/gameplays/contribute", json={
        "user_id": uid,
        "gameplay": {"id": "gp_test", "name": "Test"},
    })

    # Create another task (-5) → 500
    client.post("/api/v1/tasks", json={"user_id": uid, "description": "t2"})

    resp = client.get(f"/api/v1/credits/{uid}/balance")
    assert resp.json()["balance"] == 500

    # Check all transactions are recorded
    resp2 = client.get(f"/api/v1/credits/{uid}/transactions")
    txns = resp2.json()["transactions"]
    assert len(txns) == 4  # init + deduct + earn + deduct


def test_insufficient_credits_prevents_action(client):
    """User with 0 credits cannot create a task."""
    resp = client.post("/api/v1/tasks", json={
        "user_id": "broke_user", "description": "should fail",
    })
    assert resp.status_code == 400
