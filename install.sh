#!/usr/bin/env bash
set -euo pipefail

OWNER_REPO="guanqunpolyversestudio-rgb/self-consciousness-protocol"
REF="main"
SKILLS_DIR="${OPENCLAW_SKILLS_DIR:-}"

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

cat <<EOF
Installed:
- ${SKILLS_DIR}/self-consciousness/SKILL.md
- ${SKILLS_DIR}/gameplay-creator/

Initialized:
- ${HOME}/.self-consciousness

Next:
1. Restart OpenClaw if it caches skills.
2. Ask OpenClaw to run self-consciousness onboarding.
EOF
