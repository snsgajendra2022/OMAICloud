#!/usr/bin/env bash
# Start the OM AI web workspace using OM's native model only.
# Run from any directory: bash /path/to/OMAICloud/scripts/start_om_workspace.sh
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

fail() { printf '\n[OM AI] ERROR: %s\n' "$*" >&2; exit 1; }
info() { printf '[OM AI] %s\n' "$*"; }

command -v python3 >/dev/null 2>&1 || fail "Python 3 is required. Install Python 3.11 or newer."
PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || fail "Python 3.11+ is required; found $PYTHON_VERSION."

if [[ ! -d .venv ]]; then
  info "Creating project virtual environment (.venv)…"
  python3 -m venv .venv || fail "Could not create .venv. Install the Python venv/ensurepip package and retry."
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip

if ! python -c 'import fastapi, torch, uvicorn, om_ai' >/dev/null 2>&1 || ! command -v om-ai >/dev/null 2>&1; then
  info "Installing OM AI and development dependencies. First install can take several minutes."
  python -m pip install -e '.[dev]' || fail "Dependency installation failed. Review the pip error above."
fi

# Enforce native OM for this process. Do not fall back to a hosted LLM.
export OM_MODEL_PROVIDER=om_native
export OM_AI_CHAT_BACKEND=om_native
export OM_NATIVE_MODEL_FIRST=1
export OM_CHAT_PIPELINE=1
export OM_CHATGPT_RUNTIME=1
export OM_UNIVERSAL_INTELLIGENCE=1
export OM_COGNITIVE_INTELLIGENCE=1
export OM_AI_AUTOLOAD=1
export OM_MODEL_ID="${OM_MODEL_ID:-OM-1.0}"
export OM_MODEL_CONFIG="${OM_MODEL_CONFIG:-configs/om-1.0-local.json}"
export OM_MODEL_TOKENIZER="${OM_MODEL_TOKENIZER:-artifacts/tokenizer-production-65536.json}"
export OM_MODEL_CHECKPOINT="${OM_MODEL_CHECKPOINT:-artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt}"

mkdir -p artifacts

info "Repository: $REPO_ROOT"
info "Python: $(python --version 2>&1)"
info "Chat provider: $OM_AI_CHAT_BACKEND (hosted LLM fallback disabled)"
info "Chat UI: http://127.0.0.1:8080/chat"
info "Companion UI: http://127.0.0.1:8080/companion"
info "API docs: http://127.0.0.1:8080/docs"

if [[ ! -f "$OM_MODEL_CHECKPOINT" ]]; then
  printf '\n[OM AI] WARNING: Native checkpoint not found: %s\n' "$OM_MODEL_CHECKPOINT"
  printf '[OM AI] The UI can start, but useful native answers require the trained checkpoint and matching tokenizer.\n'
  printf '[OM AI] Run: python scripts/diagnose_native_chat.py\n\n'
else
  info "Native checkpoint found: $OM_MODEL_CHECKPOINT"
fi

info "Starting OM AI. Press Ctrl+C to stop."
exec om-ai serve --host "${OM_HOST:-127.0.0.1}" --port "${OM_PORT:-8080}"
