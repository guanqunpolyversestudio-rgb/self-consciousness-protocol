#!/usr/bin/env bash
set -euo pipefail

OWNER_REPO="guanqunpolyversestudio-rgb/self-consciousness-protocol"
REF="main"
DEFAULT_BACKEND_URL="https://self-consciousness-backend.onrender.com"
CLI_NAME="selfcon"
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
RELEASE_BASE="https://github.com/${OWNER_REPO}/releases/download"
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
PLATFORM="$(printf '%s' "${OS}" | tr '[:upper:]' '[:lower:]')"
ASSET_NAME="${CLI_NAME}-${VERSION}-${PLATFORM}-${ARCH}.tar.gz"
ASSET_URL="${RELEASE_BASE}/v${VERSION}/${ASSET_NAME}"

mkdir -p "${TMP_VERSION_DIR}" "${BIN_DIR}"

if ! curl -fsSL "${ASSET_URL}" -o "${TMP_ROOT}/${ASSET_NAME}"; then
  echo "Failed to download ${ASSET_URL}" >&2
  echo "Make sure release v${VERSION} contains ${ASSET_NAME}." >&2
  exit 1
fi

tar -xzf "${TMP_ROOT}/${ASSET_NAME}" -C "${TMP_VERSION_DIR}"

rm -rf "${FINAL_VERSION_DIR}"
mkdir -p "${INSTALL_BASE}"
mv "${TMP_VERSION_DIR}" "${FINAL_VERSION_DIR}"

ln -sfn "${FINAL_VERSION_DIR}/${CLI_NAME}" "${BIN_DIR}/${CLI_NAME}"

if [[ -n "${SKILLS_DIR}" ]]; then
  "${BIN_DIR}/${CLI_NAME}" install --skills-dir "${SKILLS_DIR}" --backend-url "${DEFAULT_BACKEND_URL}"
fi

cat <<EOF
Installed ${CLI_NAME} ${VERSION} for ${OS}/${ARCH}

CLI:
- ${BIN_DIR}/${CLI_NAME}

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
