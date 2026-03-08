"""Bridge to the Node.js skill engine via subprocess calls."""
from __future__ import annotations
import json
import subprocess
import os
from pathlib import Path
from typing import Optional, Union

from .user_data import get_user_root

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_JS = SKILL_ROOT / "index.js"

def _run(args: list[str], input_data: Optional[str] = None) -> Union[dict, str]:
    """Run a node index.js command and return parsed output."""
    cmd = ["node", str(INDEX_JS)] + args
    result = subprocess.run(
        cmd,
        cwd=str(SKILL_ROOT),
        capture_output=True,
        text=True,
        input=input_data,
        timeout=30,
    )
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode != 0:
        raise RuntimeError(f"Node command failed: {stderr or stdout}")

    # Try to parse as JSON
    try:
        return json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return stdout


def _run_json_file(args: list[str], data: dict) -> Union[dict, str]:
    """Write data to a temp JSON file, pass via --file, clean up."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir=str(SKILL_ROOT)) as f:
        json.dump(data, f)
        tmp_path = f.name
    try:
        return _run(args + [f"--file={tmp_path}"])
    finally:
        os.unlink(tmp_path)


# === Direct file-based operations (bypass CLI for speed) ===

def read_json(rel_path: str, fallback=None):
    """Read a JSON file relative to skill root."""
    p = SKILL_ROOT / rel_path
    if not p.exists():
        return fallback
    try:
        return json.loads(p.read_text())
    except Exception:
        return fallback


def write_json(rel_path: str, data):
    """Write a JSON file relative to skill root."""
    p = SKILL_ROOT / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def read_jsonl(rel_path: str, limit: int = 200) -> list[dict]:
    """Read a JSONL file relative to SKILL_ROOT, return last N entries."""
    p = SKILL_ROOT / rel_path
    return _read_jsonl_abs(p, limit)


def append_jsonl(rel_path: str, record: dict):
    """Append a record to a JSONL file relative to SKILL_ROOT."""
    p = SKILL_ROOT / rel_path
    _append_jsonl_abs(p, record)


def read_user_jsonl(user_id: str, filename: str, limit: int = 200) -> list[dict]:
    """Read a JSONL file from ~/.self-consciousness/users/{user_id}/."""
    p = get_user_root(user_id) / filename
    return _read_jsonl_abs(p, limit)


def append_user_jsonl(user_id: str, filename: str, record: dict):
    """Append a record to ~/.self-consciousness/users/{user_id}/{filename}."""
    p = get_user_root(user_id) / filename
    _append_jsonl_abs(p, record)


def _read_jsonl_abs(p: Path, limit: int = 200) -> list[dict]:
    if not p.exists():
        return []
    lines = p.read_text().strip().split("\n")
    lines = [l for l in lines if l.strip()]
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries


def _append_jsonl_abs(p: Path, record: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def today() -> str:
    """Return today's date in local timezone YYYY-MM-DD."""
    from datetime import datetime
    d = datetime.now()
    return f"{d.year}-{d.month:02d}-{d.day:02d}"
