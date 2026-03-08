"""Test onboarding — register user, write local profile, save preferences."""

import json

import app.user_data as user_data_mod


def test_register_creates_profile_and_workspace(client):
    resp = client.post("/api/v1/onboarding/register", json={"user_id": "fresh_user"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["credits"] == 500
    assert data["default_gameplay"] == "structured_reflection"
    assert data["onboarding_mode"] == "structured_alignment_workspace"
    assert data["workspace"]["db_path"].endswith("/users/fresh_user/consciousness.db")

    profile = json.loads(user_data_mod.PROFILE_PATH.read_text(encoding="utf-8"))
    assert profile["current_user_id"] == "fresh_user"
    assert profile["users"]["fresh_user"]["workspace"]["gameplay_drafts_dir"].endswith("/users/fresh_user/gameplay_drafts")


def test_preference_updates_user_profile(client):
    client.post("/api/v1/onboarding/register", json={"user_id": "pref_user"})
    resp = client.post(
        "/api/v1/onboarding/preference",
        json={
            "user_id": "pref_user",
            "onboarding_mode": "playful_alignment_experience",
            "final_answer_format": "checklist",
            "notes": "Prefer gameful sessions.",
            "preferred_gameplay_ids": ["belief_interrogation"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarding_mode"] == "playful_alignment_experience"
    assert data["preference_payload"]["final_answer_format"] == "checklist"
    assert data["preference_payload"]["preferred_gameplay_ids"] == ["belief_interrogation"]
