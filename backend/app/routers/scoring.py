"""Scoring — /api/v1/scoring"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .. import db
from .. import local_db
from ..node_bridge import read_json

router = APIRouter()

_scoring_stages_cache = None


def _get_scoring_stages() -> dict:
    global _scoring_stages_cache
    if _scoring_stages_cache is None:
        _scoring_stages_cache = read_json("global_registry/scoring_stages.json", {})
        dims = _scoring_stages_cache.get("scoring_dimensions", [])
        if dims:
            _scoring_stages_cache["scoring_dimensions"] = sorted(
                dims,
                key=lambda dim: (dim.get("priority", 999), dim.get("id", "")),
            )
    return _scoring_stages_cache


def _get_scoring_system_identity() -> tuple[str, str]:
    stages = _get_scoring_stages()
    return stages.get("id", "core_alignment"), stages.get("version", "")


class EvaluateRequest(BaseModel):
    gameplay_id: str
    scores: dict
    date: Optional[str] = None


def _determine_stage(total_score: float) -> str:
    stages = _get_scoring_stages().get("stages", [])
    for s in stages:
        low, high = s["range"]
        if low <= total_score < high:
            return s["level"]
    if stages and total_score >= stages[-1]["range"][1]:
        return stages[-1]["level"]
    return "L0"


def _compute_total(scores: dict) -> float:
    dims = _get_scoring_stages().get("scoring_dimensions", [])
    if not dims:
        vals = list(scores.values())
        return sum(vals) / len(vals) if vals else 0
    total = 0.0
    for dim in dims:
        total += scores.get(dim["id"], 0) * dim["weight"]
    return total


@router.get("/stages")
def get_stages():
    return _get_scoring_stages()


@router.get("/{user_id}/current")
def get_current(user_id: str):
    latest = local_db.get_latest_score(user_id)
    if not latest:
        raise HTTPException(404, f"No scores for user '{user_id}'")
    total = _compute_total(latest["scores"])
    stage = _determine_stage(total)
    return {**latest, "total": total, "stage": stage}


@router.get("/{user_id}/history")
def get_history(user_id: str, gameplay_id: Optional[str] = None, limit: int = 30):
    entries = local_db.get_score_history(user_id, gameplay_id, limit)
    return {"user_id": user_id, "entries": entries, "count": len(entries)}


@router.post("/{user_id}/evaluate")
def evaluate(user_id: str, req: EvaluateRequest):
    total = _compute_total(req.scores)
    stage = _determine_stage(total)
    scoring_system_id, scoring_system_version = _get_scoring_system_identity()
    result = local_db.insert_score(
        user_id,
        req.gameplay_id,
        req.scores,
        stage,
        req.date,
        scoring_system_id=scoring_system_id,
        scoring_system_version=scoring_system_version,
    )
    return {**result, "total": total}


@router.get("/{user_id}/recommend")
def recommend(user_id: str):
    history = local_db.get_score_history(user_id, limit=10)
    stages_config = _get_scoring_stages()
    rules = stages_config.get("gameplay_recommendation_rules", {})
    gameplays = db.list_gameplays()

    if not gameplays:
        raise HTTPException(404, "No gameplays available")

    if not history:
        default = next((g for g in gameplays if "default" in g.get("tags", [])), gameplays[0])
        return {"recommended": default, "reason": "no_history"}

    latest = history[-1]
    total = _compute_total(latest["scores"])
    stage = _determine_stage(total)

    # Check for plateau
    plateau_days = rules.get("plateau_days", 7)
    if len(history) >= plateau_days:
        recent_totals = [_compute_total(h["scores"]) for h in history[-plateau_days:]]
        if max(recent_totals) - min(recent_totals) < 5:
            current_gp_id = latest.get("gameplay_id", "")
            alternatives = [g for g in gameplays if g["id"] != current_gp_id]
            if alternatives:
                return {"recommended": alternatives[0], "reason": "plateau_detected"}

    # Check for weak dimensions
    weak_threshold = rules.get("dimension_weak_threshold", 0.4)
    dims = stages_config.get("scoring_dimensions", [])
    for dim in dims:
        if latest["scores"].get(dim["id"], 1.0) < weak_threshold:
            return {"recommended": gameplays[0], "reason": f"weak_dimension:{dim['id']}"}

    return {"recommended": gameplays[0], "reason": "default"}
