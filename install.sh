#!/usr/bin/env bash
set -euo pipefail

OWNER_REPO="guanqunpolyversestudio-rgb/self-consciousness-protocol"
REF="main"
DEFAULT_BACKEND_URL="https://self-consciousness-backend.onrender.com"
CLI_NAME="selfcon"
CLI_ALIAS="self-consciousness"
SKILLS_DIR="${OPENCLAW_SKILLS_DIR:-}"

usage() {
  cat <<'EOF'
Usage:
  curl -fsSL <install-url> | bash -s -- [--skills-dir /path/to/openclaw/skills] [--ref main]

Options:
  --skills-dir   Optional OpenClaw skills directory. If provided, the installer
                 also runs `selfcon install --skills-dir ...`
  --ref          Git ref to download from (default: main)
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

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required to run ${CLI_NAME}. Please install Node.js 20+ and retry." >&2
  exit 1
fi

OS="$(uname -s)"
ARCH="$(uname -m)"
case "${OS}" in
  Darwin|Linux) ;;
  *)
    echo "Unsupported OS: ${OS}. Only Darwin and Linux are supported." >&2
    exit 1
    ;;
esac
case "${ARCH}" in
  arm64|aarch64) ARCH="arm64" ;;
  x86_64) ARCH="x64" ;;
  *)
    echo "Unsupported architecture: ${ARCH}. Only x64 and arm64 are supported." >&2
    exit 1
    ;;
esac

RAW_BASE="https://raw.githubusercontent.com/${OWNER_REPO}/${REF}"
TMP_ROOT="$(mktemp -d)"
cleanup() {
  rm -rf "${TMP_ROOT}"
}
trap cleanup EXIT

curl -fsSL "${RAW_BASE}/cli/package.json" -o "${TMP_ROOT}/package.json"
VERSION="$(python3 - <<'PY' "${TMP_ROOT}/package.json"
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(data["version"])
PY
)"

INSTALL_BASE="${HOME}/.local/share/${CLI_NAME}/versions"
TMP_VERSION_DIR="${INSTALL_BASE}/.tmp-${VERSION}-$(date +%s)"
FINAL_VERSION_DIR="${INSTALL_BASE}/${VERSION}"
BIN_DIR="${HOME}/.local/bin"

mkdir -p "${TMP_VERSION_DIR}/dist" \
         "${TMP_VERSION_DIR}/share/skills/self-consciousness" \
         "${TMP_VERSION_DIR}/share/skills/gameplay-creator/references" \
         "${TMP_VERSION_DIR}/share/skills/gameplay-creator/scripts" \
         "${BIN_DIR}"

curl -fsSL "${RAW_BASE}/cli/dist/index.js" -o "${TMP_VERSION_DIR}/dist/index.js"
curl -fsSL "${RAW_BASE}/SKILL.md" -o "${TMP_VERSION_DIR}/share/skills/self-consciousness/SKILL.md"
curl -fsSL "${RAW_BASE}/gameplay-creator/SKILL.md" -o "${TMP_VERSION_DIR}/share/skills/gameplay-creator/SKILL.md"
curl -fsSL "${RAW_BASE}/gameplay-creator/references/gameplay-spec.md" -o "${TMP_VERSION_DIR}/share/skills/gameplay-creator/references/gameplay-spec.md"
curl -fsSL "${RAW_BASE}/gameplay-creator/scripts/create_gameplay_draft.py" -o "${TMP_VERSION_DIR}/share/skills/gameplay-creator/scripts/create_gameplay_draft.py"
cp "${TMP_ROOT}/package.json" "${TMP_VERSION_DIR}/package.json"

cat > "${TMP_VERSION_DIR}/${CLI_NAME}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec node "${FINAL_VERSION_DIR}/dist/index.js" "\$@"
EOF
chmod +x "${TMP_VERSION_DIR}/${CLI_NAME}"

rm -rf "${FINAL_VERSION_DIR}"
mkdir -p "${INSTALL_BASE}"
mv "${TMP_VERSION_DIR}" "${FINAL_VERSION_DIR}"

ln -sfn "${FINAL_VERSION_DIR}/${CLI_NAME}" "${BIN_DIR}/${CLI_NAME}"
ln -sfn "${FINAL_VERSION_DIR}/${CLI_NAME}" "${BIN_DIR}/${CLI_ALIAS}"

if [[ -n "${SKILLS_DIR}" ]]; then
  "${BIN_DIR}/${CLI_NAME}" install --skills-dir "${SKILLS_DIR}" --backend-url "${DEFAULT_BACKEND_URL}"
fi

cat <<EOF
Installed ${CLI_NAME} ${VERSION} for ${OS}/${ARCH}

CLI:
- ${BIN_DIR}/${CLI_NAME}
- ${BIN_DIR}/${CLI_ALIAS}

Version dir:
- ${FINAL_VERSION_DIR}

Default shared backend:
- ${DEFAULT_BACKEND_URL}

Next:
1. Ensure ${BIN_DIR} is in your PATH.
2. If you passed --skills-dir, the skills are already installed.
3. Run:
   ${CLI_NAME} onboard --user-id <your_user_id>
EOF

case ":$PATH:" in
  *":${BIN_DIR}:"*) ;;
  *)
    echo
    echo "PATH note: ${BIN_DIR} is not currently on PATH."
    echo "Add this to your shell profile if needed:"
    echo "  export PATH=\"${BIN_DIR}:\$PATH\""
    ;;
esac
