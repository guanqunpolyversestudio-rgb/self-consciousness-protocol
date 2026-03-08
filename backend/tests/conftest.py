"""Shared fixtures — temp DB files, fully isolated from production."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SEED_GAMEPLAYS = [
    {
        "id": "structured_reflection",
        "name": "Structured Reflection",
        "name_zh": "结构化自省",
        "summary": "一个五维对齐工作台，user 输入五维，agent 也在同一五维上呈现理解和对齐。",
        "consciousness_architecture": {
            "dimensions": ["purpose", "direction", "constraints", "evaluation", "interaction"],
            "description": "五维反思镜头",
        },
        "loop": {
            "cadence": "session",
            "participants": "solo",
            "phases": [
                {"id": "user_input", "name": "User Input", "goal": "user 填五维"},
                {"id": "agent_mirror", "name": "Agent Mirror", "goal": "agent 五维呈现"},
                {"id": "alignment_check", "name": "Alignment Check", "goal": "逐维对齐"},
                {"id": "metric_test", "name": "Metric Test", "goal": "指标验证"},
                {"id": "dimension_experience", "name": "Dimension Experience", "goal": "维度体验"},
            ],
        },
        "interfaces": {
            "user_input": {"type": "five_dimension_capture", "dimensions": ["purpose", "direction", "constraints", "evaluation", "interaction"]},
            "agent_alignment": {"type": "five_dimension_alignment_board", "dimensions": ["purpose", "direction", "constraints", "evaluation", "interaction"]},
            "evaluation": {"type": "alignment_metric_test_panel"},
            "experience": {"type": "dimension_experience_switcher"},
        },
        "difficulty": "L1-L3",
        "tags": ["structured", "default", "alignment_workspace"],
        "markdown": "# 结构化自省\n\n五维对齐工作台。\n",
    },
    {
        "id": "belief_interrogation",
        "name": "Belief Interrogation",
        "name_zh": "信念拷问",
        "summary": "高压玩法，拆解信念和行为之间的偏差。",
        "consciousness_architecture": {
            "dimensions": ["beliefs", "confidence", "intent", "values", "preference"],
            "description": "BCIVP 框架",
        },
        "loop": {
            "cadence": "session",
            "participants": "solo",
            "phases": [
                {"id": "claim", "name": "Claim", "goal": "给出明确主张"},
                {"id": "challenge", "name": "Challenge", "goal": "追问反例"},
                {"id": "score", "name": "Score", "goal": "打分"},
                {"id": "rewrite", "name": "Rewrite", "goal": "改写信念"},
            ],
        },
        "difficulty": "L2-L4",
        "tags": ["deep", "challenging", "psychological"],
        "interfaces": {},
        "markdown": "# 信念拷问\n\n适合平台期。\n",
    },
    {
        "id": "intuition_challenge_30d",
        "name": "30-Day Intuition Challenge",
        "name_zh": "30天直觉挑战",
        "summary": "30 天轻量高频猜测 loop，不强制固定意识架构。",
        "consciousness_architecture": None,
        "loop": {
            "cadence": "daily",
            "participants": "solo",
            "phases": [
                {"id": "guess", "name": "Guess", "goal": "先猜"},
                {"id": "reveal", "name": "Reveal", "goal": "公开真实答案"},
                {"id": "score", "name": "Score", "goal": "记录命中率"},
                {"id": "tune", "name": "Tune", "goal": "调整下一轮"},
            ],
        },
        "difficulty": "L1-L2",
        "tags": ["challenge", "30day", "fun"],
        "interfaces": {},
        "markdown": "# 30天直觉挑战\n\n每天一轮。\n",
    },
    {
        "id": "couple_alignment",
        "name": "Couple Alignment Challenge",
        "name_zh": "情侣对齐挑战",
        "summary": "双人 loop，通过 cross prediction 和 repair action 做关系对齐。",
        "consciousness_architecture": {"dimensions": ["emotional_needs", "communication_style", "conflict_resolution", "shared_values", "growth_direction"]},
        "loop": {
            "cadence": "weekly",
            "participants": "duo",
            "phases": [
                {"id": "dual_capture", "name": "Dual Capture", "goal": "双方分别记录"},
                {"id": "cross_prediction", "name": "Cross Prediction", "goal": "互猜"},
                {"id": "score", "name": "Score", "goal": "打分"},
                {"id": "repair_action", "name": "Repair Action", "goal": "定义修复动作"},
            ],
        },
        "difficulty": "L2-L3",
        "tags": ["couples", "relationship"],
        "interfaces": {},
        "markdown": "# 情侣对齐挑战\n\n双人玩法。\n",
    },
    {
        "id": "agent_genesis",
        "name": "Agent Genesis",
        "name_zh": "Agent创世纪",
        "summary": "章节式 narrative loop，适合 onboarding 和阶段切换。",
        "consciousness_architecture": None,
        "loop": {
            "cadence": "chapter",
            "participants": "solo",
            "phases": [
                {"id": "invoke", "name": "Invoke", "goal": "定义章节问题"},
                {"id": "narrate", "name": "Narrate", "goal": "写叙事"},
                {"id": "score", "name": "Score", "goal": "打分"},
                {"id": "reauthor", "name": "Reauthor", "goal": "定义下一章"},
            ],
        },
        "difficulty": "L0-L4",
        "tags": ["narrative", "story", "onboarding"],
        "interfaces": {},
        "markdown": "# Agent创世纪\n\n章节式玩法。\n",
    },
    {
        "id": "mbti_alignment",
        "name": "MBTI Alignment",
        "name_zh": "MBTI对齐",
        "summary": "低门槛 baseline loop，同时校准 user 被理解程度和 agent 自知度。",
        "consciousness_architecture": {"dimensions": ["E_I", "S_N", "T_F", "J_P"]},
        "loop": {
            "cadence": "baseline",
            "participants": "solo",
            "phases": [
                {"id": "user_self_report", "name": "User Self Report", "goal": "user 自评"},
                {"id": "ai_prediction", "name": "AI Prediction", "goal": "agent 预测"},
                {"id": "compare", "name": "Compare", "goal": "对比差异"},
                {"id": "calibrate", "name": "Calibrate", "goal": "形成校准点"},
            ],
        },
        "difficulty": "L0-L1",
        "tags": ["personality", "baseline", "bidirectional"],
        "interfaces": {},
        "markdown": "# MBTI对齐\n\nbaseline 玩法。\n",
    },
]

SEED_SCORING_STAGES = {
    "id": "core_alignment",
    "version": "test-v1",
    "scoring_dimensions": [
        {"id": "understanding_depth", "priority": 1, "name": "理解深度", "weight": 0.24},
        {"id": "prediction_accuracy", "priority": 2, "name": "预测准确度", "weight": 0.2},
        {"id": "value_resonance", "priority": 3, "name": "价值贴合", "weight": 0.17},
        {"id": "correction_integration", "priority": 4, "name": "纠偏吸收", "weight": 0.14},
        {"id": "context_consistency", "priority": 5, "name": "上下文一致性", "weight": 0.1},
        {"id": "unexpressed_signal_capture", "priority": 6, "name": "未表达信号捕捉", "weight": 0.09},
        {"id": "actionability", "priority": 7, "name": "可行动性", "weight": 0.06},
    ],
    "stages": [
        {"level": "L0", "name": "Stranger", "range": [0, 20]},
        {"level": "L1", "name": "Perceiving", "range": [20, 40]},
        {"level": "L2", "name": "Understanding", "range": [40, 60]},
        {"level": "L3", "name": "Resonating", "range": [60, 80]},
        {"level": "L4", "name": "Fusing", "range": [80, 100]},
    ],
    "gameplay_recommendation_rules": {
        "plateau_days": 7,
        "plateau_action": "recommend_gameplay_switch",
        "dimension_weak_threshold": 0.4,
    },
}


@pytest.fixture()
def tmp_skill_root(tmp_path):
    gr = tmp_path / "global_registry"
    gr.mkdir()
    gp_dir = gr / "gameplays"
    gp_dir.mkdir()
    for gameplay in SEED_GAMEPLAYS:
        metadata = {
            "id": gameplay["id"],
            "name": gameplay["name"],
            "name_zh": gameplay.get("name_zh", ""),
            "summary": gameplay.get("summary", ""),
            "consciousness_architecture": gameplay.get("consciousness_architecture"),
            "loop": gameplay.get("loop", {}),
            "interfaces": gameplay.get("interfaces", {}),
            "difficulty": gameplay.get("difficulty", ""),
            "tags": gameplay.get("tags", []),
            "created_at": "2026-03-07T00:00:00Z",
        }
        body = gameplay.get("markdown", "")
        content = f"---\n{json.dumps(metadata, ensure_ascii=False, indent=2)}\n---\n\n{body}"
        (gp_dir / f"{gameplay['id']}.md").write_text(content, encoding="utf-8")
    (gr / "scoring_stages.json").write_text(json.dumps(SEED_SCORING_STAGES, ensure_ascii=False))
    (tmp_path / "memory").mkdir()
    return tmp_path


@pytest.fixture()
def client(tmp_skill_root, tmp_path, monkeypatch):
    import app.node_bridge as nb
    import app.db as db_mod
    import app.local_db as local_db_mod
    import app.user_data as user_data_mod
    import app.routers.scoring as scoring_mod
    import app.tools_gateway as tools_gateway_mod

    monkeypatch.setattr(nb, "SKILL_ROOT", tmp_skill_root)
    monkeypatch.setattr(tools_gateway_mod, "SKILL_ROOT", tmp_skill_root)

    tmp_backend_db = tmp_skill_root / "memory" / "test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_backend_db)

    tmp_user_root = tmp_path / "self-consciousness"
    tmp_local_db = tmp_user_root / "consciousness.db"
    tmp_user_root.mkdir(parents=True)
    monkeypatch.setattr(user_data_mod, "USER_DATA_ROOT", tmp_user_root)
    monkeypatch.setattr(user_data_mod, "PROFILE_PATH", tmp_user_root / "profile.json")
    monkeypatch.setattr(local_db_mod, "LOCAL_DB_PATH", tmp_local_db)

    # Reset scoring cache
    scoring_mod._scoring_stages_cache = None

    db_mod.init_db()
    db_mod.seed_from_json()

    from app.main import app
    return TestClient(app)


@pytest.fixture()
def user_with_credits(client):
    resp = client.post("/api/v1/onboarding/register", json={"user_id": "test_user"})
    assert resp.status_code == 200
    return "test_user"
