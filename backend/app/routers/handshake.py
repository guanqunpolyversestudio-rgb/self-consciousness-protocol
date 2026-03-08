"""Handshake — /api/v1/handshake"""
from fastapi import APIRouter
from pydantic import BaseModel

from ..onboarding_service import register_user_context

router = APIRouter()


class HandshakeRequest(BaseModel):
    user_id: str


@router.post("")
def handshake(req: HandshakeRequest):
    """Backward-compatible alias for first-time registration."""
    return register_user_context(req.user_id)
