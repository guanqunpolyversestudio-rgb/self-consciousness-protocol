"""Local user data paths and profile storage under ~/.self-consciousness/."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

USER_DATA_ROOT = Path.home() / ".self-consciousness"
PROFILE_PATH = USER_DATA_ROOT / "profile.json"
LOCAL_DB_FILENAME = "consciousness.db"


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def get_user_root(user_id: str) -> Path:
    return USER_DATA_ROOT / "users" / user_id


def get_user_db_path(user_id: str) -> Path:
    return get_user_root(user_id) / LOCAL_DB_FILENAME


def get_user_gameplay_drafts_dir(user_id: str) -> Path:
    return get_user_root(user_id) / "gameplay_drafts"


def get_user_artifacts_dir(user_id: str) -> Path:
    return get_user_root(user_id) / "artifacts"


def ensure_user_workspace(user_id: str) -> dict:
    root = get_user_root(user_id)
    drafts = get_user_gameplay_drafts_dir(user_id)
    artifacts = get_user_artifacts_dir(user_id)
    logs = USER_DATA_ROOT / "logs"

    root.mkdir(parents=True, exist_ok=True)
    drafts.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    return {
        "root": str(root),
        "db_path": str(get_user_db_path(user_id)),
        "gameplay_drafts_dir": str(drafts),
        "artifacts_dir": str(artifacts),
        "logs_dir": str(logs),
    }


def read_profile() -> dict:
    if not PROFILE_PATH.exists():
        return {
            "current_user_id": "",
            "backend_base_url": "",
            "users": {},
            "updated_at": "",
        }
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "current_user_id": "",
            "backend_base_url": "",
            "users": {},
            "updated_at": "",
        }


def write_profile(profile: dict) -> dict:
    USER_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    profile["updated_at"] = _now()
    PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return profile


def upsert_profile_user(
    user_id: str,
    *,
    backend_base_url: str = "",
    onboarding_mode: str = "",
    preference_payload: Optional[dict] = None,
) -> dict:
    workspace = ensure_user_workspace(user_id)
    profile = read_profile()
    users = profile.setdefault("users", {})
    existing = users.get(user_id, {})

    users[user_id] = {
        **existing,
        "user_id": user_id,
        "workspace": workspace,
        "onboarding_mode": onboarding_mode or existing.get("onboarding_mode", ""),
        "preference_payload": preference_payload or existing.get("preference_payload", {}),
        "created_at": existing.get("created_at") or _now(),
    }
    profile["current_user_id"] = user_id
    if backend_base_url:
        profile["backend_base_url"] = backend_base_url

    return write_profile(profile)


def set_profile_preference(user_id: str, onboarding_mode: str, preference_payload: Optional[dict] = None) -> dict:
    profile = upsert_profile_user(
        user_id,
        onboarding_mode=onboarding_mode,
        preference_payload=preference_payload or {},
    )
    profile["current_user_id"] = user_id
    return write_profile(profile)
