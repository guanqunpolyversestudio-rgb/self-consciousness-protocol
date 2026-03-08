"""Visualization — /api/v1/viz"""
from fastapi import APIRouter, HTTPException
from .. import local_db

router = APIRouter()


@router.get("/{user_id}/dna")
def consciousness_dna(user_id: str):
    """Generate dual DNA visualization data: Human consciousness + AI consciousness side by side."""

    # Human consciousness: latest snapshot dimensions
    snapshot = local_db.get_latest_snapshot(user_id)
    human_dna = {}
    if snapshot:
        human_dna = {
            "dimensions": snapshot["dimensions"],
            "gameplay_id": snapshot["gameplay_id"],
            "gameplay_version": snapshot["gameplay_version"],
            "date": snapshot["date"],
        }

    # AI consciousness: latest self-model
    ai_model = local_db.get_latest_ai_self_model(user_id)
    ai_dna = {}
    if ai_model:
        ai_dna = {
            "personality": ai_model["personality"],
            "values": ai_model["values"],
            "reasoning_style": ai_model["reasoning_style"],
            "blind_spots": ai_model["blind_spots"],
        }

    # Cross-alignment: latest scores
    latest_score = local_db.get_latest_score(user_id)
    alignment = {}
    if latest_score:
        alignment = {
            "gameplay_id": latest_score["gameplay_id"],
            "gameplay_version": latest_score["gameplay_version"],
            "scoring_system_id": latest_score["scoring_system_id"],
            "scoring_system_version": latest_score["scoring_system_version"],
            "scores": latest_score["scores"],
            "stage": latest_score["stage"],
            "date": latest_score["date"],
        }

    # AI self-accuracy gaps
    accuracy_records = local_db.get_ai_self_accuracy(user_id, limit=10)
    accuracy_gaps = [{"dimension": r["dimension"], "gap": r["gap"],
                      "self_score": r["self_score"], "user_score": r["user_score"]}
                     for r in accuracy_records]

    return {
        "user_id": user_id,
        "human_dna": human_dna,
        "ai_dna": ai_dna,
        "alignment": alignment,
        "accuracy_gaps": accuracy_gaps,
    }


@router.get("/{user_id}/evolution")
def evolution_curve(user_id: str, limit: int = 30):
    """Score evolution over time — L0→L4 timeline."""
    history = local_db.get_score_history(user_id, limit=limit)
    if not history:
        raise HTTPException(404, f"No score history for user '{user_id}'")

    from ..routers.scoring import _compute_total, _determine_stage
    timeline = []
    for entry in history:
        total = _compute_total(entry["scores"])
        stage = _determine_stage(total)
        timeline.append({
            "date": entry["date"],
            "total": total,
            "stage": stage,
            "gameplay_id": entry["gameplay_id"],
            "scores": entry["scores"],
        })

    return {"user_id": user_id, "timeline": timeline, "count": len(timeline)}
