#!/usr/bin/env python3
"""Create a markdown-first gameplay draft under the local user workspace."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT.parent / "self_consciousness_backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.user_data import ensure_user_workspace, get_user_gameplay_drafts_dir  # noqa: E402


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _load_spec(args) -> dict:
    if args.spec_json:
        return json.loads(args.spec_json)
    if args.spec_file:
        return json.loads(Path(args.spec_file).read_text(encoding="utf-8"))
    raise SystemExit("Provide --spec-file or --spec-json")


def _synthesize_markdown(spec: dict) -> str:
    loop = spec.get("loop", {})
    phases = loop.get("phases", [])
    lines = [
        f"# {spec.get('name_zh') or spec['name']}",
        "",
        spec.get("summary", "").strip(),
        "",
        "## Loop",
        "",
        f"- cadence: `{loop.get('cadence', 'session')}`",
        f"- participants: `{loop.get('participants', 'solo')}`",
        "",
        "## Phases",
        "",
    ]
    for phase in phases:
        lines.append(f"- `{phase.get('id', 'phase')}`: {phase.get('goal', '').strip()}")
    architecture = spec.get("consciousness_architecture") or {}
    if architecture:
        lines.extend([
            "",
            "## Consciousness Architecture",
            "",
            architecture.get("description", "").strip() or "Optional lens.",
        ])
        dims = architecture.get("dimensions") or []
        if dims:
            lines.append(f"- dimensions: `{', '.join(dims)}`")
    return "\n".join(lines).strip() + "\n"


def _normalize_spec(spec: dict) -> dict:
    required = ["id", "name", "summary"]
    missing = [field for field in required if not str(spec.get(field, "")).strip()]
    if missing:
        raise SystemExit(f"Missing required spec fields: {', '.join(missing)}")

    normalized = {
        "id": spec["id"],
        "name": spec["name"],
        "name_zh": spec.get("name_zh", ""),
        "summary": spec["summary"],
        "consciousness_architecture": spec.get("consciousness_architecture"),
        "loop": spec.get("loop", {}),
        "interfaces": spec.get("interfaces", {}),
        "required_tools": spec.get("required_tools", []),
        "difficulty": spec.get("difficulty", ""),
        "tags": spec.get("tags", []),
        "created_at": spec.get("created_at") or _now(),
    }
    body = spec.get("markdown") or spec.get("body") or _synthesize_markdown(normalized)
    return normalized, body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--spec-file")
    parser.add_argument("--spec-json")
    parser.add_argument("--output-dir")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    spec = _load_spec(args)
    normalized, body = _normalize_spec(spec)
    ensure_user_workspace(args.user_id)
    output_dir = Path(args.output_dir) if args.output_dir else get_user_gameplay_drafts_dir(args.user_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{normalized['id']}.md"
    if output_path.exists() and not args.force:
        raise SystemExit(f"Draft already exists: {output_path}")

    content = f"---\n{json.dumps(normalized, ensure_ascii=False, indent=2)}\n---\n\n{body.rstrip()}\n"
    output_path.write_text(content, encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "path": str(output_path),
                "user_id": args.user_id,
                "gameplay_id": normalized["id"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
