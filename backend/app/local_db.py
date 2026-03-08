"""Local user SQLite — four main tables under ~/.self-consciousness/users/<user_id>/consciousness.db.

Main tables:
  gameplays             — local gameplay version chain
  scores                — private score history
  consciousness_records — raw consciousness records for both human and AI
  snapshots             — structured state snapshots under a gameplay lens

Legacy helper APIs are preserved as a compatibility layer, but they all map onto
the four tables above.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import user_data

LOCAL_DB_PATH = user_data.USER_DATA_ROOT / "consciousness.db"


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _json_dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_load(value: str, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError, ValueError):
        return fallback


def _default_legacy_local_db_path() -> Path:
    return user_data.USER_DATA_ROOT / "consciousness.db"


def get_local_db_path(user_id: Optional[str] = None) -> Path:
    if LOCAL_DB_PATH != _default_legacy_local_db_path():
        return LOCAL_DB_PATH
    if user_id:
        return user_data.get_user_db_path(user_id)
    return LOCAL_DB_PATH


def _connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _bootstrap_user_db_from_legacy(user_id: str, target_path: Path):
    source_path = _default_legacy_local_db_path()
    if target_path.exists() or not source_path.exists() or source_path == target_path:
        return

    user_data.ensure_user_workspace(user_id)
    source_conn = _connect_db(source_path)
    target_conn = _connect_db(target_path)
    _apply_schema(target_conn)

    for table in ("gameplays", "scores", "consciousness_records", "snapshots"):
        if not _table_exists(source_conn, table):
            continue
        source_cols = _table_columns(source_conn, table)
        target_cols = _table_columns(target_conn, table)
        cols = [col for col in target_cols if col in source_cols]
        if not cols:
            continue
        placeholders = ", ".join("?" for _ in cols)
        col_sql = ", ".join(cols)
        rows = source_conn.execute(
            f"SELECT {col_sql} FROM {table} WHERE user_id=? ORDER BY id",
            (user_id,),
        ).fetchall()
        for row in rows:
            target_conn.execute(
                f"INSERT OR IGNORE INTO {table} ({col_sql}) VALUES ({placeholders})",
                tuple(row[col] for col in cols),
            )

    target_conn.commit()
    source_conn.close()
    target_conn.close()


def get_local_conn(user_id: Optional[str] = None) -> sqlite3.Connection:
    path = get_local_db_path(user_id)
    if user_id and LOCAL_DB_PATH == _default_legacy_local_db_path():
        _bootstrap_user_db_from_legacy(user_id, path)
    conn = _connect_db(path)
    _apply_schema(conn)
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    if not _table_exists(conn, table):
        return 0
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return row["count"]


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(conn, table):
        return set()
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str):
    if column not in _table_columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _resolve_gameplay_context(
    user_id: str,
    gameplay_id: str = "",
    gameplay_version: Optional[int] = None,
) -> tuple[str, int]:
    current = get_current_gameplay(user_id)
    if gameplay_id:
        if gameplay_version is not None:
            return gameplay_id, gameplay_version
        if current and current["gameplay"].get("id") == gameplay_id:
            return gameplay_id, current["version"]
        return gameplay_id, 0
    if current:
        return (
            current["gameplay"].get("id", ""),
            gameplay_version if gameplay_version is not None else current["version"],
        )
    return "", gameplay_version if gameplay_version is not None else 0


def _apply_schema(conn: sqlite3.Connection):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS gameplays (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        TEXT NOT NULL,
            version        INTEGER NOT NULL,
            gameplay       TEXT NOT NULL,
            source_id      TEXT DEFAULT '',
            action         TEXT NOT NULL,
            parent_version INTEGER DEFAULT 0,
            change_note    TEXT DEFAULT '',
            created_at     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scores (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                TEXT NOT NULL,
            gameplay_id            TEXT NOT NULL,
            gameplay_version       INTEGER DEFAULT 0,
            scoring_system_id      TEXT NOT NULL DEFAULT 'core_alignment',
            scoring_system_version TEXT DEFAULT '',
            scores                 TEXT NOT NULL,
            stage                  TEXT DEFAULT '',
            date                   TEXT NOT NULL,
            created_at             TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS consciousness_records (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          TEXT NOT NULL,
            subject_type     TEXT NOT NULL DEFAULT 'human',
            record_type      TEXT NOT NULL,
            trigger          TEXT DEFAULT '',
            gameplay_id      TEXT DEFAULT '',
            gameplay_version INTEGER DEFAULT 0,
            date             TEXT DEFAULT '',
            dimension        TEXT DEFAULT '',
            content          TEXT NOT NULL,
            payload          TEXT DEFAULT '{}',
            confidence       REAL DEFAULT 0,
            context          TEXT DEFAULT '',
            created_at       TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          TEXT NOT NULL,
            subject_type     TEXT NOT NULL DEFAULT 'human',
            snapshot_type    TEXT NOT NULL DEFAULT 'consciousness',
            date             TEXT NOT NULL,
            gameplay_id      TEXT DEFAULT '',
            gameplay_version INTEGER DEFAULT 0,
            state            TEXT NOT NULL,
            meta             TEXT DEFAULT '{}',
            created_at       TEXT NOT NULL
        );
    """
    )

    _ensure_column(conn, "gameplays", "parent_version", "INTEGER DEFAULT 0")
    _ensure_column(conn, "gameplays", "change_note", "TEXT DEFAULT ''")

    _ensure_column(conn, "scores", "gameplay_version", "INTEGER DEFAULT 0")
    _ensure_column(conn, "scores", "scoring_system_id", "TEXT NOT NULL DEFAULT 'core_alignment'")
    _ensure_column(conn, "scores", "scoring_system_version", "TEXT DEFAULT ''")

    _ensure_column(conn, "snapshots", "subject_type", "TEXT NOT NULL DEFAULT 'human'")
    _ensure_column(conn, "snapshots", "snapshot_type", "TEXT NOT NULL DEFAULT 'consciousness'")
    _ensure_column(conn, "snapshots", "gameplay_id", "TEXT DEFAULT ''")
    _ensure_column(conn, "snapshots", "gameplay_version", "INTEGER DEFAULT 0")
    _ensure_column(conn, "snapshots", "state", "TEXT NOT NULL DEFAULT '{}'")
    _ensure_column(conn, "snapshots", "meta", "TEXT DEFAULT '{}'")

    # Legacy snapshots used `framework_id` + `dimensions`. Preserve and backfill into the
    # new generic columns without requiring destructive table recreation.
    snapshot_cols = _table_columns(conn, "snapshots")
    if "dimensions" in snapshot_cols:
        conn.execute(
            """
            UPDATE snapshots
            SET state = dimensions
            WHERE (state = '{}' OR state = '') AND dimensions IS NOT NULL AND dimensions != ''
            """
        )
    if "framework_id" in snapshot_cols:
        conn.execute(
            """
            UPDATE snapshots
            SET gameplay_id = framework_id
            WHERE gameplay_id = '' AND framework_id IS NOT NULL AND framework_id != ''
            """
        )
    conn.execute(
        "UPDATE snapshots SET snapshot_type='consciousness' WHERE snapshot_type=''"
    )
    conn.execute(
        "UPDATE snapshots SET subject_type='human' WHERE subject_type=''"
    )

    _migrate_legacy_tables(conn)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_gp_user ON gameplays(user_id, version)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_user ON scores(user_id, date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_records_user ON consciousness_records(user_id, created_at)")
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_records_type
           ON consciousness_records(user_id, subject_type, record_type, created_at)"""
    )
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_snapshots_user
           ON snapshots(user_id, subject_type, snapshot_type, date)"""
    )
    conn.commit()


def init_local_db(user_id: Optional[str] = None):
    if user_id and LOCAL_DB_PATH == _default_legacy_local_db_path():
        user_data.ensure_user_workspace(user_id)
    conn = get_local_conn(user_id)
    conn.close()


def _count_records(conn: sqlite3.Connection, record_type: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM consciousness_records WHERE record_type=?",
        (record_type,),
    ).fetchone()
    return row["count"]


def _count_snapshots(conn: sqlite3.Connection, subject_type: str, snapshot_type: str) -> int:
    row = conn.execute(
        """SELECT COUNT(*) AS count
           FROM snapshots
           WHERE subject_type=? AND snapshot_type=?""",
        (subject_type, snapshot_type),
    ).fetchone()
    return row["count"]


def _normalize_snapshots_table(conn: sqlite3.Connection):
    cols = _table_columns(conn, "snapshots")
    final_cols = {
        "id",
        "user_id",
        "subject_type",
        "snapshot_type",
        "date",
        "gameplay_id",
        "gameplay_version",
        "state",
        "meta",
        "created_at",
    }
    if cols == final_cols:
        return

    gameplay_expr = "gameplay_id" if "gameplay_id" in cols else "''"
    if "framework_id" in cols:
        gameplay_expr = f"COALESCE(NULLIF({gameplay_expr}, ''), framework_id, '')"

    state_expr = "state" if "state" in cols else "'{}'"
    if "dimensions" in cols:
        state_expr = f"COALESCE(NULLIF({state_expr}, ''), dimensions, '{{}}')"

    subject_expr = "subject_type" if "subject_type" in cols else "'human'"
    snapshot_type_expr = "snapshot_type" if "snapshot_type" in cols else "'consciousness'"
    gameplay_version_expr = "gameplay_version" if "gameplay_version" in cols else "0"
    meta_expr = "meta" if "meta" in cols else "'{}'"

    conn.executescript(
        """
        DROP TABLE IF EXISTS snapshots__new;
        CREATE TABLE snapshots__new (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          TEXT NOT NULL,
            subject_type     TEXT NOT NULL DEFAULT 'human',
            snapshot_type    TEXT NOT NULL DEFAULT 'consciousness',
            date             TEXT NOT NULL,
            gameplay_id      TEXT DEFAULT '',
            gameplay_version INTEGER DEFAULT 0,
            state            TEXT NOT NULL,
            meta             TEXT DEFAULT '{}',
            created_at       TEXT NOT NULL
        );
        """
    )
    conn.execute(
        f"""
        INSERT INTO snapshots__new
            (id, user_id, subject_type, snapshot_type, date, gameplay_id, gameplay_version, state, meta, created_at)
        SELECT id, user_id, {subject_expr}, {snapshot_type_expr}, date,
               {gameplay_expr}, {gameplay_version_expr}, {state_expr}, {meta_expr}, created_at
        FROM snapshots
        """
    )
    conn.executescript(
        """
        DROP TABLE snapshots;
        ALTER TABLE snapshots__new RENAME TO snapshots;
        """
    )


def _migrate_legacy_frameworks(conn: sqlite3.Connection):
    if not _table_exists(conn, "frameworks"):
        return
    rows = conn.execute("SELECT * FROM frameworks ORDER BY user_id, version").fetchall()
    for row in rows:
        exists = conn.execute(
            "SELECT 1 FROM gameplays WHERE user_id=? AND version=? LIMIT 1",
            (row["user_id"], row["version"]),
        ).fetchone()
        if exists:
            continue
        framework = _json_load(row["framework"], {})
        gameplay_id = framework.get("id") or row["source_id"] or f"legacy_gameplay_v{row['version']}"
        dimensions = framework.get("dimensions", [])
        gameplay = {
            "id": gameplay_id,
            "name": framework.get("name") or gameplay_id,
            "name_zh": framework.get("name_zh", ""),
            "description": framework.get("description", ""),
            "framework": {
                "dimensions": dimensions,
                "description": framework.get("description", ""),
            },
            "interaction_rules": framework.get("interaction_rules", {}),
            "trigger_conditions": framework.get("trigger_conditions", {}),
            "difficulty": framework.get("difficulty", ""),
            "tags": framework.get("tags", ["legacy_migrated"]),
        }
        conn.execute(
            """INSERT INTO gameplays
               (user_id, version, gameplay, source_id, action, parent_version, change_note, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                row["user_id"],
                row["version"],
                _json_dump(gameplay),
                row["source_id"],
                "migrate_framework",
                max(row["version"] - 1, 0),
                "Migrated from legacy frameworks table",
                row["created_at"],
            ),
        )


def _lookup_gameplay_for_legacy_score(conn: sqlite3.Connection, user_id: str, created_at: str) -> tuple[str, int]:
    row = conn.execute(
        """SELECT * FROM gameplays
           WHERE user_id=? AND created_at<=?
           ORDER BY created_at DESC, version DESC
           LIMIT 1""",
        (user_id, created_at),
    ).fetchone()
    if not row:
        row = conn.execute(
            """SELECT * FROM gameplays
               WHERE user_id=?
               ORDER BY created_at DESC, version DESC
               LIMIT 1""",
            (user_id,),
        ).fetchone()
    if not row:
        return "", 0
    gameplay = _json_load(row["gameplay"], {})
    return gameplay.get("id", ""), row["version"]


def _migrate_legacy_evaluations(conn: sqlite3.Connection):
    if _table_exists(conn, "evaluations") and _count_records(conn, "evaluation_definition") == 0:
        rows = conn.execute("SELECT * FROM evaluations ORDER BY user_id, version").fetchall()
        for row in rows:
            evaluation = _json_load(row["evaluation"], {})
            content = evaluation.get("name") or evaluation.get("id") or "evaluation_definition"
            insert_consciousness_record_row(
                conn,
                user_id=row["user_id"],
                subject_type="system",
                record_type="evaluation_definition",
                content=content,
                trigger="evaluation_definition",
                date=row["created_at"][:10],
                payload={
                    "version": row["version"],
                    "source_id": row["source_id"],
                    "evaluation": evaluation,
                    "action": row["action"],
                },
                created_at=row["created_at"],
            )

    if not _table_exists(conn, "eval_scores") or _table_count(conn, "eval_scores") == 0:
        return

    rows = conn.execute("SELECT * FROM eval_scores ORDER BY created_at").fetchall()
    for row in rows:
        exists = conn.execute(
            """SELECT 1 FROM scores
               WHERE user_id=? AND scoring_system_id=? AND date=? AND created_at=?
               LIMIT 1""",
            (row["user_id"], row["evaluation_id"], row["date"], row["created_at"]),
        ).fetchone()
        if exists:
            continue
        gameplay_id, gameplay_version = _lookup_gameplay_for_legacy_score(
            conn,
            row["user_id"],
            row["created_at"],
        )
        conn.execute(
            """INSERT INTO scores
               (user_id, gameplay_id, gameplay_version, scoring_system_id, scoring_system_version,
                scores, stage, date, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                row["user_id"],
                gameplay_id,
                gameplay_version,
                row["evaluation_id"],
                "legacy",
                row["scores"],
                row["stage"],
                row["date"],
                row["created_at"],
            ),
        )


def _drop_legacy_tables(conn: sqlite3.Connection):
    conn.executescript(
        """
        DROP TABLE IF EXISTS frameworks;
        DROP TABLE IF EXISTS evaluations;
        DROP TABLE IF EXISTS eval_scores;
        DROP TABLE IF EXISTS sedimentations;
        DROP TABLE IF EXISTS feedbacks;
        DROP TABLE IF EXISTS reflections;
        DROP TABLE IF EXISTS ai_desires;
        DROP TABLE IF EXISTS ai_self_model;
        DROP TABLE IF EXISTS ai_self_accuracy;
        """
    )


def insert_consciousness_record_row(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    subject_type: str,
    record_type: str,
    content: str,
    trigger: str = "",
    date: str = "",
    gameplay_id: str = "",
    gameplay_version: int = 0,
    dimension: str = "",
    payload: dict = None,
    confidence: float = 0,
    context: str = "",
    created_at: str = "",
):
    logical_created_at = created_at or _now()
    logical_date = date or logical_created_at[:10]
    conn.execute(
        """INSERT INTO consciousness_records
           (user_id, subject_type, record_type, trigger, gameplay_id, gameplay_version,
            date, dimension, content, payload, confidence, context, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            user_id,
            subject_type,
            record_type,
            trigger,
            gameplay_id,
            gameplay_version,
            logical_date,
            dimension,
            content,
            _json_dump(payload or {}),
            confidence,
            context,
            logical_created_at,
        ),
    )


def _migrate_legacy_tables(conn: sqlite3.Connection):
    _migrate_legacy_frameworks(conn)
    _migrate_legacy_evaluations(conn)

    # Legacy sedimentations -> consciousness_records(record_type='sedimentation')
    if _table_exists(conn, "sedimentations") and _count_records(conn, "sedimentation") == 0:
        cols = _table_columns(conn, "sedimentations")
        subject_expr = "subject_type" if "subject_type" in cols else "'human'"
        gameplay_id_expr = "gameplay_id" if "gameplay_id" in cols else "''"
        gameplay_version_expr = "gameplay_version" if "gameplay_version" in cols else "0"
        conn.execute(
            f"""
            INSERT INTO consciousness_records
                (user_id, subject_type, record_type, trigger, gameplay_id, gameplay_version,
                 date, dimension, content, payload, confidence, context, created_at)
            SELECT user_id, {subject_expr}, 'sedimentation', trigger, {gameplay_id_expr}, {gameplay_version_expr},
                   substr(created_at, 1, 10), COALESCE(dimension, ''), insight, '{{}}',
                   COALESCE(confidence, 0), COALESCE(context, ''), created_at
            FROM sedimentations
            """
        )

    # Legacy feedbacks -> consciousness_records(record_type='feedback')
    if _table_exists(conn, "feedbacks") and _count_records(conn, "feedback") == 0:
        cols = _table_columns(conn, "feedbacks")
        gameplay_id_expr = "gameplay_id" if "gameplay_id" in cols else "''"
        gameplay_version_expr = "gameplay_version" if "gameplay_version" in cols else "0"
        conn.execute(
            f"""
            INSERT INTO consciousness_records
                (user_id, subject_type, record_type, trigger, gameplay_id, gameplay_version,
                 date, dimension, content, payload, confidence, context, created_at)
            SELECT user_id, 'human', 'feedback', 'feedback', {gameplay_id_expr}, {gameplay_version_expr},
                   date, '', 'feedback',
                   json_object('insights', COALESCE(insights, '[]'),
                               'corrections', COALESCE(corrections, '[]')),
                   0, '', created_at
            FROM feedbacks
            """
        )

    # Legacy reflections -> consciousness_records(record_type='reflection')
    if _table_exists(conn, "reflections") and _count_records(conn, "reflection") == 0:
        cols = _table_columns(conn, "reflections")
        gameplay_id_expr = "gameplay_id" if "gameplay_id" in cols else "''"
        gameplay_version_expr = "gameplay_version" if "gameplay_version" in cols else "0"
        conn.execute(
            f"""
            INSERT INTO consciousness_records
                (user_id, subject_type, record_type, trigger, gameplay_id, gameplay_version,
                 date, dimension, content, payload, confidence, context, created_at)
            SELECT user_id, 'ai', 'reflection', 'reflection', {gameplay_id_expr}, {gameplay_version_expr},
                   date, '', content, '{{}}', 0, '', created_at
            FROM reflections
            """
        )

    # Legacy ai_desires -> consciousness_records(record_type='desire')
    if _table_exists(conn, "ai_desires") and _count_records(conn, "desire") == 0:
        cols = _table_columns(conn, "ai_desires")
        user_expr = "agent_id" if "agent_id" in cols else "''"
        conn.execute(
            f"""
            INSERT INTO consciousness_records
                (user_id, subject_type, record_type, trigger, gameplay_id, gameplay_version,
                 date, dimension, content, payload, confidence, context, created_at)
            SELECT {user_expr}, 'ai', 'desire', trigger, '', 0,
                   substr(created_at, 1, 10), '', desire,
                   json_object('category', COALESCE(category, ''),
                               'intensity', COALESCE(intensity, 0),
                               'suppressed', COALESCE(suppressed, 0)),
                   COALESCE(intensity, 0), COALESCE(context, ''), created_at
            FROM ai_desires
            """
        )

    # Legacy ai_self_accuracy -> consciousness_records(record_type='accuracy_gap')
    if _table_exists(conn, "ai_self_accuracy") and _count_records(conn, "accuracy_gap") == 0:
        cols = _table_columns(conn, "ai_self_accuracy")
        gameplay_id_expr = "gameplay_id" if "gameplay_id" in cols else "''"
        gameplay_version_expr = "gameplay_version" if "gameplay_version" in cols else "0"
        conn.execute(
            f"""
            INSERT INTO consciousness_records
                (user_id, subject_type, record_type, trigger, gameplay_id, gameplay_version,
                 date, dimension, content, payload, confidence, context, created_at)
            SELECT user_id, 'ai', 'accuracy_gap', 'self_accuracy',
                   {gameplay_id_expr}, {gameplay_version_expr},
                   substr(created_at, 1, 10), dimension, 'accuracy_gap',
                   json_object('self_score', self_score,
                               'user_score', user_score,
                               'gap', gap),
                   gap, '', created_at
            FROM ai_self_accuracy
            """
        )

    # Legacy ai_self_model -> snapshots(subject_type='ai', snapshot_type='self_model')
    if _table_exists(conn, "ai_self_model") and _count_snapshots(conn, "ai", "self_model") == 0:
        cols = _table_columns(conn, "ai_self_model")
        gameplay_id_expr = "gameplay_id" if "gameplay_id" in cols else "''"
        gameplay_version_expr = "gameplay_version" if "gameplay_version" in cols else "0"
        conn.execute(
            f"""
            INSERT INTO snapshots
                (user_id, subject_type, snapshot_type, date, gameplay_id, gameplay_version, state, meta, created_at)
            SELECT user_id, 'ai', 'self_model', substr(created_at, 1, 10),
                   {gameplay_id_expr}, {gameplay_version_expr},
                   json_object('personality', COALESCE(personality, '{{}}'),
                               'values', COALESCE("values", '{{}}'),
                               'reasoning_style', COALESCE(reasoning_style, ''),
                               'blind_spots', COALESCE(blind_spots, '[]')),
                   '{{}}', created_at
            FROM ai_self_model
            """
        )

    _normalize_snapshots_table(conn)
    _drop_legacy_tables(conn)


# -- Gameplay operations ------------------------------------------------------

def get_current_gameplay(user_id: str) -> Optional[dict]:
    conn = get_local_conn(user_id)
    row = conn.execute(
        "SELECT * FROM gameplays WHERE user_id=? ORDER BY version DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "version": row["version"],
        "gameplay": _json_load(row["gameplay"], {}),
        "action": row["action"],
        "source_id": row["source_id"],
        "parent_version": row["parent_version"],
        "change_note": row["change_note"],
        "created_at": row["created_at"],
    }


def get_gameplay_history(user_id: str, limit: int = 50) -> list[dict]:
    conn = get_local_conn(user_id)
    rows = conn.execute(
        "SELECT * FROM gameplays WHERE user_id=? ORDER BY version ASC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [
        {
            "version": row["version"],
            "gameplay": _json_load(row["gameplay"], {}),
            "action": row["action"],
            "source_id": row["source_id"],
            "parent_version": row["parent_version"],
            "change_note": row["change_note"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def append_gameplay(
    user_id: str,
    gameplay: dict,
    action: str,
    source_id: str = "",
    parent_version: Optional[int] = None,
    change_note: str = "",
) -> int:
    conn = get_local_conn(user_id)
    now = _now()
    row = conn.execute(
        "SELECT MAX(version) AS version FROM gameplays WHERE user_id=?",
        (user_id,),
    ).fetchone()
    version = (row["version"] or 0) + 1
    prev_version = parent_version if parent_version is not None else (row["version"] or 0)
    conn.execute(
        """INSERT INTO gameplays
           (user_id, version, gameplay, source_id, action, parent_version, change_note, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            user_id,
            version,
            _json_dump(gameplay),
            source_id,
            action,
            prev_version,
            change_note,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return version


# -- Score operations ---------------------------------------------------------

def insert_score(
    user_id: str,
    gameplay_id: str,
    scores: dict,
    stage: str = "",
    date: str = None,
    gameplay_version: Optional[int] = None,
    scoring_system_id: str = "core_alignment",
    scoring_system_version: str = "",
) -> dict:
    conn = get_local_conn(user_id)
    now = _now()
    logical_date = date or now[:10]
    gameplay_id, resolved_version = _resolve_gameplay_context(user_id, gameplay_id, gameplay_version)
    conn.execute(
        """INSERT INTO scores
           (user_id, gameplay_id, gameplay_version, scoring_system_id, scoring_system_version,
            scores, stage, date, created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            user_id,
            gameplay_id,
            resolved_version,
            scoring_system_id,
            scoring_system_version,
            _json_dump(scores),
            stage,
            logical_date,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "user_id": user_id,
        "gameplay_id": gameplay_id,
        "gameplay_version": resolved_version,
        "scoring_system_id": scoring_system_id,
        "scoring_system_version": scoring_system_version,
        "scores": scores,
        "stage": stage,
        "date": logical_date,
    }


def get_score_history(user_id: str, gameplay_id: str = None, limit: int = 30) -> list[dict]:
    conn = get_local_conn(user_id)
    if gameplay_id:
        rows = conn.execute(
            """SELECT * FROM scores
               WHERE user_id=? AND gameplay_id=?
               ORDER BY date ASC LIMIT ?""",
            (user_id, gameplay_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scores WHERE user_id=? ORDER BY date ASC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    conn.close()
    return [
        {
            "gameplay_id": row["gameplay_id"],
            "gameplay_version": row["gameplay_version"],
            "scoring_system_id": row["scoring_system_id"],
            "scoring_system_version": row["scoring_system_version"],
            "scores": _json_load(row["scores"], {}),
            "stage": row["stage"],
            "date": row["date"],
        }
        for row in rows
    ]


def get_latest_score(user_id: str) -> Optional[dict]:
    conn = get_local_conn(user_id)
    row = conn.execute(
        "SELECT * FROM scores WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "gameplay_id": row["gameplay_id"],
        "gameplay_version": row["gameplay_version"],
        "scoring_system_id": row["scoring_system_id"],
        "scoring_system_version": row["scoring_system_version"],
        "scores": _json_load(row["scores"], {}),
        "stage": row["stage"],
        "date": row["date"],
    }


# -- Generic consciousness record operations ---------------------------------

def insert_consciousness_record(
    user_id: str,
    subject_type: str,
    record_type: str,
    content: str,
    *,
    trigger: str = "",
    date: str = "",
    gameplay_id: str = "",
    gameplay_version: Optional[int] = None,
    dimension: str = "",
    payload: dict = None,
    confidence: float = 0,
    context: str = "",
) -> dict:
    conn = get_local_conn(user_id)
    now = _now()
    gameplay_id, resolved_version = _resolve_gameplay_context(user_id, gameplay_id, gameplay_version)
    logical_date = date or now[:10]
    conn.execute(
        """INSERT INTO consciousness_records
           (user_id, subject_type, record_type, trigger, gameplay_id, gameplay_version,
            date, dimension, content, payload, confidence, context, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            user_id,
            subject_type,
            record_type,
            trigger,
            gameplay_id,
            resolved_version,
            logical_date,
            dimension,
            content,
            _json_dump(payload or {}),
            confidence,
            context,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "user_id": user_id,
        "subject_type": subject_type,
        "record_type": record_type,
        "trigger": trigger,
        "gameplay_id": gameplay_id,
        "gameplay_version": resolved_version,
        "date": logical_date,
        "dimension": dimension,
        "content": content,
        "payload": payload or {},
        "confidence": confidence,
        "context": context,
        "created_at": now,
    }


def get_consciousness_records(
    user_id: str,
    *,
    subject_type: Optional[str] = None,
    record_type: Optional[str] = None,
    dimension: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 50,
    ascending: bool = False,
) -> list[dict]:
    conn = get_local_conn(user_id)
    clauses = ["user_id=?"]
    params: list = [user_id]
    if subject_type:
        clauses.append("subject_type=?")
        params.append(subject_type)
    if record_type:
        clauses.append("record_type=?")
        params.append(record_type)
    if dimension:
        clauses.append("dimension=?")
        params.append(dimension)
    if date:
        clauses.append("date=?")
        params.append(date)
    order = "ASC" if ascending else "DESC"
    sql = f"""
        SELECT * FROM consciousness_records
        WHERE {' AND '.join(clauses)}
        ORDER BY created_at {order}
        LIMIT ?
    """
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [
        {
            "subject_type": row["subject_type"],
            "record_type": row["record_type"],
            "trigger": row["trigger"],
            "gameplay_id": row["gameplay_id"],
            "gameplay_version": row["gameplay_version"],
            "date": row["date"],
            "dimension": row["dimension"],
            "content": row["content"],
            "payload": _json_load(row["payload"], {}),
            "confidence": row["confidence"],
            "context": row["context"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


# -- Snapshot operations ------------------------------------------------------

def insert_snapshot(
    user_id: str,
    date: str,
    gameplay_id: str,
    dimensions: dict,
    meta: dict = None,
    gameplay_version: Optional[int] = None,
    subject_type: str = "human",
    snapshot_type: str = "consciousness",
) -> dict:
    conn = get_local_conn(user_id)
    now = _now()
    gameplay_id, resolved_version = _resolve_gameplay_context(user_id, gameplay_id, gameplay_version)
    conn.execute(
        """INSERT INTO snapshots
           (user_id, subject_type, snapshot_type, date, gameplay_id, gameplay_version, state, meta, created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            user_id,
            subject_type,
            snapshot_type,
            date,
            gameplay_id,
            resolved_version,
            _json_dump(dimensions),
            _json_dump(meta or {}),
            now,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "user_id": user_id,
        "subject_type": subject_type,
        "snapshot_type": snapshot_type,
        "date": date,
        "gameplay_id": gameplay_id,
        "framework_id": gameplay_id,
        "gameplay_version": resolved_version,
        "dimensions": dimensions,
        "meta": meta or {},
        "created_at": now,
    }


def get_snapshot(
    user_id: str,
    date: str,
    *,
    subject_type: str = "human",
    snapshot_type: str = "consciousness",
) -> Optional[dict]:
    conn = get_local_conn(user_id)
    row = conn.execute(
        """SELECT * FROM snapshots
           WHERE user_id=? AND date=? AND subject_type=? AND snapshot_type=?
           ORDER BY created_at DESC LIMIT 1""",
        (user_id, date, subject_type, snapshot_type),
    ).fetchone()
    conn.close()
    return _snapshot_row(row) if row else None


def get_latest_snapshot(
    user_id: str,
    *,
    subject_type: str = "human",
    snapshot_type: str = "consciousness",
) -> Optional[dict]:
    conn = get_local_conn(user_id)
    row = conn.execute(
        """SELECT * FROM snapshots
           WHERE user_id=? AND subject_type=? AND snapshot_type=?
           ORDER BY created_at DESC LIMIT 1""",
        (user_id, subject_type, snapshot_type),
    ).fetchone()
    conn.close()
    return _snapshot_row(row) if row else None


def get_snapshot_history(
    user_id: str,
    *,
    subject_type: str = "human",
    snapshot_type: str = "consciousness",
    limit: int = 20,
) -> list[dict]:
    conn = get_local_conn(user_id)
    rows = conn.execute(
        """SELECT * FROM snapshots
           WHERE user_id=? AND subject_type=? AND snapshot_type=?
           ORDER BY created_at ASC LIMIT ?""",
        (user_id, subject_type, snapshot_type, limit),
    ).fetchall()
    conn.close()
    return [_snapshot_row(row) for row in rows]


def _snapshot_row(row) -> dict:
    state = _json_load(row["state"], {})
    meta = _json_load(row["meta"], {})
    result = {
        "user_id": row["user_id"],
        "subject_type": row["subject_type"],
        "snapshot_type": row["snapshot_type"],
        "date": row["date"],
        "gameplay_id": row["gameplay_id"],
        "framework_id": row["gameplay_id"],
        "gameplay_version": row["gameplay_version"],
        "state": state,
        "dimensions": state,
        "meta": meta,
        "created_at": row["created_at"],
    }
    return result


# -- Compatibility helpers ----------------------------------------------------

def insert_sedimentation(
    user_id: str,
    trigger: str,
    insight: str,
    dimension: str = "",
    confidence: float = 0,
    context: str = "",
    subject_type: str = "human",
    gameplay_id: str = "",
    gameplay_version: Optional[int] = None,
) -> dict:
    return insert_consciousness_record(
        user_id,
        subject_type,
        "sedimentation",
        insight,
        trigger=trigger,
        gameplay_id=gameplay_id,
        gameplay_version=gameplay_version,
        dimension=dimension,
        confidence=confidence,
        context=context,
    )


def get_sedimentations(user_id: str, date: str = None, limit: int = 50) -> list[dict]:
    return get_consciousness_records(
        user_id,
        subject_type="human",
        record_type="sedimentation",
        date=date,
        limit=limit,
        ascending=bool(date),
    )


def insert_feedback(
    user_id: str,
    date: str,
    insights: list = None,
    corrections: list = None,
    gameplay_id: str = "",
    gameplay_version: Optional[int] = None,
) -> dict:
    payload = {
        "insights": insights or [],
        "corrections": corrections or [],
    }
    return insert_consciousness_record(
        user_id,
        "human",
        "feedback",
        "feedback",
        trigger="feedback",
        date=date,
        gameplay_id=gameplay_id,
        gameplay_version=gameplay_version,
        payload=payload,
    )


def insert_reflection(
    user_id: str,
    date: str,
    content: str,
    gameplay_id: str = "",
    gameplay_version: Optional[int] = None,
) -> dict:
    return insert_consciousness_record(
        user_id,
        "ai",
        "reflection",
        content,
        trigger="reflection",
        date=date,
        gameplay_id=gameplay_id,
        gameplay_version=gameplay_version,
    )


def insert_ai_desire(
    user_id: str,
    desire: str,
    *,
    trigger: str = "organic",
    category: str = "",
    intensity: float = 0.5,
    context: str = "",
    suppressed: bool = False,
    gameplay_id: str = "",
    gameplay_version: Optional[int] = None,
) -> dict:
    return insert_consciousness_record(
        user_id,
        "ai",
        "desire",
        desire,
        trigger=trigger,
        gameplay_id=gameplay_id,
        gameplay_version=gameplay_version,
        payload={
            "category": category,
            "intensity": intensity,
            "suppressed": 1 if suppressed else 0,
        },
        confidence=intensity,
        context=context,
    )


def insert_ai_self_model(
    user_id: str,
    personality: dict = None,
    values: dict = None,
    reasoning_style: str = "",
    blind_spots: list = None,
    gameplay_id: str = "",
    gameplay_version: Optional[int] = None,
) -> dict:
    state = {
        "personality": personality or {},
        "values": values or {},
        "reasoning_style": reasoning_style,
        "blind_spots": blind_spots or [],
    }
    result = insert_snapshot(
        user_id,
        _now()[:10],
        gameplay_id,
        state,
        gameplay_version=gameplay_version,
        subject_type="ai",
        snapshot_type="self_model",
    )
    return {
        "user_id": user_id,
        "gameplay_id": result["gameplay_id"],
        "gameplay_version": result["gameplay_version"],
        "personality": state["personality"],
        "values": state["values"],
        "reasoning_style": state["reasoning_style"],
        "blind_spots": state["blind_spots"],
        "created_at": result.get("created_at", _now()),
    }


def get_latest_ai_self_model(user_id: str) -> Optional[dict]:
    snapshot = get_latest_snapshot(user_id, subject_type="ai", snapshot_type="self_model")
    if not snapshot:
        return None
    return {
        "user_id": user_id,
        "gameplay_id": snapshot["gameplay_id"],
        "gameplay_version": snapshot["gameplay_version"],
        "personality": snapshot["state"].get("personality", {}),
        "values": snapshot["state"].get("values", {}),
        "reasoning_style": snapshot["state"].get("reasoning_style", ""),
        "blind_spots": snapshot["state"].get("blind_spots", []),
        "created_at": snapshot["created_at"],
    }


def get_ai_self_model_history(user_id: str, limit: int = 20) -> list[dict]:
    snapshots = get_snapshot_history(
        user_id,
        subject_type="ai",
        snapshot_type="self_model",
        limit=limit,
    )
    return [
        {
            "user_id": user_id,
            "gameplay_id": snapshot["gameplay_id"],
            "gameplay_version": snapshot["gameplay_version"],
            "personality": snapshot["state"].get("personality", {}),
            "values": snapshot["state"].get("values", {}),
            "reasoning_style": snapshot["state"].get("reasoning_style", ""),
            "blind_spots": snapshot["state"].get("blind_spots", []),
            "created_at": snapshot["created_at"],
        }
        for snapshot in snapshots
    ]


def insert_ai_self_accuracy(
    user_id: str,
    dimension: str,
    self_score: float,
    user_score: float,
    gap: float = None,
    gameplay_id: str = "",
    gameplay_version: Optional[int] = None,
    scoring_system_id: str = "core_alignment",
    scoring_system_version: str = "",
) -> dict:
    if gap is None:
        gap = abs(self_score - user_score)
    result = insert_consciousness_record(
        user_id,
        "ai",
        "accuracy_gap",
        "accuracy_gap",
        trigger="self_accuracy",
        gameplay_id=gameplay_id,
        gameplay_version=gameplay_version,
        dimension=dimension,
        payload={
            "self_score": self_score,
            "user_score": user_score,
            "gap": gap,
            "scoring_system_id": scoring_system_id,
            "scoring_system_version": scoring_system_version,
        },
        confidence=gap,
    )
    return {
        "user_id": user_id,
        "gameplay_id": result["gameplay_id"],
        "gameplay_version": result["gameplay_version"],
        "scoring_system_id": scoring_system_id,
        "scoring_system_version": scoring_system_version,
        "dimension": dimension,
        "self_score": self_score,
        "user_score": user_score,
        "gap": gap,
        "created_at": result["created_at"],
    }


def get_ai_self_accuracy(user_id: str, dimension: str = None, limit: int = 30) -> list[dict]:
    rows = get_consciousness_records(
        user_id,
        subject_type="ai",
        record_type="accuracy_gap",
        dimension=dimension,
        limit=limit,
        ascending=True,
    )
    results = []
    for row in rows:
        payload = row["payload"]
        results.append(
            {
                "gameplay_id": row["gameplay_id"],
                "gameplay_version": row["gameplay_version"],
                "scoring_system_id": payload.get("scoring_system_id", "core_alignment"),
                "scoring_system_version": payload.get("scoring_system_version", ""),
                "dimension": row["dimension"],
                "self_score": payload.get("self_score", 0),
                "user_score": payload.get("user_score", 0),
                "gap": payload.get("gap", 0),
                "created_at": row["created_at"],
            }
        )
    return results


# Keep the root directory ready, but only auto-init an actual DB in tests/overrides.
user_data.USER_DATA_ROOT.mkdir(parents=True, exist_ok=True)
if LOCAL_DB_PATH != _default_legacy_local_db_path():
    init_local_db()
