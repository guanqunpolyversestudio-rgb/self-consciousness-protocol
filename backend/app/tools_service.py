"""Application service for tool execution and media job lifecycle."""
from __future__ import annotations

from typing import Any, Optional

from . import db
from .tools_gateway import get_capability, get_wavespeed_api_key
from .wavespeed_client import WaveSpeedError, get_prediction_result, submit_prediction

TERMINAL_STATUSES = {"completed", "failed"}


class ToolServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _extract_prediction_id(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("id", "prediction_id", "request_id", "task_id"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        for value in payload.values():
            prediction_id = _extract_prediction_id(value)
            if prediction_id:
                return prediction_id
    if isinstance(payload, list):
        for item in payload:
            prediction_id = _extract_prediction_id(item)
            if prediction_id:
                return prediction_id
    return ""


def _extract_output_urls(payload: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"url", "file_url", "download_url", "image_url", "video_url"} and isinstance(value, str):
                urls.append(value)
            elif key in {"images", "videos", "outputs", "artifacts", "files", "results"}:
                urls.extend(_extract_output_urls(value))
            elif isinstance(value, (dict, list)):
                urls.extend(_extract_output_urls(value))
    elif isinstance(payload, list):
        for item in payload:
            urls.extend(_extract_output_urls(item))
    return list(dict.fromkeys(url for url in urls if url.startswith("http")))


def _normalize_status(payload: dict, default: str = "processing") -> str:
    raw = (
        payload.get("status")
        or payload.get("state")
        or payload.get("task_status")
        or payload.get("result", {}).get("status")
        or default
    )
    normalized = str(raw).strip().lower()
    if normalized in {"queued", "pending", "created"}:
        return "submitted"
    if normalized in {"submitted", "processing", "running", "in_progress", "starting"}:
        return "processing"
    if normalized in {"completed", "succeeded", "success", "done"}:
        return "completed"
    if normalized in {"failed", "error", "canceled", "cancelled"}:
        return "failed"
    return default


def _refund_media_job(job: dict, reason: str) -> dict:
    refunded_amount = int(job.get("refunded_amount", 0))
    credit_cost = int(job.get("credit_cost", 0))
    if refunded_amount >= credit_cost:
        return db.update_media_job(job["id"], status="failed", error=reason) or job
    if credit_cost > 0:
        db.add_credit(job["user_id"], "earn", credit_cost, f"Refund media job: {job['id']}")
    return db.update_media_job(
        job["id"],
        status="failed",
        error=reason,
        refunded_amount=credit_cost,
    ) or job


def submit_media_request(
    *,
    user_id: str,
    capability_id: str,
    prompt: str,
    gameplay_id: str = "",
    params: Optional[dict] = None,
    model: str = "",
) -> dict:
    capability = get_capability(capability_id)
    if not capability:
        raise ToolServiceError(f"Unsupported capability: {capability_id}", status_code=404)
    if capability["default_provider"] != "wavespeed":
        raise ToolServiceError(f"No provider wired for capability: {capability_id}", status_code=503)

    api_key = get_wavespeed_api_key()
    if not api_key:
        raise ToolServiceError("WaveSpeed is not configured", status_code=503)

    credit_cost = int(capability["credit_cost"])
    balance = db.get_balance(user_id)
    if balance < credit_cost:
        raise ToolServiceError(
            f"Insufficient credits: have {balance}, need {credit_cost}",
            status_code=400,
        )

    selected_model = model or capability["default_model"]
    db.add_credit(user_id, "deduct", -credit_cost, f"{capability_id} via {selected_model}")
    job = db.create_media_job(
        user_id,
        capability_id,
        capability["default_provider"],
        selected_model,
        prompt,
        gameplay_id=gameplay_id,
        params=params or {},
        credit_cost=credit_cost,
        status="queued",
    )
    try:
        provider_payload = submit_prediction(
            api_key=api_key,
            model=selected_model,
            prompt=prompt,
            params=params or {},
        )
    except WaveSpeedError as exc:
        return _refund_media_job(job, str(exc))

    provider_job_id = _extract_prediction_id(provider_payload)
    output_urls = _extract_output_urls(provider_payload)
    status = _normalize_status(provider_payload, default="submitted")
    if status == "failed":
        error_text = str(provider_payload.get("error") or provider_payload.get("message") or "Provider failed")
        return _refund_media_job(job, error_text)
    return db.update_media_job(
        job["id"],
        provider_job_id=provider_job_id,
        provider_result_url=output_urls[0] if output_urls else "",
        output_urls=output_urls,
        status="completed" if output_urls else status,
        error="",
    ) or job


def refresh_media_job(job_id: str) -> Optional[dict]:
    job = db.get_media_job(job_id)
    if not job:
        return None
    if job["status"] in TERMINAL_STATUSES or not job.get("provider_job_id"):
        return job
    if job["provider"] != "wavespeed":
        return job

    api_key = get_wavespeed_api_key()
    if not api_key:
        return job

    try:
        provider_payload = get_prediction_result(
            api_key=api_key,
            prediction_id=job["provider_job_id"],
        )
    except WaveSpeedError as exc:
        return _refund_media_job(job, str(exc))

    status = _normalize_status(provider_payload)
    output_urls = _extract_output_urls(provider_payload)
    error_text = ""
    if status == "failed":
        error_text = str(provider_payload.get("error") or provider_payload.get("message") or "Provider failed")
        return _refund_media_job(job, error_text)

    return db.update_media_job(
        job_id,
        status="completed" if output_urls else status,
        provider_result_url=output_urls[0] if output_urls else job.get("provider_result_url", ""),
        output_urls=output_urls or job.get("output_urls", []),
        error=error_text,
    )
