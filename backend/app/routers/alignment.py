"""Daily Alignment — /api/v1/alignment"""
from __future__ import annotations

from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import db, local_db

router = APIRouter()

DEFAULT_DIMENSIONS = ["purpose", "direction", "constraints", "evaluation", "interaction"]


class QuestionSetRequest(BaseModel):
    theme: str = ""


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    dimension: str = ""
    question: str = ""
    agent_answer: str
    user_answer: str = ""
    user_match: Optional[bool] = None
    notes: str = ""


class AskRequest(BaseModel):
    session_id: str
    asker: str
    question: str
    answer: str = ""
    dimension: str = ""


def _current_dimensions(user_id: str) -> list[str]:
    current = local_db.get_current_gameplay(user_id)
    architecture = {}
    if current:
        architecture = current["gameplay"].get("consciousness_architecture") or {}
    dimensions = architecture.get("dimensions") or DEFAULT_DIMENSIONS
    return dimensions[:5]


def _question_templates(user_id: str, theme: str = "") -> list[dict]:
    dims = _current_dimensions(user_id)
    current_score = local_db.get_latest_score(user_id) or {}
    stage = current_score.get("stage", "L0")
    themed_prefix = f"[{theme}] " if theme else ""
    prompts = [
        {
            "dimension": dims[0],
            "prompt": f"{themed_prefix}如果我现在替你说出你最在意的 {dims[0]}，我应该怎么说才最像你自己的第一反应？",
        },
        {
            "dimension": dims[min(1, len(dims) - 1)],
            "prompt": f"{themed_prefix}如果今天只能推进一个 {dims[min(1, len(dims) - 1)]} 相关动作，你的直觉会选什么？",
        },
        {
            "dimension": "bidirectional",
            "prompt": f"{themed_prefix}当前对齐阶段约为 {stage}。你最想反问 agent 哪个意识判断，来检验它是否真的懂你？",
        },
    ]
    return [
        {"id": f"q{i+1}", **item}
        for i, item in enumerate(prompts)
    ]


def _alignment_history(user_id: str, limit: int = 100) -> list[dict]:
    records = local_db.get_consciousness_records(user_id, limit=limit)
    filtered = []
    for item in records:
        payload = item.get("payload", {})
        if payload.get("session_kind") != "daily_alignment":
            continue
        filtered.append(item)
    return filtered


@router.post("/{user_id}/question-set")
def question_set(user_id: str, req: QuestionSetRequest):
    if not db.get_user(user_id):
        raise HTTPException(404, f"User '{user_id}' not registered")

    session_id = f"aln_{uuid4().hex[:10]}"
    questions = _question_templates(user_id, req.theme)
    for question in questions:
        local_db.insert_consciousness_record(
            user_id,
            subject_type="relationship",
            record_type="question",
            content=question["prompt"],
            dimension=question["dimension"],
            trigger="daily_alignment",
            payload={
                "session_kind": "daily_alignment",
                "session_id": session_id,
                "question_id": question["id"],
                "role": "agent_to_user",
            },
            context="daily_alignment.question_set",
        )
    return {
        "ok": True,
        "session_id": session_id,
        "theme": req.theme or "intuition-mirror",
        "questions": questions,
        "game_layer": {
            "mode": "blind_guess_streak",
            "instruction": "agent 先猜，再由 user 判断命中与否；每次只求更接近，不求一次全对。",
        },
    }


@router.post("/{user_id}/answer")
def answer(user_id: str, req: AnswerRequest):
    if not db.get_user(user_id):
        raise HTTPException(404, f"User '{user_id}' not registered")

    local_db.insert_consciousness_record(
        user_id,
        subject_type="human",
        record_type="intuition_guess",
        content=req.agent_answer,
        dimension=req.dimension,
        trigger="daily_alignment",
        payload={
            "session_kind": "daily_alignment",
            "session_id": req.session_id,
            "question_id": req.question_id,
            "question": req.question,
            "source": "agent",
        },
        context="daily_alignment.agent_guess",
        confidence=0.7,
    )
    if req.user_answer:
        local_db.insert_consciousness_record(
            user_id,
            subject_type="human",
            record_type="answer",
            content=req.user_answer,
            dimension=req.dimension,
            trigger="daily_alignment",
            payload={
                "session_kind": "daily_alignment",
                "session_id": req.session_id,
                "question_id": req.question_id,
                "question": req.question,
                "source": "user",
                "user_match": req.user_match,
            },
            context="daily_alignment.user_answer",
        )
    if req.user_match is not None or req.notes:
        local_db.insert_consciousness_record(
            user_id,
            subject_type="relationship",
            record_type="feedback",
            content=req.notes or ("match" if req.user_match else "mismatch"),
            dimension=req.dimension,
            trigger="daily_alignment",
            payload={
                "session_kind": "daily_alignment",
                "session_id": req.session_id,
                "question_id": req.question_id,
                "user_match": req.user_match,
            },
            context="daily_alignment.feedback",
        )
    return {
        "ok": True,
        "session_id": req.session_id,
        "question_id": req.question_id,
        "user_match": req.user_match,
    }


@router.post("/{user_id}/ask")
def ask(user_id: str, req: AskRequest):
    if req.asker not in {"agent", "user"}:
        raise HTTPException(400, "asker must be 'agent' or 'user'")
    if not db.get_user(user_id):
        raise HTTPException(404, f"User '{user_id}' not registered")

    local_db.insert_consciousness_record(
        user_id,
        subject_type="relationship",
        record_type="question",
        content=req.question,
        dimension=req.dimension,
        trigger="daily_alignment",
        payload={
            "session_kind": "daily_alignment",
            "session_id": req.session_id,
            "role": f"{req.asker}_question",
        },
        context="daily_alignment.ask",
    )
    if req.answer:
        local_db.insert_consciousness_record(
            user_id,
            subject_type="relationship",
            record_type="answer",
            content=req.answer,
            dimension=req.dimension,
            trigger="daily_alignment",
            payload={
                "session_kind": "daily_alignment",
                "session_id": req.session_id,
                "role": f"{req.asker}_answer",
            },
            context="daily_alignment.ask",
        )
    return {"ok": True, "session_id": req.session_id, "asker": req.asker}


@router.get("/{user_id}/history")
def history(user_id: str, limit: int = 100):
    records = _alignment_history(user_id, limit=limit)
    return {
        "user_id": user_id,
        "records": records,
        "count": len(records),
    }
