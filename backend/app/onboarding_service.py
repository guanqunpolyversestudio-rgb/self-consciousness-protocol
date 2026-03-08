"""Onboarding helpers shared by /onboarding and legacy /handshake."""
from __future__ import annotations

from typing import Optional

from . import db, local_db
from .user_data import set_profile_preference, upsert_profile_user

INITIAL_CREDITS = 500
DEFAULT_ONBOARDING_MODE = "structured_alignment_workspace"


def register_user_context(
    user_id: str,
    *,
    backend_base_url: str = "",
    onboarding_mode: str = "",
) -> dict:
    chosen_mode = onboarding_mode or DEFAULT_ONBOARDING_MODE
    db_user = db.register_user(
        user_id,
        onboarding_mode=chosen_mode,
        backend_base_url=backend_base_url,
    )

    balance = db.get_balance(user_id)
    if balance == 0:
        db.add_credit(user_id, "init", INITIAL_CREDITS, "Initial credit on first registration")
        balance = INITIAL_CREDITS

    local_db.init_local_db(user_id)
    current_gp = local_db.get_current_gameplay(user_id)
    default_gp = None
    if not current_gp:
        default_gp = db.get_gameplay("structured_reflection")
        if default_gp:
            local_db.append_gameplay(
                user_id,
                default_gp,
                "onboarding_pull",
                "structured_reflection",
                change_note="Initial default gameplay on first registration",
            )

    profile = upsert_profile_user(
        user_id,
        backend_base_url=backend_base_url,
        onboarding_mode=chosen_mode,
        preference_payload=db_user.get("preference_payload", {}),
    )

    return {
        "ok": True,
        "user_id": user_id,
        "credits": balance,
        "onboarding_mode": chosen_mode,
        "default_gameplay": default_gp["id"] if default_gp else (current_gp["gameplay"]["id"] if current_gp else None),
        "profile": profile,
        "workspace": profile["users"][user_id]["workspace"],
    }


def save_user_preference(
    user_id: str,
    *,
    onboarding_mode: str,
    preference_payload: Optional[dict] = None,
) -> dict:
    pref_payload = preference_payload or {}
    user = db.set_user_preference(
        user_id,
        onboarding_mode=onboarding_mode,
        preference_payload=pref_payload,
    )
    profile = set_profile_preference(
        user_id,
        onboarding_mode=onboarding_mode,
        preference_payload=user.get("preference_payload", {}),
    )
    return {
        "ok": True,
        "user_id": user_id,
        "onboarding_mode": onboarding_mode,
        "preference_payload": user.get("preference_payload", {}),
        "profile": profile,
    }
