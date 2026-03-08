"""Gameplays — /api/v1/gameplays"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from copy import deepcopy
import json
from typing import Optional
from .. import db
from .. import local_db

router = APIRouter()


class RecommendRequest(BaseModel):
    query: str = ""


class PullRequest(BaseModel):
    user_id: str
    gameplay_id: str


class ContributeRequest(BaseModel):
    user_id: str
    gameplay: Optional[dict] = None
    markdown: str = ""


class IterateRequest(BaseModel):
    updates: dict = {}
    gameplay: Optional[dict] = None
    note: str = ""


def _deep_merge(base: dict, updates: dict) -> dict:
    merged = deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# ── Global ─────────────────────────────────────────────

@router.get("")
def list_all():
    return {"gameplays": db.list_gameplays()}


@router.get("/{gameplay_id}")
def get_one(gameplay_id: str):
    gp = db.get_gameplay(gameplay_id)
    if not gp:
        raise HTTPException(404, f"Gameplay '{gameplay_id}' not found")
    return gp


@router.post("/recommend")
def recommend(req: RecommendRequest):
    gameplays = db.list_gameplays()
    if not gameplays:
        raise HTTPException(404, "No gameplays available")
    if not req.query:
        default = next((g for g in gameplays if "default" in g.get("tags", [])), gameplays[0])
        return {"recommended": default, "reason": "default"}

    def score(gp):
        architecture = gp.get("consciousness_architecture") or {}
        searchable = " ".join([
            gp.get("name", ""),
            gp.get("name_zh", ""),
            gp.get("summary", ""),
            " ".join(gp.get("tags", [])),
            " ".join(architecture.get("dimensions", [])),
            json.dumps(gp.get("interfaces", {}), ensure_ascii=False),
            gp.get("markdown", ""),
        ]).lower()
        return sum(1 for w in req.query.lower().split() if w in searchable)

    best = max(gameplays, key=score)
    return {"recommended": best, "reason": f"keyword match (score={score(best)})"}


@router.post("/contribute")
def contribute(req: ContributeRequest):
    gp = req.gameplay or {}
    if req.markdown:
        try:
            gp = db.parse_gameplay_markdown(req.markdown)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
    if not gp.get("id") or not gp.get("name"):
        raise HTTPException(400, "Gameplay must have id and name")
    db.upsert_gameplay(gp)
    db.add_credit(req.user_id, "earn", 10, f"Contributed gameplay: {gp['id']}")
    return {"ok": True, "gameplay_id": gp["id"], "credit_earned": 10}


# ── User local (~/.self-consciousness/consciousness.db) ─

@router.post("/pull")
def pull(req: PullRequest):
    gp = db.get_gameplay(req.gameplay_id)
    if not gp:
        raise HTTPException(404, f"Gameplay '{req.gameplay_id}' not found")

    version = local_db.append_gameplay(req.user_id, gp, "pull", req.gameplay_id, change_note="Pulled from shared registry")
    return {"ok": True, "gameplay_id": req.gameplay_id, "version": version}


@router.post("/{user_id}/iterate")
def iterate(user_id: str, req: IterateRequest):
    current = local_db.get_current_gameplay(user_id)
    if not current:
        raise HTTPException(404, f"No local gameplays for user '{user_id}'")
    if not req.gameplay and not req.updates:
        raise HTTPException(400, "Provide either gameplay or updates")

    next_gameplay = req.gameplay or _deep_merge(current["gameplay"], req.updates)
    next_gameplay.setdefault("id", current["gameplay"].get("id"))
    next_gameplay.setdefault("name", current["gameplay"].get("name"))
    next_gameplay.setdefault("name_zh", current["gameplay"].get("name_zh", ""))

    version = local_db.append_gameplay(
        user_id,
        next_gameplay,
        "iterate",
        current["source_id"] or current["gameplay"].get("id", ""),
        parent_version=current["version"],
        change_note=req.note or "Iterated local gameplay",
    )
    return {
        "ok": True,
        "previous_version": current["version"],
        "version": version,
        "gameplay": next_gameplay,
    }


@router.get("/{user_id}/current")
def get_current(user_id: str):
    entry = local_db.get_current_gameplay(user_id)
    if not entry:
        raise HTTPException(404, f"No local gameplays for user '{user_id}'")
    return entry


@router.get("/{user_id}/history")
def get_history(user_id: str, limit: int = 50):
    entries = local_db.get_gameplay_history(user_id, limit)
    return {"user_id": user_id, "entries": entries, "count": len(entries)}
