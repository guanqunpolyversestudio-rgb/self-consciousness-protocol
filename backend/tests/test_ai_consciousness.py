"""Test AI Consciousness — ai_self_model + ai_self_accuracy tables."""
import app.local_db as local_db_mod


def test_insert_ai_self_model(client):
    result = local_db_mod.insert_ai_self_model(
        user_id="test_user",
        personality={"E_I": 0.7, "S_N": 0.3, "T_F": 0.6, "J_P": 0.4},
        values={"honesty": 0.9, "efficiency": 0.8},
        reasoning_style="analytical",
        blind_spots=["over-optimism", "sycophancy"],
    )
    assert result["user_id"] == "test_user"
    assert result["reasoning_style"] == "analytical"


def test_get_ai_self_model_history(client):
    local_db_mod.insert_ai_self_model("u1", {"E_I": 0.5}, {}, "balanced", [])
    local_db_mod.insert_ai_self_model("u1", {"E_I": 0.6}, {}, "analytical", ["bias"])

    models = local_db_mod.get_ai_self_model_history("u1")
    assert len(models) == 2
    assert models[0]["reasoning_style"] == "balanced"
    assert models[1]["reasoning_style"] == "analytical"


def test_get_ai_self_model_history_empty(client):
    models = local_db_mod.get_ai_self_model_history("nobody")
    assert models == []


def test_insert_ai_self_accuracy(client):
    result = local_db_mod.insert_ai_self_accuracy(
        user_id="test_user",
        dimension="empathy",
        self_score=0.8,
        user_score=0.5,
    )
    assert result["user_id"] == "test_user"
    assert result["gap"] == pytest.approx(0.3)


def test_get_ai_self_accuracy(client):
    local_db_mod.insert_ai_self_accuracy("u2", "empathy", 0.8, 0.6)
    local_db_mod.insert_ai_self_accuracy("u2", "logic", 0.9, 0.9)

    records = local_db_mod.get_ai_self_accuracy("u2")
    assert len(records) == 2


def test_ai_self_accuracy_gap_auto_calculated(client):
    local_db_mod.insert_ai_self_accuracy("u3", "humor", 0.7, 0.3)
    records = local_db_mod.get_ai_self_accuracy("u3")
    assert records[0]["gap"] == pytest.approx(0.4)


import pytest
