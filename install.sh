#!/usr/bin/env bash
set -euo pipefail

OWNER_REPO="guanqunpolyversestudio-rgb/self-consciousness-protocol"
REF="main"
SKILLS_DIR="${OPENCLAW_SKILLS_DIR:-}"
DEFAULT_BACKEND_URL="https://self-consciousness-backend.onrender.com"

usage() {
  cat <<'EOF'
Usage:
  bash install.sh --skills-dir /path/to/openclaw/skills [--ref main]

Options:
  --skills-dir   Target OpenClaw skills directory
  --ref          Git ref to download from (default: main)

Environment:
  OPENCLAW_SKILLS_DIR can be used instead of --skills-dir
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skills-dir)
      SKILLS_DIR="${2:-}"
      shift 2
      ;;
    --ref)
      REF="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${SKILLS_DIR}" ]]; then
  echo "Missing OpenClaw skills directory." >&2
  usage >&2
  exit 1
fi

RAW_BASE="https://raw.githubusercontent.com/${OWNER_REPO}/${REF}"
TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

mkdir -p "${TMP_DIR}/gameplay-creator/references" "${TMP_DIR}/gameplay-creator/scripts"

curl -fsSL "${RAW_BASE}/SKILL.md" -o "${TMP_DIR}/SKILL.md"
curl -fsSL "${RAW_BASE}/gameplay-creator/SKILL.md" -o "${TMP_DIR}/gameplay-creator/SKILL.md"
curl -fsSL "${RAW_BASE}/gameplay-creator/references/gameplay-spec.md" -o "${TMP_DIR}/gameplay-creator/references/gameplay-spec.md"
curl -fsSL "${RAW_BASE}/gameplay-creator/scripts/create_gameplay_draft.py" -o "${TMP_DIR}/gameplay-creator/scripts/create_gameplay_draft.py"

mkdir -p "${SKILLS_DIR}/self-consciousness" "${SKILLS_DIR}/gameplay-creator"
rsync -a "${TMP_DIR}/SKILL.md" "${SKILLS_DIR}/self-consciousness/SKILL.md"
rsync -a --delete "${TMP_DIR}/gameplay-creator/" "${SKILLS_DIR}/gameplay-creator/"

mkdir -p "${HOME}/.self-consciousness"

python3 - <<PY
import json
from pathlib import Path

profile_path = Path.home() / ".self-consciousness" / "profile.json"
default_backend = "${DEFAULT_BACKEND_URL}"

if profile_path.exists():
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        profile = {}
else:
    profile = {}

profile.setdefault("current_user_id", "")
profile.setdefault("users", {})
profile.setdefault("updated_at", "")
legacy_local = {
    "",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://127.0.0.1:8000",
    "https://localhost:8000",
}
if profile.get("backend_base_url", "") in legacy_local:
    profile["backend_base_url"] = default_backend

profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
PY

cat <<EOF
Installed:
- ${SKILLS_DIR}/self-consciousness/SKILL.md
- ${SKILLS_DIR}/gameplay-creator/

Initialized:
- ${HOME}/.self-consciousness
- ${HOME}/.self-consciousness/profile.json

Next:
1. Restart OpenClaw if it caches skills.
2. Default shared backend is ${DEFAULT_BACKEND_URL}
3. Ask OpenClaw to run self-consciousness onboarding.
EOF
