"""Daily alignment API tests."""


def test_daily_alignment_question_set(user_with_credits, client):
    resp = client.post(f"/api/v1/alignment/{user_with_credits}/question-set", json={"theme": "mirror"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["session_id"].startswith("aln_")
    assert len(data["questions"]) == 3
    assert data["game_layer"]["mode"] == "blind_guess_streak"


def test_daily_alignment_answer_and_history(user_with_credits, client):
    qs = client.post(f"/api/v1/alignment/{user_with_credits}/question-set", json={}).json()
    question = qs["questions"][0]

    answer_resp = client.post(
        f"/api/v1/alignment/{user_with_credits}/answer",
        json={
            "session_id": qs["session_id"],
            "question_id": question["id"],
            "dimension": question["dimension"],
            "question": question["prompt"],
            "agent_answer": "你现在最在意的是保持方向感。",
            "user_answer": "我第一反应确实是先别失去方向。",
            "user_match": True,
            "notes": "方向判断命中了",
        },
    )
    assert answer_resp.status_code == 200
    assert answer_resp.json()["user_match"] is True

    ask_resp = client.post(
        f"/api/v1/alignment/{user_with_credits}/ask",
        json={
            "session_id": qs["session_id"],
            "asker": "user",
            "dimension": "bidirectional",
            "question": "你为什么总先看长期方向？",
            "answer": "因为我会先用稳定目标过滤短期波动。",
        },
    )
    assert ask_resp.status_code == 200

    history = client.get(f"/api/v1/alignment/{user_with_credits}/history")
    assert history.status_code == 200
    records = history.json()["records"]
    assert any(item["record_type"] == "intuition_guess" for item in records)
    assert any(item["record_type"] == "answer" for item in records)
