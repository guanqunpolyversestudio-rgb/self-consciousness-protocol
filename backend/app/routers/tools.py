"""Tools gateway — /api/v1/tools"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..tools_gateway import list_capabilities
from ..tools_service import ToolServiceError, refresh_media_job, submit_media_request

router = APIRouter()


class GenerateRequest(BaseModel):
    user_id: str
    prompt: str
    gameplay_id: str = ""
    model: str = ""
    params: dict = {}


@router.get("/capabilities")
def capabilities():
    return {"capabilities": list_capabilities()}


@router.post("/image/generate")
def generate_image(req: GenerateRequest):
    try:
        job = submit_media_request(
            user_id=req.user_id,
            capability_id="image.generate",
            prompt=req.prompt,
            gameplay_id=req.gameplay_id,
            model=req.model,
            params=req.params,
        )
    except ToolServiceError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    return {"ok": True, "job": job}


@router.post("/video/generate")
def generate_video(req: GenerateRequest):
    try:
        job = submit_media_request(
            user_id=req.user_id,
            capability_id="video.generate",
            prompt=req.prompt,
            gameplay_id=req.gameplay_id,
            model=req.model,
            params=req.params,
        )
    except ToolServiceError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    return {"ok": True, "job": job}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = refresh_media_job(job_id)
    if not job:
        raise HTTPException(404, f"Media job '{job_id}' not found")
    return {"job": job}
