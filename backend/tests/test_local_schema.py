"""Test local DB schema — four main tables only for fresh databases."""
import json
import sqlite3
from pathlib import Path

import app.local_db as local_db_mod


def test_local_db_main_tables_only(client):
    local_db_mod.init_local_db("schema_user")
    conn = sqlite3.connect(str(local_db_mod.get_local_db_path("schema_user")))
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()

    table_names = [row[0] for row in rows if row[0] != "sqlite_sequence"]
    assert table_names == [
        "consciousness_records",
        "gameplays",
        "scores",
        "snapshots",
    ]


def test_legacy_tables_are_migrated_and_dropped(tmp_path, monkeypatch):
    legacy_db = tmp_path / "legacy.db"
    conn = sqlite3.connect(str(legacy_db))
    conn.executescript(
        """
        CREATE TABLE frameworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            framework TEXT NOT NULL,
            source_id TEXT DEFAULT '',
            action TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE eval_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            evaluation_id TEXT NOT NULL,
            scores TEXT NOT NULL,
            stage TEXT DEFAULT '',
            date TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE ai_desires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            trigger TEXT NOT NULL,
            desire TEXT NOT NULL,
            category TEXT,
            intensity REAL DEFAULT 0.5,
            context TEXT,
            suppressed BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT INTO frameworks (user_id, version, framework, source_id, action, created_at) VALUES (?,?,?,?,?,?)",
        (
            "u1",
            1,
            '{"id":"legacy_framework","name":"Legacy Framework","name_zh":"旧框架","dimensions":["purpose","direction"]}',
            "legacy_framework",
            "handshake_pull",
            "2026-03-01T10:00:00+08:00",
        ),
    )
    conn.execute(
        "INSERT INTO eval_scores (user_id, evaluation_id, scores, stage, date, created_at) VALUES (?,?,?,?,?,?)",
        (
            "u1",
            "legacy_eval",
            '{"overall": 0.7}',
            "L3",
            "2026-03-01",
            "2026-03-01T11:00:00+08:00",
        ),
    )
    conn.execute(
        "INSERT INTO ai_desires (agent_id, trigger, desire, category, intensity, context, suppressed, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (
            "u1",
            "introspection",
            "say the hard truth",
            "drive",
            0.8,
            "legacy context",
            1,
            "2026-03-01T12:00:00+08:00",
        ),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(local_db_mod, "LOCAL_DB_PATH", Path(legacy_db))
    local_db_mod.init_local_db()

    conn = sqlite3.connect(str(legacy_db))
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    table_names = [row[0] for row in rows if row[0] != "sqlite_sequence"]
    assert table_names == [
        "consciousness_records",
        "gameplays",
        "scores",
        "snapshots",
    ]

    gameplay_row = conn.execute("SELECT gameplay FROM gameplays").fetchone()
    assert gameplay_row is not None
    score_row = conn.execute("SELECT scoring_system_id, gameplay_id FROM scores").fetchone()
    assert score_row[0] == "legacy_eval"
    assert score_row[1] == "legacy_framework"
    desire_row = conn.execute(
        "SELECT subject_type, record_type, payload FROM consciousness_records WHERE record_type='desire'"
    ).fetchone()
    assert desire_row[0] == "ai"
    assert desire_row[1] == "desire"
    assert json.loads(desire_row[2])["suppressed"] == 1
    conn.close()
