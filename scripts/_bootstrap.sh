#!/usr/bin/env bash
# _bootstrap.sh: shared setup for export.sh and qa.sh. Not meant to be run directly.
#
# Creates a private virtualenv under ~/.cache/chalkboarding on first run,
# installs Playwright + Chromium into it, and exports $PY (the venv python).
# Second run onward is instant. Nothing touches the system Python.

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${CYAN}i${NC} $*"; }
ok()    { echo -e "${GREEN}ok${NC} $*"; }
warn()  { echo -e "${YELLOW}!${NC} $*"; }
err()   { echo -e "${RED}x${NC} $*" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${CHALKBOARDING_CACHE:-$HOME/.cache/chalkboarding}"
VENV="$CACHE_DIR/venv"
PY="$VENV/bin/python"

if ! command -v python3 &>/dev/null; then
    err "python3 is required."
    err "  macOS:  brew install python"
    err "  or:     https://www.python.org/downloads/"
    exit 1
fi

if [[ ! -x "$PY" ]]; then
    info "First run: creating a private Python env in $VENV"
    mkdir -p "$CACHE_DIR"
    python3 -m venv "$VENV"
fi

if ! "$PY" -c "import playwright" &>/dev/null; then
    info "Installing Playwright (one time)..."
    "$PY" -m pip install --quiet --upgrade pip
    "$PY" -m pip install --quiet playwright
fi

if ! "$PY" -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); b.close()
" &>/dev/null; then
    info "Downloading Chromium for Playwright (one time, ~150 MB)..."
    "$PY" -m playwright install chromium
fi

ok "Playwright ready"
export PY SCRIPT_DIR
