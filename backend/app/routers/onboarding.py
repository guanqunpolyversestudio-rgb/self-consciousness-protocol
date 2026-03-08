"""Onboarding — /api/v1/onboarding"""
from fastapi import APIRouter
from pydantic import BaseModel

from ..onboarding_service import DEFAULT_ONBOARDING_MODE, register_user_context, save_user_preference

router = APIRouter()


class RegisterRequest(BaseModel):
    user_id: str
    backend_base_url: str = ""
    onboarding_mode: str = DEFAULT_ONBOARDING_MODE


class PreferenceRequest(BaseModel):
    user_id: str
    onboarding_mode: str
    final_answer_format: str = ""
    notes: str = ""
    preferred_gameplay_ids: list[str] = []


@router.post("/register")
def register(req: RegisterRequest):
    return register_user_context(
        req.user_id,
        backend_base_url=req.backend_base_url,
        onboarding_mode=req.onboarding_mode,
    )


@router.post("/preference")
def preference(req: PreferenceRequest):
    return save_user_preference(
        req.user_id,
        onboarding_mode=req.onboarding_mode,
        preference_payload={
            "final_answer_format": req.final_answer_format,
            "notes": req.notes,
            "preferred_gameplay_ids": req.preferred_gameplay_ids,
        },
    )
