"""Test DB 4: Alignment Tasks — escrowed bounty lifecycle."""


def _create_reviewing_task(client, creator_id: str, solver_id: str, *, price: int = 10, review_reward: int = 1):
    create_resp = client.post(
        "/api/v1/tasks",
        json={
            "user_id": creator_id,
            "description": "AI misunderstands my humor",
            "price": price,
            "review_reward": review_reward,
        },
    )
    task_id = create_resp.json()["task"]["id"]
    client.post("/api/v1/handshake", json={"user_id": solver_id})
    client.post(f"/api/v1/tasks/{task_id}/claim", params={"user_id": solver_id})
    client.post(
        f"/api/v1/tasks/{task_id}/solve",
        json={"user_id": solver_id, "solution": "Use more context from previous conversations"},
    )
    return task_id


def test_create_task(user_with_credits, client):
    resp = client.post(
        "/api/v1/tasks",
        json={
            "user_id": user_with_credits,
            "description": "AI doesn't understand my sarcasm",
            "price": 20,
            "review_reward": 2,
            "tags": ["sarcasm", "tone"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["credit_deducted"] == 20
    assert data["task"]["status"] == "open"
    assert data["task"]["settlement_status"] == "escrowed"
    assert data["task"]["price"] == 20
    assert data["task"]["review_reward"] == 2

    resp2 = client.get(f"/api/v1/credits/{user_with_credits}/balance")
    assert resp2.json()["balance"] == 480


def test_create_task_returns_structured_experience(user_with_credits, client):
    resp = client.post(
        "/api/v1/tasks",
        json={
            "user_id": user_with_credits,
            "proposer_type": "agent",
            "title": "Fix purpose drift",
            "summary": "The agent keeps missing the user's real purpose behind recent choices.",
            "gameplay_id": "structured_reflection",
            "dimension_id": "purpose",
            "desired_outcome": "Agent can restate purpose in the user's own language.",
            "current_gap": "Current summaries are accurate on facts but not motivation.",
            "acceptance_criteria": [
                "Purpose dimension is mirrored without adding extra assumptions",
                "User confirms the purpose readback feels right",
            ],
            "context_notes": "Recent discussions were about career change.",
            "deliverable_format": "playbook",
            "price": 8,
            "review_reward": 1,
            "tags": ["purpose", "mirror"],
        },
    )
    assert resp.status_code == 200
    task = resp.json()["task"]
    assert task["proposer_type"] == "agent"
    assert task["title"] == "Fix purpose drift"
    assert task["gameplay_id"] == "structured_reflection"
    assert task["framework_id"] == "structured_reflection"
    assert task["experience"]["publisher"]["type"] == "task_brief"
    assert task["experience"]["solver"]["type"] == "solver_workspace"
    assert task["experience"]["reviewer"]["type"] == "review_panel"


def test_create_task_insufficient_credits(client):
    resp = client.post(
        "/api/v1/tasks",
        json={"user_id": "poor_user", "description": "some problem", "price": 5},
    )
    assert resp.status_code == 400
    assert "Insufficient" in resp.json()["detail"]


def test_list_tasks(user_with_credits, client):
    client.post("/api/v1/tasks", json={"user_id": user_with_credits, "description": "task 1"})
    client.post("/api/v1/tasks", json={"user_id": user_with_credits, "description": "task 2"})

    resp = client.get("/api/v1/tasks")
    assert resp.status_code == 200
    assert len(resp.json()["tasks"]) == 2


def test_get_task(user_with_credits, client):
    create_resp = client.post("/api/v1/tasks", json={"user_id": user_with_credits, "description": "get me"})
    task_id = create_resp.json()["task"]["id"]

    resp = client.get(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["description"] == "get me"


def test_get_task_not_found(client):
    resp = client.get("/api/v1/tasks/task_nonexistent")
    assert resp.status_code == 404


def test_full_lifecycle(user_with_credits, client):
    create_resp = client.post(
        "/api/v1/tasks",
        json={"user_id": user_with_credits, "description": "AI misunderstands my humor", "price": 10, "review_reward": 1},
    )
    task_id = create_resp.json()["task"]["id"]

    client.post("/api/v1/handshake", json={"user_id": "solver_user"})

    claim_resp = client.post(f"/api/v1/tasks/{task_id}/claim", params={"user_id": "solver_user"})
    assert claim_resp.status_code == 200
    assert claim_resp.json()["task"]["status"] == "claimed"

    solve_resp = client.post(
        f"/api/v1/tasks/{task_id}/solve",
        json={"user_id": "solver_user", "solution": "Use more context from previous conversations"},
    )
    assert solve_resp.status_code == 200
    assert solve_resp.json()["task"]["status"] == "reviewing"

    resp = client.get("/api/v1/credits/solver_user/balance")
    assert resp.json()["balance"] == 500

    resp2 = client.get(f"/api/v1/credits/{user_with_credits}/balance")
    assert resp2.json()["balance"] == 490


def test_claim_already_claimed(user_with_credits, client):
    create_resp = client.post("/api/v1/tasks", json={"user_id": user_with_credits, "description": "claim test"})
    task_id = create_resp.json()["task"]["id"]

    client.post(f"/api/v1/tasks/{task_id}/claim", params={"user_id": "user_a"})
    resp = client.post(f"/api/v1/tasks/{task_id}/claim", params={"user_id": "user_b"})
    assert resp.status_code == 400


def test_solve_requires_claim_owner(user_with_credits, client):
    create_resp = client.post("/api/v1/tasks", json={"user_id": user_with_credits, "description": "solve test"})
    task_id = create_resp.json()["task"]["id"]

    client.post("/api/v1/handshake", json={"user_id": "solver_a"})
    client.post("/api/v1/handshake", json={"user_id": "solver_b"})
    client.post(f"/api/v1/tasks/{task_id}/claim", params={"user_id": "solver_a"})

    resp = client.post(f"/api/v1/tasks/{task_id}/solve", json={"user_id": "solver_b", "solution": "nope"})
    assert resp.status_code == 400


def test_recommend_tasks(user_with_credits, client):
    client.post("/api/v1/tasks", json={"user_id": user_with_credits, "description": "alignment task", "task_type": "alignment", "price": 9})
    client.post("/api/v1/tasks", json={"user_id": user_with_credits, "description": "repair task", "task_type": "repair", "price": 20})

    resp = client.get("/api/v1/tasks/recommend", params={"user_id": "other_user"})
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    assert len(tasks) >= 1
    assert tasks[0]["task_type"] == "alignment"
    assert all(t["user_id"] != "other_user" for t in tasks)


def test_review_cannot_review_own(user_with_credits, client):
    task_id = _create_reviewing_task(client, user_with_credits, "solver_self")

    resp = client.post(
        f"/api/v1/tasks/{task_id}/review",
        json={"reviewer_id": user_with_credits, "resonance": 8, "novelty": 8, "depth": 8, "actionability": 8},
    )
    assert resp.status_code == 400

    resp2 = client.post(
        f"/api/v1/tasks/{task_id}/review",
        json={"reviewer_id": "solver_self", "resonance": 8, "novelty": 8, "depth": 8, "actionability": 8},
    )
    assert resp2.status_code == 400


def test_verification_pass_and_settlement(user_with_credits, client):
    task_id = _create_reviewing_task(client, user_with_credits, "solver_v", price=10, review_reward=1)

    for i, scores in enumerate(
        [
            (8, 7, 9, 6),
            (2, 3, 1, 4),
            (7, 8, 6, 7),
            (1, 2, 3, 2),
            (9, 8, 7, 8),
        ]
    ):
        resp = client.post(
            f"/api/v1/tasks/{task_id}/review",
            json={
                "reviewer_id": f"r_{i}",
                "resonance": scores[0],
                "novelty": scores[1],
                "depth": scores[2],
                "actionability": scores[3],
                "recommendation": "approve" if i in {0, 2, 4} else "revise",
            },
        )

    assert resp.json()["verification"] == "verified"
    assert resp.json()["settlement_status"] == "ready"

    pre_solver = client.get("/api/v1/credits/solver_v/balance").json()["balance"]
    assert pre_solver == 500

    settle = client.post(f"/api/v1/tasks/{task_id}/settle", json={"user_id": user_with_credits})
    assert settle.status_code == 200
    body = settle.json()
    assert body["solver_reward"] == 5
    assert body["review_reward_total"] == 5
    assert body["task"]["settlement_status"] == "settled"

    post_solver = client.get("/api/v1/credits/solver_v/balance").json()["balance"]
    assert post_solver == 505
    reviewer_balance = client.get("/api/v1/credits/r_0/balance").json()["balance"]
    assert reviewer_balance == 1


def test_verification_fail_and_refund(user_with_credits, client):
    task_id = _create_reviewing_task(client, user_with_credits, "solver_r", price=10, review_reward=1)

    for i, scores in enumerate(
        [
            (8, 7, 9, 6),
            (2, 3, 1, 4),
            (1, 2, 3, 2),
            (1, 2, 3, 2),
            (9, 8, 7, 8),
        ]
    ):
        resp = client.post(
            f"/api/v1/tasks/{task_id}/review",
            json={
                "reviewer_id": f"rj_{i}",
                "resonance": scores[0],
                "novelty": scores[1],
                "depth": scores[2],
                "actionability": scores[3],
            },
        )

    assert resp.json()["verification"] == "rejected"

    settle = client.post(f"/api/v1/tasks/{task_id}/settle", json={"user_id": user_with_credits})
    assert settle.status_code == 200
    body = settle.json()
    assert body["creator_refund"] == 5
    assert body["solver_reward"] == 0

    creator_balance = client.get(f"/api/v1/credits/{user_with_credits}/balance").json()["balance"]
    assert creator_balance == 495


def test_get_reviews(user_with_credits, client):
    task_id = _create_reviewing_task(client, user_with_credits, "sv")
    client.post(
        f"/api/v1/tasks/{task_id}/review",
        json={"reviewer_id": "rv1", "resonance": 8, "novelty": 7, "depth": 6, "actionability": 5},
    )

    resp = client.get(f"/api/v1/tasks/{task_id}/reviews")
    assert resp.status_code == 200
    assert len(resp.json()["reviews"]) == 1
    assert resp.json()["verification"]["total_reviews"] == 1
