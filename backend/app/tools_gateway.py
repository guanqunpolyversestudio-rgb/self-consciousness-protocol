"""Capability catalog for the local tools gateway."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .node_bridge import SKILL_ROOT


DEFAULT_MODELS = {
    "image.generate": "bytedance/seedream-v3",
    "video.generate": "bytedance/seedance-v1-lite-t2v-720p",
}


def _read_api_key_from_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _read_key_from_dotenv(path: Path, key_name: str) -> str:
    if not path.exists():
        return ""
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() != key_name:
                continue
            return value.strip().strip("'").strip('"')
    except Exception:
        return ""
    return ""


def get_wavespeed_api_key() -> str:
    direct = os.getenv("WAVESPEED_API_KEY", "").strip()
    if direct:
        return direct

    file_from_env = os.getenv("WAVESPEED_API_KEY_FILE", "").strip()
    if file_from_env:
        key = _read_api_key_from_file(Path(file_from_env))
        if key:
            return key

    for candidate in (
        SKILL_ROOT / ".wavespeed_api_key",
        SKILL_ROOT / "wavespeed_api_key.txt",
    ):
        key = _read_api_key_from_file(candidate)
        if key:
            return key

    dotenv_key = _read_key_from_dotenv(SKILL_ROOT / "backend" / ".env", "WAVESPEED_API_KEY")
    if dotenv_key:
        return dotenv_key
    return ""


def _provider_status(provider: str) -> dict:
    if provider == "wavespeed":
        configured = bool(get_wavespeed_api_key())
        return {
            "provider": provider,
            "configured": configured,
            "note": (
                "Set WAVESPEED_API_KEY or place .wavespeed_api_key under the skill root."
                if not configured
                else "Configured."
            ),
        }
    return {"provider": provider, "configured": False, "note": "Provider not configured."}


def list_capabilities() -> list[dict]:
    wavespeed = _provider_status("wavespeed")
    return [
        {
            "id": "image.generate",
            "category": "media",
            "providers": [wavespeed],
            "default_provider": "wavespeed",
            "default_model": DEFAULT_MODELS["image.generate"],
            "credit_cost": 1,
            "status": "available" if wavespeed["configured"] else "declared",
        },
        {
            "id": "video.generate",
            "category": "media",
            "providers": [wavespeed],
            "default_provider": "wavespeed",
            "default_model": DEFAULT_MODELS["video.generate"],
            "credit_cost": 5,
            "status": "available" if wavespeed["configured"] else "declared",
        },
        {
            "id": "audio.generate",
            "category": "media",
            "providers": [],
            "default_provider": "",
            "default_model": "",
            "credit_cost": 0,
            "status": "planned",
        },
        {
            "id": "voice.speak",
            "category": "media",
            "providers": [],
            "default_provider": "",
            "default_model": "",
            "credit_cost": 0,
            "status": "planned",
        },
        {
            "id": "vision.analyze",
            "category": "analysis",
            "providers": [],
            "default_provider": "",
            "default_model": "",
            "credit_cost": 0,
            "status": "planned",
        },
        {
            "id": "web.search",
            "category": "knowledge",
            "providers": [],
            "default_provider": "",
            "default_model": "",
            "credit_cost": 0,
            "status": "planned",
        },
        {
            "id": "browser.capture",
            "category": "knowledge",
            "providers": [],
            "default_provider": "",
            "default_model": "",
            "credit_cost": 0,
            "status": "planned",
        },
        {
            "id": "document.render",
            "category": "productivity",
            "providers": [],
            "default_provider": "",
            "default_model": "",
            "credit_cost": 0,
            "status": "planned",
        },
    ]


def get_capability(capability_id: str) -> Optional[dict]:
    return next((item for item in list_capabilities() if item["id"] == capability_id), None)
