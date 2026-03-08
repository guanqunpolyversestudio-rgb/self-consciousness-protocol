"""Minimal WaveSpeed client using the official async prediction flow.

Primary source:
https://wavespeed.ai/docs/docs-api/get-started
https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v3
"""
from __future__ import annotations

import json
from typing import Optional
from urllib import error, request

BASE_URL = "https://api.wavespeed.ai/api/v3"


class WaveSpeedError(RuntimeError):
    pass


def _http_json(url: str, *, method: str = "GET", payload: Optional[dict] = None, api_key: str) -> dict:
    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=body, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise WaveSpeedError(f"WaveSpeed HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise WaveSpeedError(f"WaveSpeed request failed: {exc.reason}") from exc

    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WaveSpeedError(f"WaveSpeed returned invalid JSON: {raw[:200]}") from exc


def submit_prediction(*, api_key: str, model: str, prompt: str, params: Optional[dict] = None) -> dict:
    payload = {"prompt": prompt, **(params or {})}
    return _http_json(f"{BASE_URL}/{model}", method="POST", payload=payload, api_key=api_key)


def get_prediction_result(*, api_key: str, prediction_id: str) -> dict:
    return _http_json(f"{BASE_URL}/predictions/{prediction_id}/result", api_key=api_key)
