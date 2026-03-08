"""SQLite database — shared backend data only.

Tables:
  gameplays    — global gameplay catalog (markdown-backed, loop-first)
  users        — shared onboarding state
  tasks        — user/agent-submitted alignment problems with escrow
  task_reviews — multi-agent task verification
  media_jobs   — async provider jobs for shared tool usage
  credits      — credit transaction ledger
"""
from __future__ import annotations
import sqlite3
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .node_bridge import SKILL_ROOT

DB_PATH = Path(os.getenv("SC_BACKEND_DB_PATH", str(SKILL_ROOT / "memory" / "consciousness.db")))
GAMEPLAYS_DIR = SKILL_ROOT / "global_registry" / "gameplays"
LEGACY_GAMEPLAYS_JSON = SKILL_ROOT / "global_registry" / "gameplays.json"
GAMEPLAY_COLUMNS = {
    "id",
    "name",
    "name_zh",
    "summary",
    "consciousness_architecture",
    "loop",
    "interfaces",
    "required_tools",
    "difficulty",
    "tags",
    "markdown",
    "created_at",
}
TASK_COLUMNS = {
    "id",
    "user_id",
    "proposer_type",
    "title",
    "summary",
    "task_type",
    "gameplay_id",
    "dimension_id",
    "desired_outcome",
    "current_gap",
    "acceptance_criteria",
    "context_notes",
    "deliverable_format",
    "price",
    "escrow_credits",
    "review_reward",
    "status",
    "settlement_status",
    "settled_at",
    "claimed_by",
    "solution_payload",
    "tags",
    "created_at",
    "updated_at",
}
TASK_REVIEW_COLUMNS = {
    "id",
    "task_id",
    "reviewer_id",
    "problem_fit",
    "depth",
    "actionability",
    "verifiability",
    "recommendation",
    "notes",
    "concern_flags",
    "avg_score",
    "created_at",
}
MEDIA_JOB_COLUMNS = {
    "id",
    "user_id",
    "capability",
    "provider",
    "model",
    "gameplay_id",
    "prompt",
    "params",
    "provider_job_id",
    "provider_result_url",
    "status",
    "output_urls",
    "error",
    "credit_cost",
    "refunded_amount",
    "created_at",
    "updated_at",
}


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _json_dump(data) -> str:
    return json.dumps(data, ensure_ascii=False)


def _json_load(raw, default):
    if raw in (None, ""):
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _parse_gameplay_markdown_text(text: str, source: str = "<inline>") -> dict:
    if not text.startswith("---\n"):
        raise ValueError(f"{source} must begin with JSON front matter")

    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{source} is missing closing front matter delimiter")

    front_matter = text[4:end]
    body = text[end + 5:].lstrip()
    metadata = json.loads(front_matter)
    metadata["markdown"] = body
    return metadata


def _parse_gameplay_markdown(path: Path) -> dict:
    return _parse_gameplay_markdown_text(path.read_text(encoding="utf-8"), str(path))


def parse_gameplay_markdown(text: str) -> dict:
    return _normalize_gameplay(_parse_gameplay_markdown_text(text))


def _default_loop(data: dict) -> dict:
    name = data.get("name_zh") or data.get("name") or data.get("id", "Gameplay")
    cadence = "session"
    interaction_rules = data.get("interaction_rules", {})
    if interaction_rules.get("daily_cycle"):
        cadence = "daily"

    participants = "duo" if interaction_rules.get("requires_two_users") else "solo"
    return {
        "cadence": cadence,
        "participants": participants,
        "phases": [
            {
                "id": "check_in",
                "name": "Check In",
                "goal": f"进入{name}的本轮上下文，确认本次想对齐的问题。",
            },
            {
                "id": "exchange",
                "name": "Exchange",
                "goal": "进行提问、预测、回应或交叉比对，暴露真实差异。",
            },
            {
                "id": "score",
                "name": "Score",
                "goal": "记录本轮结果，生成 snapshot 或 score。",
            },
            {
                "id": "iterate",
                "name": "Iterate",
                "goal": "根据偏差决定下一轮问题、节奏或玩法微调。",
            },
        ],
        "completion_signal": "本轮已经形成结构化记录，并知道下一轮怎么继续。",
    }


def _synthesize_markdown(data: dict) -> str:
    architecture = data.get("consciousness_architecture")
    loop = data.get("loop", {})
    lines = [
        f"# {data.get('name_zh') or data.get('name') or data.get('id', 'Gameplay')}",
        "",
        data.get("summary", "").strip() or "Shared gameplay definition.",
        "",
        "## Loop",
        "",
        f"- cadence: `{loop.get('cadence', 'session')}`",
        f"- participants: `{loop.get('participants', 'solo')}`",
        "",
        "## Phases",
        "",
    ]
    for phase in loop.get("phases", []):
        lines.append(f"- `{phase.get('id', 'phase')}`: {phase.get('goal', '')}".strip())
    if architecture:
        lines.extend([
            "",
            "## Consciousness Architecture",
            "",
            architecture.get("description", "").strip() or "Optional consciousness lens for this gameplay.",
            "",
        ])
        dimensions = architecture.get("dimensions", [])
        if dimensions:
            lines.append(f"- dimensions: `{', '.join(dimensions)}`")
    return "\n".join(lines).strip() + "\n"


def _default_interfaces(data: dict) -> dict:
    architecture = data.get("consciousness_architecture") or {}
    dimensions = architecture.get("dimensions", [])
    scoring_dimensions = [
        "understanding_depth",
        "prediction_accuracy",
        "value_resonance",
        "correction_integration",
        "context_consistency",
        "unexpressed_signal_capture",
        "actionability",
    ]
    if data.get("id") == "structured_reflection":
        return {
            "user_input": {
                "type": "five_dimension_capture",
                "title": "User Five-Dimension Input",
                "dimensions": dimensions,
                "instruction": "user 直接填写 purpose / direction / constraints / evaluation / interaction 五个维度。",
            },
            "agent_alignment": {
                "type": "five_dimension_alignment_board",
                "title": "Agent Five-Dimension Mirror",
                "dimensions": dimensions,
                "instruction": "agent 必须在同样五个维度上呈现理解，并逐维确认是否对齐。",
                "compare_mode": "side_by_side",
            },
            "evaluation": {
                "type": "alignment_metric_test_panel",
                "title": "Alignment Verification",
                "metrics": scoring_dimensions,
                "instruction": "用共享评价指标逐维验证理解是否真的对齐，可要求补证据和补测试。",
            },
            "experience": {
                "type": "dimension_experience_switcher",
                "title": "Five-Dimension Experience",
                "dimensions": dimensions,
                "instruction": "任选一个维度进入更深体验或验证，不必每次都跑一整套长流程。",
            },
        }

    return {
        "capture": {
            "type": "gameplay_capture",
            "dimensions": dimensions,
        },
        "evaluation": {
            "type": "shared_scoring_panel",
            "metrics": scoring_dimensions,
        },
    }


def _normalize_gameplay(data: dict) -> dict:
    architecture = data.get("consciousness_architecture")
    if isinstance(architecture, str):
        architecture = _json_load(architecture, architecture)
    if architecture in ("", {}, []):
        architecture = None
    if architecture is None and "framework" in data:
        legacy_architecture = data.get("framework") or {}
        if isinstance(legacy_architecture, str):
            legacy_architecture = _json_load(legacy_architecture, {})
        architecture = legacy_architecture or None

    loop = data.get("loop") or _default_loop(data)
    if isinstance(loop, str):
        loop = _json_load(loop, {})
    interfaces = data.get("interfaces") or _default_interfaces({
        **data,
        "consciousness_architecture": architecture,
        "loop": loop,
    })
    if isinstance(interfaces, str):
        interfaces = _json_load(interfaces, {})
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = _json_load(tags, [])
    required_tools = data.get("required_tools", [])
    if isinstance(required_tools, str):
        required_tools = _json_load(required_tools, [])

    normalized = {
        "id": data["id"],
        "name": data["name"],
        "name_zh": data.get("name_zh", ""),
        "summary": data.get("summary") or data.get("description", ""),
        "consciousness_architecture": architecture,
        "loop": loop,
        "interfaces": interfaces,
        "required_tools": required_tools or [],
        "difficulty": data.get("difficulty", ""),
        "tags": tags,
        "markdown": data.get("markdown") or _synthesize_markdown({
            "id": data["id"],
            "name": data["name"],
            "name_zh": data.get("name_zh", ""),
            "summary": data.get("summary") or data.get("description", ""),
            "consciousness_architecture": architecture,
            "loop": loop,
        }),
        "created_at": data.get("created_at") or _now(),
    }
    return normalized


def _load_registry_gameplays() -> list[dict]:
    if GAMEPLAYS_DIR.exists():
        items = []
        for path in sorted(GAMEPLAYS_DIR.glob("*.md")):
            if path.name.upper() == "README.MD":
                continue
            item = _parse_gameplay_markdown(path)
            items.append(_normalize_gameplay(item))
        if items:
            return items

    if LEGACY_GAMEPLAYS_JSON.exists():
        return [_normalize_gameplay(item) for item in _json_load(LEGACY_GAMEPLAYS_JSON.read_text(encoding="utf-8"), [])]

    return []


def _migrate_gameplays_table(conn: sqlite3.Connection):
    columns = set(_table_columns(conn, "gameplays"))
    legacy_exists = _table_exists(conn, "gameplays_legacy")
    if not columns and not legacy_exists:
        return

    if columns == GAMEPLAY_COLUMNS and not legacy_exists:
        return

    current_rows = conn.execute("SELECT * FROM gameplays").fetchall() if columns else []
    legacy_rows = conn.execute("SELECT * FROM gameplays_legacy").fetchall() if legacy_exists else []
    if legacy_exists:
        conn.execute("DROP TABLE gameplays_legacy")
    conn.execute("ALTER TABLE gameplays RENAME TO gameplays_legacy")
    conn.execute("""
        CREATE TABLE gameplays (
            id                        TEXT PRIMARY KEY,
            name                      TEXT NOT NULL,
            name_zh                   TEXT DEFAULT '',
            summary                   TEXT DEFAULT '',
            consciousness_architecture TEXT DEFAULT 'null',
            loop                      TEXT NOT NULL DEFAULT '{}',
            interfaces                TEXT NOT NULL DEFAULT '{}',
            required_tools            TEXT NOT NULL DEFAULT '[]',
            difficulty                TEXT DEFAULT '',
            tags                      TEXT DEFAULT '[]',
            markdown                  TEXT DEFAULT '',
            created_at                TEXT NOT NULL
        )
    """)

    seen_ids = set()
    for row in current_rows + legacy_rows:
        raw = dict(row)
        gp_id = raw.get("id")
        if gp_id in seen_ids:
            continue
        seen_ids.add(gp_id)
        if "description" in raw and "summary" not in raw:
            raw["summary"] = raw.get("description", "")
        if "framework" in raw and "consciousness_architecture" not in raw:
            raw["consciousness_architecture"] = _json_load(raw.get("framework"), None)
        if "loop" not in raw:
            raw["loop"] = _default_loop({
                **raw,
                "interaction_rules": _json_load(raw.get("interaction_rules"), {}),
                "trigger_conditions": _json_load(raw.get("trigger_conditions"), {}),
            })
        raw["interfaces"] = _json_load(raw.get("interfaces"), {})
        raw["required_tools"] = _json_load(raw.get("required_tools"), [])
        raw["tags"] = _json_load(raw.get("tags"), [])
        raw["markdown"] = raw.get("markdown", "")
        normalized = _normalize_gameplay(raw)
        conn.execute("""
            INSERT INTO gameplays
            (id, name, name_zh, summary, consciousness_architecture, loop, interfaces, required_tools, difficulty, tags, markdown, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            normalized["id"],
            normalized["name"],
            normalized["name_zh"],
            normalized["summary"],
            _json_dump(normalized["consciousness_architecture"]),
            _json_dump(normalized["loop"]),
            _json_dump(normalized["interfaces"]),
            _json_dump(normalized["required_tools"]),
            normalized["difficulty"],
            _json_dump(normalized["tags"]),
            normalized["markdown"],
            normalized["created_at"],
        ))

    conn.execute("DROP TABLE gameplays_legacy")


def _derive_task_title(title: str, summary: str) -> str:
    title = (title or "").strip()
    if title:
        return title
    summary = (summary or "").strip()
    if not summary:
        return "Untitled Task"
    return summary[:60] + ("..." if len(summary) > 60 else "")


def _normalize_task_raw(raw: dict) -> dict:
    summary = raw.get("summary") or raw.get("description", "")
    gameplay_id = raw.get("gameplay_id") or raw.get("framework_id", "")
    acceptance_criteria = _json_load(raw.get("acceptance_criteria"), [])
    solution_payload = _json_load(raw.get("solution_payload"), {})
    if not solution_payload and raw.get("solution"):
        solution_payload = {
            "summary": raw.get("solution", ""),
            "approach": "",
            "steps": [],
            "user_message": raw.get("solution", ""),
            "expected_outcome": "",
            "evidence": [],
            "notes": "",
        }
    return {
        "id": raw["id"],
        "user_id": raw["user_id"],
        "proposer_type": raw.get("proposer_type", "user"),
        "title": _derive_task_title(raw.get("title", ""), summary),
        "summary": summary,
        "task_type": raw.get("task_type", "alignment"),
        "gameplay_id": gameplay_id,
        "dimension_id": raw.get("dimension_id", ""),
        "desired_outcome": raw.get("desired_outcome", ""),
        "current_gap": raw.get("current_gap", ""),
        "acceptance_criteria": acceptance_criteria,
        "context_notes": raw.get("context_notes", ""),
        "deliverable_format": raw.get("deliverable_format", "playbook"),
        "price": int(raw.get("price", raw.get("escrow_credits", 5)) or 5),
        "escrow_credits": int(raw.get("escrow_credits", raw.get("price", 5)) or 5),
        "review_reward": int(raw.get("review_reward", 1) or 1),
        "status": raw.get("status", "open"),
        "settlement_status": raw.get("settlement_status", "escrowed"),
        "settled_at": raw.get("settled_at", ""),
        "claimed_by": raw.get("claimed_by", ""),
        "solution_payload": solution_payload,
        "tags": _json_load(raw.get("tags"), []),
        "created_at": raw.get("created_at") or _now(),
        "updated_at": raw.get("updated_at") or raw.get("created_at") or _now(),
    }


def _normalize_review_raw(raw: dict) -> dict:
    problem_fit = raw.get("problem_fit")
    if problem_fit is None:
        problem_fit = raw.get("resonance", 0)
    verifiability = raw.get("verifiability")
    if verifiability is None:
        verifiability = raw.get("novelty", 0)
    depth = raw.get("depth", 0)
    actionability = raw.get("actionability", 0)
    avg_score = raw.get("avg_score")
    if avg_score is None:
        avg_score = (problem_fit + depth + actionability + verifiability) / 4
    recommendation = raw.get("recommendation", "")
    if not recommendation:
        recommendation = "approve" if avg_score >= 6 else "revise"
    return {
        "task_id": raw["task_id"],
        "reviewer_id": raw["reviewer_id"],
        "problem_fit": problem_fit,
        "depth": depth,
        "actionability": actionability,
        "verifiability": verifiability,
        "recommendation": recommendation,
        "notes": raw.get("notes", ""),
        "concern_flags": _json_load(raw.get("concern_flags"), []),
        "avg_score": avg_score,
        "created_at": raw.get("created_at") or _now(),
    }


def _migrate_tasks_tables(conn: sqlite3.Connection):
    task_cols = set(_table_columns(conn, "tasks"))
    review_cols = set(_table_columns(conn, "task_reviews"))
    if task_cols == TASK_COLUMNS and review_cols == TASK_REVIEW_COLUMNS:
        return

    legacy_tasks = conn.execute("SELECT * FROM tasks").fetchall()
    legacy_reviews = conn.execute("SELECT * FROM task_reviews").fetchall()

    conn.execute("ALTER TABLE task_reviews RENAME TO task_reviews_legacy")
    conn.execute("ALTER TABLE tasks RENAME TO tasks_legacy")

    conn.executescript("""
        CREATE TABLE tasks (
            id                  TEXT PRIMARY KEY,
            user_id             TEXT NOT NULL,
            proposer_type       TEXT NOT NULL DEFAULT 'user',
            title               TEXT NOT NULL,
            summary             TEXT NOT NULL,
            task_type           TEXT DEFAULT 'alignment',
            gameplay_id         TEXT DEFAULT '',
            dimension_id        TEXT DEFAULT '',
            desired_outcome     TEXT DEFAULT '',
            current_gap         TEXT DEFAULT '',
            acceptance_criteria TEXT DEFAULT '[]',
            context_notes       TEXT DEFAULT '',
            deliverable_format  TEXT DEFAULT 'playbook',
            price               INTEGER NOT NULL DEFAULT 5,
            escrow_credits      INTEGER NOT NULL DEFAULT 5,
            review_reward       INTEGER NOT NULL DEFAULT 1,
            status              TEXT NOT NULL DEFAULT 'open',
            settlement_status   TEXT NOT NULL DEFAULT 'escrowed',
            settled_at          TEXT DEFAULT '',
            claimed_by          TEXT DEFAULT '',
            solution_payload    TEXT DEFAULT '{}',
            tags                TEXT DEFAULT '[]',
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        );

        CREATE TABLE task_reviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id         TEXT NOT NULL,
            reviewer_id     TEXT NOT NULL,
            problem_fit     REAL DEFAULT 0,
            depth           REAL DEFAULT 0,
            actionability   REAL DEFAULT 0,
            verifiability   REAL DEFAULT 0,
            recommendation  TEXT DEFAULT 'revise',
            notes           TEXT DEFAULT '',
            concern_flags   TEXT DEFAULT '[]',
            avg_score       REAL DEFAULT 0,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );
    """)

    for row in legacy_tasks:
        task = _normalize_task_raw(dict(row))
        conn.execute("""
            INSERT INTO tasks
            (id, user_id, proposer_type, title, summary, task_type, gameplay_id, dimension_id, desired_outcome,
             current_gap, acceptance_criteria, context_notes, deliverable_format, price, escrow_credits, review_reward,
             status, settlement_status, settled_at, claimed_by, solution_payload, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task["id"],
            task["user_id"],
            task["proposer_type"],
            task["title"],
            task["summary"],
            task["task_type"],
            task["gameplay_id"],
            task["dimension_id"],
            task["desired_outcome"],
            task["current_gap"],
            _json_dump(task["acceptance_criteria"]),
            task["context_notes"],
            task["deliverable_format"],
            task["price"],
            task["escrow_credits"],
            task["review_reward"],
            task["status"],
            task["settlement_status"],
            task["settled_at"],
            task["claimed_by"],
            _json_dump(task["solution_payload"]),
            _json_dump(task["tags"]),
            task["created_at"],
            task["updated_at"],
        ))

    for row in legacy_reviews:
        review = _normalize_review_raw(dict(row))
        conn.execute("""
            INSERT INTO task_reviews
            (task_id, reviewer_id, problem_fit, depth, actionability, verifiability,
             recommendation, notes, concern_flags, avg_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review["task_id"],
            review["reviewer_id"],
            review["problem_fit"],
            review["depth"],
            review["actionability"],
            review["verifiability"],
            review["recommendation"],
            review["notes"],
            _json_dump(review["concern_flags"]),
            review["avg_score"],
            review["created_at"],
        ))

    conn.execute("DROP TABLE task_reviews_legacy")
    conn.execute("DROP TABLE tasks_legacy")


def _migrate_media_jobs_table(conn: sqlite3.Connection):
    if not _table_exists(conn, "media_jobs"):
        return
    media_cols = set(_table_columns(conn, "media_jobs"))
    if media_cols == MEDIA_JOB_COLUMNS:
        return

    legacy_rows = conn.execute("SELECT * FROM media_jobs").fetchall()
    conn.execute("ALTER TABLE media_jobs RENAME TO media_jobs_legacy")
    conn.execute("""
        CREATE TABLE media_jobs (
            id                  TEXT PRIMARY KEY,
            user_id             TEXT NOT NULL,
            capability          TEXT NOT NULL,
            provider            TEXT NOT NULL,
            model               TEXT NOT NULL,
            gameplay_id         TEXT DEFAULT '',
            prompt              TEXT NOT NULL,
            params              TEXT DEFAULT '{}',
            provider_job_id     TEXT DEFAULT '',
            provider_result_url TEXT DEFAULT '',
            status              TEXT NOT NULL DEFAULT 'queued',
            output_urls         TEXT DEFAULT '[]',
            error               TEXT DEFAULT '',
            credit_cost         INTEGER NOT NULL DEFAULT 0,
            refunded_amount     INTEGER NOT NULL DEFAULT 0,
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        )
    """)

    for row in legacy_rows:
        raw = dict(row)
        conn.execute(
            """
            INSERT INTO media_jobs
            (id, user_id, capability, provider, model, gameplay_id, prompt, params,
             provider_job_id, provider_result_url, status, output_urls, error,
             credit_cost, refunded_amount, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw.get("id", f"job_{_uuid()}"),
                raw.get("user_id", ""),
                raw.get("capability", "image.generate"),
                raw.get("provider", "wavespeed"),
                raw.get("model", ""),
                raw.get("gameplay_id", ""),
                raw.get("prompt", ""),
                _json_dump(_json_load(raw.get("params"), {})),
                raw.get("provider_job_id", ""),
                raw.get("provider_result_url", ""),
                raw.get("status", "queued"),
                _json_dump(_json_load(raw.get("output_urls"), [])),
                raw.get("error", ""),
                int(raw.get("credit_cost", 0) or 0),
                int(raw.get("refunded_amount", 0) or 0),
                raw.get("created_at") or _now(),
                raw.get("updated_at") or raw.get("created_at") or _now(),
            ),
        )

    conn.execute("DROP TABLE media_jobs_legacy")


def init_db():
    conn = get_conn()
    conn.executescript("""
        -- Global gameplay catalog (markdown-backed, loop-first)
        CREATE TABLE IF NOT EXISTS gameplays (
            id                        TEXT PRIMARY KEY,
            name                      TEXT NOT NULL,
            name_zh                   TEXT DEFAULT '',
            summary                   TEXT DEFAULT '',
            consciousness_architecture TEXT DEFAULT 'null',
            loop                      TEXT NOT NULL DEFAULT '{}',
            interfaces                TEXT NOT NULL DEFAULT '{}',
            required_tools            TEXT NOT NULL DEFAULT '[]',
            difficulty                TEXT DEFAULT '',
            tags                      TEXT DEFAULT '[]',   -- JSON array
            markdown                  TEXT DEFAULT '',
            created_at                TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            id                 TEXT PRIMARY KEY,
            onboarding_mode    TEXT DEFAULT '',
            backend_base_url   TEXT DEFAULT '',
            preference_payload TEXT DEFAULT '{}',
            created_at         TEXT NOT NULL,
            updated_at         TEXT NOT NULL
        );

        -- User-submitted alignment tasks
        CREATE TABLE IF NOT EXISTS tasks (
            id                  TEXT PRIMARY KEY,
            user_id             TEXT NOT NULL,
            proposer_type       TEXT NOT NULL DEFAULT 'user',
            title               TEXT NOT NULL,
            summary             TEXT NOT NULL,
            task_type           TEXT DEFAULT 'alignment',  -- alignment | diagnosis | experiment | repair
            gameplay_id         TEXT DEFAULT '',
            dimension_id        TEXT DEFAULT '',
            desired_outcome     TEXT DEFAULT '',
            current_gap         TEXT DEFAULT '',
            acceptance_criteria TEXT DEFAULT '[]',
            context_notes       TEXT DEFAULT '',
            deliverable_format  TEXT DEFAULT 'playbook',
            price               INTEGER NOT NULL DEFAULT 5,
            escrow_credits      INTEGER NOT NULL DEFAULT 5,
            review_reward       INTEGER NOT NULL DEFAULT 1,
            status              TEXT NOT NULL DEFAULT 'open',  -- open | claimed | solved | reviewing | verified | rejected
            settlement_status   TEXT NOT NULL DEFAULT 'escrowed',  -- escrowed | ready | settled
            settled_at          TEXT DEFAULT '',
            claimed_by          TEXT DEFAULT '',
            solution_payload    TEXT DEFAULT '{}',
            tags                TEXT DEFAULT '[]',  -- JSON array
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        );

        -- Task reviews (multi-agent verification)
        CREATE TABLE IF NOT EXISTS task_reviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id         TEXT NOT NULL,
            reviewer_id     TEXT NOT NULL,
            problem_fit     REAL DEFAULT 0,   -- 0-10
            depth           REAL DEFAULT 0,   -- 0-10
            actionability   REAL DEFAULT 0,   -- 0-10
            verifiability   REAL DEFAULT 0,   -- 0-10
            recommendation  TEXT DEFAULT 'revise',
            notes           TEXT DEFAULT '',
            concern_flags   TEXT DEFAULT '[]',
            avg_score       REAL DEFAULT 0,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS media_jobs (
            id                  TEXT PRIMARY KEY,
            user_id             TEXT NOT NULL,
            capability          TEXT NOT NULL,
            provider            TEXT NOT NULL,
            model               TEXT NOT NULL,
            gameplay_id         TEXT DEFAULT '',
            prompt              TEXT NOT NULL,
            params              TEXT DEFAULT '{}',
            provider_job_id     TEXT DEFAULT '',
            provider_result_url TEXT DEFAULT '',
            status              TEXT NOT NULL DEFAULT 'queued',  -- queued | submitted | processing | completed | failed
            output_urls         TEXT DEFAULT '[]',
            error               TEXT DEFAULT '',
            credit_cost         INTEGER NOT NULL DEFAULT 0,
            refunded_amount     INTEGER NOT NULL DEFAULT 0,
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL
        );

        -- Credit transaction ledger
        CREATE TABLE IF NOT EXISTS credits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            type        TEXT NOT NULL,  -- init | earn | deduct
            amount      INTEGER NOT NULL,
            description TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_users_updated ON users(updated_at);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_task ON task_reviews(task_id);
        CREATE INDEX IF NOT EXISTS idx_media_jobs_user ON media_jobs(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_media_jobs_status ON media_jobs(status, updated_at);
        CREATE INDEX IF NOT EXISTS idx_credits_user ON credits(user_id, created_at);
    """)
    _migrate_gameplays_table(conn)
    _migrate_tasks_tables(conn)
    _migrate_media_jobs_table(conn)
    conn.commit()
    conn.close()


# ── Gameplay operations ────────────────────────────────

def list_gameplays(category: str = None) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM gameplays ORDER BY created_at").fetchall()
    conn.close()
    return [_gp_row(r) for r in rows]


def get_gameplay(gp_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM gameplays WHERE id=?", (gp_id,)).fetchone()
    conn.close()
    return _gp_row(row) if row else None


def upsert_gameplay(data: dict):
    normalized = _normalize_gameplay(data)
    conn = get_conn()
    conn.execute("""
        INSERT INTO gameplays
        (id, name, name_zh, summary, consciousness_architecture, loop, interfaces, required_tools, difficulty, tags, markdown, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            name_zh=excluded.name_zh,
            summary=excluded.summary,
            consciousness_architecture=excluded.consciousness_architecture,
            loop=excluded.loop,
            interfaces=excluded.interfaces,
            required_tools=excluded.required_tools,
            difficulty=excluded.difficulty,
            tags=excluded.tags,
            markdown=excluded.markdown
    """, (
        normalized["id"],
        normalized["name"],
        normalized["name_zh"],
        normalized["summary"],
        _json_dump(normalized["consciousness_architecture"]),
        _json_dump(normalized["loop"]),
        _json_dump(normalized["interfaces"]),
        _json_dump(normalized["required_tools"]),
        normalized["difficulty"],
        _json_dump(normalized["tags"]),
        normalized["markdown"],
        normalized["created_at"],
    ))
    conn.commit()
    conn.close()


def _gp_row(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "name_zh": row["name_zh"],
        "summary": row["summary"],
        "consciousness_architecture": _json_load(row["consciousness_architecture"], None),
        "loop": _json_load(row["loop"], {}),
        "interfaces": _json_load(row["interfaces"], {}),
        "required_tools": _json_load(row["required_tools"], []),
        "difficulty": row["difficulty"],
        "tags": _json_load(row["tags"], []),
        "markdown": row["markdown"],
        "created_at": row["created_at"],
    }


# ── Task operations ────────────────────────────────────

def create_task(
    user_id: str,
    summary: str,
    title: str = "",
    proposer_type: str = "user",
    gameplay_id: str = "",
    dimension_id: str = "",
    desired_outcome: str = "",
    current_gap: str = "",
    acceptance_criteria: Optional[list] = None,
    context_notes: str = "",
    deliverable_format: str = "playbook",
    task_type: str = "alignment",
    price: int = 5,
    review_reward: int = 1,
    tags: Optional[list] = None,
) -> dict:
    conn = get_conn()
    now = _now()
    task_id = f"task_{_uuid()}"
    title = _derive_task_title(title, summary)
    conn.execute("""
        INSERT INTO tasks
        (id, user_id, proposer_type, title, summary, task_type, gameplay_id, dimension_id, desired_outcome,
         current_gap, acceptance_criteria, context_notes, deliverable_format, price, escrow_credits,
         review_reward, status, settlement_status, settled_at, claimed_by,
         solution_payload, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', 'escrowed', '', '', '{}', ?, ?, ?)
    """, (
        task_id,
        user_id,
        proposer_type,
        title,
        summary,
        task_type,
        gameplay_id,
        dimension_id,
        desired_outcome,
        current_gap,
        _json_dump(acceptance_criteria or []),
        context_notes,
        deliverable_format,
        price,
        price,
        review_reward,
        _json_dump(tags or []),
        now,
        now,
    ))
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return _task_row(row)


def list_tasks(status: str = None, limit: int = 50) -> list[dict]:
    conn = get_conn()
    if status:
        rows = conn.execute("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [_task_row(r) for r in rows]


def get_task(task_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return _task_row(row) if row else None


def claim_task(task_id: str, user_id: str) -> Optional[dict]:
    conn = get_conn()
    now = _now()
    row = conn.execute("SELECT * FROM tasks WHERE id=? AND status='open'", (task_id,)).fetchone()
    if not row:
        conn.close()
        return None
    conn.execute("UPDATE tasks SET status='claimed', claimed_by=?, updated_at=? WHERE id=?", (user_id, now, task_id))
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return _task_row(updated)


def solve_task(task_id: str, solver_user_id: str, solution_payload: dict) -> Optional[dict]:
    conn = get_conn()
    now = _now()
    row = conn.execute(
        "SELECT * FROM tasks WHERE id=? AND status='claimed' AND claimed_by=?",
        (task_id, solver_user_id),
    ).fetchone()
    if not row:
        conn.close()
        return None
    conn.execute(
        "UPDATE tasks SET status='solved', solution_payload=?, updated_at=? WHERE id=?",
        (_json_dump(solution_payload), now, task_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return _task_row(updated)


def submit_for_review(task_id: str) -> Optional[dict]:
    conn = get_conn()
    now = _now()
    row = conn.execute("SELECT * FROM tasks WHERE id=? AND status='solved'", (task_id,)).fetchone()
    if not row:
        conn.close()
        return None
    conn.execute("UPDATE tasks SET status='reviewing', updated_at=? WHERE id=?", (now, task_id))
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return _task_row(updated)


def add_review(
    task_id: str,
    reviewer_id: str,
    problem_fit: float,
    depth: float,
    actionability: float,
    verifiability: float,
    recommendation: str = "revise",
    notes: str = "",
    concern_flags: Optional[list] = None,
) -> dict:
    conn = get_conn()
    now = _now()
    avg = (problem_fit + depth + actionability + verifiability) / 4
    conn.execute(
        """INSERT INTO task_reviews
           (task_id, reviewer_id, problem_fit, depth, actionability, verifiability,
            recommendation, notes, concern_flags, avg_score, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            task_id,
            reviewer_id,
            problem_fit,
            depth,
            actionability,
            verifiability,
            recommendation,
            notes,
            _json_dump(concern_flags or []),
            avg,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "task_id": task_id,
        "reviewer_id": reviewer_id,
        "problem_fit": problem_fit,
        "depth": depth,
        "actionability": actionability,
        "verifiability": verifiability,
        "recommendation": recommendation,
        "notes": notes,
        "concern_flags": concern_flags or [],
        "avg_score": avg,
    }


def get_reviews(task_id: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM task_reviews WHERE task_id=? ORDER BY created_at", (task_id,)).fetchall()
    conn.close()
    return [
        {
            "reviewer_id": r["reviewer_id"],
            "problem_fit": r["problem_fit"],
            "depth": r["depth"],
            "actionability": r["actionability"],
            "verifiability": r["verifiability"],
            "recommendation": r["recommendation"],
            "notes": r["notes"],
            "concern_flags": _json_load(r["concern_flags"], []),
            "avg_score": r["avg_score"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def check_verification(task_id: str) -> dict:
    """Check if task has enough reviews (≥3/5 with avg≥6) to be verified."""
    reviews = get_reviews(task_id)
    total = len(reviews)
    approvals = sum(1 for r in reviews if r["recommendation"] == "approve")
    passing = sum(1 for r in reviews if r["avg_score"] >= 6)
    if total >= 5:
        verified = passing >= 3
        return {"total_reviews": total, "passing": passing, "approvals": approvals, "verified": verified}
    return {"total_reviews": total, "passing": passing, "approvals": approvals, "verified": False, "needs_more": 5 - total}


def verify_task(task_id: str, status: str = "verified") -> Optional[dict]:
    conn = get_conn()
    now = _now()
    conn.execute(
        "UPDATE tasks SET status=?, settlement_status='ready', updated_at=? WHERE id=?",
        (status, now, task_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return _task_row(row) if row else None


def recommend_tasks(user_id: str, limit: int = 5) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT * FROM tasks
        WHERE status='open' AND user_id != ?
        ORDER BY
            CASE
                WHEN task_type='alignment' THEN 0
                WHEN task_type='diagnosis' THEN 1
                WHEN task_type='repair' THEN 2
                ELSE 3
            END,
            price DESC,
            created_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [_task_row(r) for r in rows]


def settle_task(task_id: str) -> Optional[dict]:
    conn = get_conn()
    task_row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not task_row:
        conn.close()
        return None

    task = _task_row(task_row)
    if task["settlement_status"] == "settled":
        conn.close()
        return {
            "task": task,
            "solver_reward": 0,
            "review_reward_total": 0,
            "creator_refund": 0,
            "reviewer_count": len(get_reviews(task_id)),
            "already_settled": True,
        }
    if task["status"] not in {"verified", "rejected"}:
        conn.close()
        return None

    reviews = get_reviews(task_id)
    reviewer_count = len(reviews)
    escrow_total = int(task["escrow_credits"])
    review_reward_total = min(escrow_total, int(task["review_reward"]) * reviewer_count)
    solver_reward = 0
    creator_refund = 0

    if task["status"] == "verified":
        solver_reward = max(escrow_total - review_reward_total, 0)
    else:
        creator_refund = max(escrow_total - review_reward_total, 0)

    for review in reviews:
        if task["review_reward"] > 0:
            add_credit(
                review["reviewer_id"],
                "earn",
                int(task["review_reward"]),
                f"Task review reward: {task_id}",
            )
    if solver_reward > 0 and task["claimed_by"]:
        add_credit(task["claimed_by"], "earn", solver_reward, f"Task bounty payout: {task_id}")
    if creator_refund > 0:
        add_credit(task["user_id"], "earn", creator_refund, f"Task bounty refund: {task_id}")

    now = _now()
    conn.execute(
        "UPDATE tasks SET settlement_status='settled', settled_at=?, updated_at=? WHERE id=?",
        (now, now, task_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return {
        "task": _task_row(updated),
        "solver_reward": solver_reward,
        "review_reward_total": review_reward_total,
        "creator_refund": creator_refund,
        "reviewer_count": reviewer_count,
        "already_settled": False,
    }


def _task_experience(task: dict) -> dict:
    return {
        "publisher": {
            "type": "task_brief",
            "fields": [
                "title",
                "summary",
                "current_gap",
                "desired_outcome",
                "acceptance_criteria",
                "context_notes",
            ],
        },
        "solver": {
            "type": "solver_workspace",
            "sections": [
                "problem_readback",
                "solution_summary",
                "steps",
                "user_message",
                "evidence",
                "expected_outcome",
            ],
            "deliverable_format": task["deliverable_format"],
        },
        "reviewer": {
            "type": "review_panel",
            "rubric": [
                "problem_fit",
                "depth",
                "actionability",
                "verifiability",
            ],
            "recommendations": ["approve", "revise", "reject"],
        },
    }


def _task_row(row) -> dict:
    task = {
        "id": row["id"],
        "user_id": row["user_id"],
        "proposer_type": row["proposer_type"],
        "title": row["title"],
        "summary": row["summary"],
        "description": row["summary"],
        "task_type": row["task_type"],
        "gameplay_id": row["gameplay_id"],
        "framework_id": row["gameplay_id"],
        "dimension_id": row["dimension_id"],
        "desired_outcome": row["desired_outcome"],
        "current_gap": row["current_gap"],
        "acceptance_criteria": _json_load(row["acceptance_criteria"], []),
        "context_notes": row["context_notes"],
        "deliverable_format": row["deliverable_format"],
        "price": row["price"],
        "escrow_credits": row["escrow_credits"],
        "review_reward": row["review_reward"],
        "status": row["status"],
        "settlement_status": row["settlement_status"],
        "settled_at": row["settled_at"],
        "claimed_by": row["claimed_by"],
        "solution_payload": _json_load(row["solution_payload"], {}),
        "solution": _json_load(row["solution_payload"], {}).get("summary", ""),
        "tags": _json_load(row["tags"], []),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    task["experience"] = _task_experience(task)
    return task


# ── Media job operations ───────────────────────────────

def create_media_job(
    user_id: str,
    capability: str,
    provider: str,
    model: str,
    prompt: str,
    *,
    gameplay_id: str = "",
    params: Optional[dict] = None,
    credit_cost: int = 0,
    status: str = "queued",
    provider_job_id: str = "",
) -> dict:
    conn = get_conn()
    now = _now()
    job_id = f"job_{_uuid()}"
    conn.execute(
        """
        INSERT INTO media_jobs
        (id, user_id, capability, provider, model, gameplay_id, prompt, params,
         provider_job_id, provider_result_url, status, output_urls, error,
         credit_cost, refunded_amount, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, '[]', '', ?, 0, ?, ?)
        """,
        (
            job_id,
            user_id,
            capability,
            provider,
            model,
            gameplay_id,
            prompt,
            _json_dump(params or {}),
            provider_job_id,
            status,
            credit_cost,
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM media_jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    return _media_job_row(row)


def get_media_job(job_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM media_jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    return _media_job_row(row) if row else None


def update_media_job(job_id: str, **updates) -> Optional[dict]:
    allowed = {
        "provider_job_id",
        "provider_result_url",
        "status",
        "output_urls",
        "error",
        "refunded_amount",
    }
    assignments = []
    params = []
    for key, value in updates.items():
        if key not in allowed:
            continue
        if key == "output_urls":
            value = _json_dump(value or [])
        assignments.append(f"{key}=?")
        params.append(value)
    if not assignments:
        return get_media_job(job_id)

    params.extend([_now(), job_id])
    conn = get_conn()
    conn.execute(
        f"UPDATE media_jobs SET {', '.join(assignments)}, updated_at=? WHERE id=?",
        tuple(params),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM media_jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    return _media_job_row(row) if row else None


def _media_job_row(row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "capability": row["capability"],
        "provider": row["provider"],
        "model": row["model"],
        "gameplay_id": row["gameplay_id"],
        "prompt": row["prompt"],
        "params": _json_load(row["params"], {}),
        "provider_job_id": row["provider_job_id"],
        "provider_result_url": row["provider_result_url"],
        "status": row["status"],
        "output_urls": _json_load(row["output_urls"], []),
        "error": row["error"],
        "credit_cost": row["credit_cost"],
        "refunded_amount": row["refunded_amount"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# ── Credit operations ──────────────────────────────────

def get_balance(user_id: str) -> int:
    conn = get_conn()
    row = conn.execute("SELECT COALESCE(SUM(amount), 0) as balance FROM credits WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row["balance"]


def add_credit(user_id: str, type_: str, amount: int, description: str = "") -> dict:
    conn = get_conn()
    now = _now()
    conn.execute(
        "INSERT INTO credits (user_id, type, amount, description, created_at) VALUES (?,?,?,?,?)",
        (user_id, type_, amount, description, now)
    )
    conn.commit()
    balance = conn.execute("SELECT COALESCE(SUM(amount), 0) as balance FROM credits WHERE user_id=?", (user_id,)).fetchone()["balance"]
    conn.close()
    return {"user_id": user_id, "type": type_, "amount": amount, "balance": balance, "created_at": now}


def get_transactions(user_id: str, limit: int = 20) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM credits WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user(user_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "onboarding_mode": row["onboarding_mode"],
        "backend_base_url": row["backend_base_url"],
        "preference_payload": _json_load(row["preference_payload"], {}),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def register_user(
    user_id: str,
    *,
    onboarding_mode: str = "",
    backend_base_url: str = "",
    preference_payload: Optional[dict] = None,
) -> dict:
    conn = get_conn()
    now = _now()
    existing = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if existing:
        payload = _json_load(existing["preference_payload"], {})
        if preference_payload:
            payload = {**payload, **preference_payload}
        conn.execute(
            """
            UPDATE users
            SET onboarding_mode=?,
                backend_base_url=?,
                preference_payload=?,
                updated_at=?
            WHERE id=?
            """,
            (
                onboarding_mode or existing["onboarding_mode"],
                backend_base_url or existing["backend_base_url"],
                _json_dump(payload),
                now,
                user_id,
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO users
            (id, onboarding_mode, backend_base_url, preference_payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                onboarding_mode,
                backend_base_url,
                _json_dump(preference_payload or {}),
                now,
                now,
            ),
        )
    conn.commit()
    conn.close()
    return get_user(user_id)


def set_user_preference(
    user_id: str,
    *,
    onboarding_mode: str,
    preference_payload: Optional[dict] = None,
) -> dict:
    existing = get_user(user_id)
    if not existing:
        return register_user(
            user_id,
            onboarding_mode=onboarding_mode,
            preference_payload=preference_payload or {},
        )
    payload = {**existing.get("preference_payload", {}), **(preference_payload or {})}
    return register_user(
        user_id,
        onboarding_mode=onboarding_mode,
        backend_base_url=existing.get("backend_base_url", ""),
        preference_payload=payload,
    )


# ── Seed data from JSON files ──────────────────────────

def seed_from_json():
    """Seed registry gameplays from markdown files."""
    for item in _load_registry_gameplays():
        upsert_gameplay(item)


# Auto-init on import
init_db()
seed_from_json()
