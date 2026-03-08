"""Test tools gateway and media job persistence."""


def test_tools_capabilities_detect_backend_dotenv(tmp_skill_root, monkeypatch):
    import app.tools_gateway as tools_gateway

    (tmp_skill_root / "backend").mkdir(exist_ok=True)
    (tmp_skill_root / "backend" / ".env").write_text("WAVESPEED_API_KEY=test-key\n", encoding="utf-8")
    monkeypatch.setattr(tools_gateway, "SKILL_ROOT", tmp_skill_root)

    capabilities = tools_gateway.list_capabilities()
    image_cap = next(item for item in capabilities if item["id"] == "image.generate")
    assert image_cap["status"] == "available"
    assert image_cap["providers"][0]["configured"] is True


def test_tools_capabilities(client):
    resp = client.get("/api/v1/tools/capabilities")
    assert resp.status_code == 200
    capabilities = resp.json()["capabilities"]
    ids = [item["id"] for item in capabilities]
    assert "image.generate" in ids
    assert "video.generate" in ids
    assert "web.search" in ids


def test_generate_image_requires_provider_config(client):
    resp = client.post(
        "/api/v1/tools/image/generate",
        json={"user_id": "tool_user", "prompt": "a reflective mirror in watercolor"},
    )
    assert resp.status_code == 503
    assert "WaveSpeed is not configured" in resp.json()["detail"]


def test_generate_image_creates_job_and_deducts_credits(client, user_with_credits, monkeypatch):
    import app.tools_service as tools_service

    monkeypatch.setattr(tools_service, "get_wavespeed_api_key", lambda: "test-key")
    monkeypatch.setattr(
        tools_service,
        "submit_prediction",
        lambda **kwargs: {"id": "pred_image_1", "status": "pending"},
    )
    monkeypatch.setattr(
        tools_service,
        "get_prediction_result",
        lambda **kwargs: {
            "status": "completed",
            "outputs": [{"url": "https://example.com/generated.png"}],
        },
    )

    resp = client.post(
        "/api/v1/tools/image/generate",
        json={"user_id": user_with_credits, "prompt": "a reflective mirror in watercolor"},
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert job["capability"] == "image.generate"
    assert job["status"] == "submitted"

    balance = client.get(f"/api/v1/credits/{user_with_credits}/balance").json()["balance"]
    assert balance == 499

    refresh = client.get(f"/api/v1/tools/jobs/{job['id']}")
    assert refresh.status_code == 200
    updated = refresh.json()["job"]
    assert updated["status"] == "completed"
    assert updated["output_urls"][0] == "https://example.com/generated.png"


def test_generate_video_refunds_on_provider_failure(client, user_with_credits, monkeypatch):
    import app.tools_service as tools_service

    monkeypatch.setattr(tools_service, "get_wavespeed_api_key", lambda: "test-key")
    monkeypatch.setattr(
        tools_service,
        "submit_prediction",
        lambda **kwargs: {"id": "pred_video_1", "status": "pending"},
    )
    monkeypatch.setattr(
        tools_service,
        "get_prediction_result",
        lambda **kwargs: {"status": "failed", "error": "provider timeout"},
    )

    resp = client.post(
        "/api/v1/tools/video/generate",
        json={"user_id": user_with_credits, "prompt": "a surreal alignment ritual"},
    )
    assert resp.status_code == 200
    job = resp.json()["job"]
    balance_after_submit = client.get(f"/api/v1/credits/{user_with_credits}/balance").json()["balance"]
    assert balance_after_submit == 495

    refresh = client.get(f"/api/v1/tools/jobs/{job['id']}")
    assert refresh.status_code == 200
    updated = refresh.json()["job"]
    assert updated["status"] == "failed"
    assert updated["refunded_amount"] == 5

    balance_after_refund = client.get(f"/api/v1/credits/{user_with_credits}/balance").json()["balance"]
    assert balance_after_refund == 500
