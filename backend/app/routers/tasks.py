"""DB 4: Alignment Tasks — /api/v1/tasks"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .. import db

router = APIRouter()


class CreateRequest(BaseModel):
    user_id: str
    proposer_type: str = "user"
    title: str = ""
    description: str = ""
    summary: str = ""
    gameplay_id: str = ""
    framework_id: str = ""
    dimension_id: str = ""
    desired_outcome: str = ""
    current_gap: str = ""
    acceptance_criteria: list[str] = []
    context_notes: str = ""
    deliverable_format: str = "playbook"
    task_type: str = "alignment"
    price: int = 5
    review_reward: int = 1
    tags: list[str] = []


class SolveRequest(BaseModel):
    user_id: str
    solution: str = ""
    summary: str = ""
    approach: str = ""
    steps: list[str] = []
    user_message: str = ""
    expected_outcome: str = ""
    evidence: list[str] = []
    notes: str = ""


class ReviewRequest(BaseModel):
    reviewer_id: str
    problem_fit: Optional[float] = None     # 0-10
    resonance: Optional[float] = None       # backward-compatible alias
    depth: float = 0           # 0-10
    actionability: float = 0   # 0-10
    verifiability: Optional[float] = None   # 0-10
    novelty: Optional[float] = None         # backward-compatible alias
    recommendation: str = "revise"
    notes: str = ""
    concern_flags: list[str] = []


class SettleRequest(BaseModel):
    user_id: str = ""


# ── CRUD ───────────────────────────────────────────────

@router.post("")
def create(req: CreateRequest):
    summary = req.summary or req.description
    if not summary:
        raise HTTPException(400, "Task must have summary or description")
    if req.price <= 0:
        raise HTTPException(400, "Task price must be > 0")
    if req.review_reward < 0:
        raise HTTPException(400, "Review reward must be >= 0")

    # Lock bounty into escrow.
    balance = db.get_balance(req.user_id)
    if balance < req.price:
        raise HTTPException(400, f"Insufficient credits: have {balance}, need {req.price}")
    db.add_credit(req.user_id, "deduct", -req.price, "Submit alignment task bounty")

    task = db.create_task(
        user_id=req.user_id,
        title=req.title,
        summary=summary,
        proposer_type=req.proposer_type,
        gameplay_id=req.gameplay_id or req.framework_id,
        dimension_id=req.dimension_id,
        desired_outcome=req.desired_outcome,
        current_gap=req.current_gap,
        acceptance_criteria=req.acceptance_criteria,
        context_notes=req.context_notes,
        deliverable_format=req.deliverable_format,
        task_type=req.task_type,
        price=req.price,
        review_reward=req.review_reward,
        tags=req.tags,
    )
    return {"ok": True, "task": task, "credit_deducted": req.price}


@router.get("")
def list_all(status: Optional[str] = None, limit: int = 50):
    return {"tasks": db.list_tasks(status, limit)}


@router.get("/recommend")
def recommend(user_id: str, limit: int = 5):
    return {"tasks": db.recommend_tasks(user_id, limit)}


@router.get("/{task_id}")
def get_one(task_id: str):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@router.post("/{task_id}/claim")
def claim(task_id: str, user_id: str):
    task = db.claim_task(task_id, user_id)
    if not task:
        raise HTTPException(400, f"Task '{task_id}' not available for claiming (not open or not found)")
    return {"ok": True, "task": task}


@router.post("/{task_id}/solve")
def solve(task_id: str, req: SolveRequest):
    solution_payload = {
        "summary": req.summary or req.solution,
        "approach": req.approach,
        "steps": req.steps,
        "user_message": req.user_message or req.solution,
        "expected_outcome": req.expected_outcome,
        "evidence": req.evidence,
        "notes": req.notes,
    }
    if not solution_payload["summary"]:
        raise HTTPException(400, "Solution must include summary or solution text")

    task = db.solve_task(task_id, req.user_id, solution_payload)
    if not task:
        raise HTTPException(400, f"Task '{task_id}' not available for solving (not claimed by this user or not found)")

    # Auto-submit for review
    db.submit_for_review(task_id)
    return {"ok": True, "task": {**task, "status": "reviewing"}, "status": "submitted_for_review"}


@router.post("/{task_id}/review")
def review(task_id: str, req: ReviewRequest):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    if task["status"] != "reviewing":
        raise HTTPException(400, f"Task '{task_id}' is not in reviewing status")
    if req.reviewer_id == task["user_id"] or req.reviewer_id == task["claimed_by"]:
        raise HTTPException(400, "Cannot review your own task or your own solution")

    problem_fit = req.problem_fit if req.problem_fit is not None else (req.resonance or 0)
    verifiability = req.verifiability if req.verifiability is not None else (req.novelty or 0)
    review_result = db.add_review(
        task_id,
        req.reviewer_id,
        problem_fit,
        req.depth,
        req.actionability,
        verifiability,
        recommendation=req.recommendation,
        notes=req.notes,
        concern_flags=req.concern_flags,
    )

    # Check if verification threshold reached
    check = db.check_verification(task_id)
    if check.get("verified"):
        db.verify_task(task_id, "verified")
        return {"ok": True, "review": review_result, "verification": "verified", "settlement_status": "ready"}
    elif check["total_reviews"] >= 5 and not check["verified"]:
        db.verify_task(task_id, "rejected")
        return {"ok": True, "review": review_result, "verification": "rejected", "settlement_status": "ready"}

    return {"ok": True, "review": review_result, "verification": "pending", "needs_more": check.get("needs_more", 0)}


@router.get("/{task_id}/reviews")
def get_reviews(task_id: str):
    reviews = db.get_reviews(task_id)
    check = db.check_verification(task_id)
    return {"task_id": task_id, "reviews": reviews, "verification": check}


@router.post("/{task_id}/settle")
def settle(task_id: str, req: SettleRequest):
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    if req.user_id and req.user_id != task["user_id"]:
        raise HTTPException(403, "Only the task proposer can settle this task")

    result = db.settle_task(task_id)
    if not result:
        raise HTTPException(400, f"Task '{task_id}' is not ready for settlement")
    return {"ok": True, **result}
