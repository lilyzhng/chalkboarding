#!/usr/bin/env bash
# qa.sh: screenshot a chalkboard figure at three beats (plus the replay reset).
#
# Usage:
#   bash scripts/qa.sh <figure.html> [--beats START,MID,END] [--out DIR] [--replay]
#
# Examples:
#   bash scripts/qa.sh my_chalk.html --beats 0.4,3.6,8 --replay
#
# Writes <name>_start.png, <name>_mid.png, <name>_end.png (and _replay.png)
# into --out (default: current directory). Look at every one before delivering.
# Same one-time Playwright setup as export.sh, no ffmpeg needed.
set -euo pipefail

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: bash scripts/qa.sh <figure.html> [--beats START,MID,END] [--out DIR] [--replay]"
    exit 1
fi
if [[ ! -f "$1" ]]; then
    echo "File not found: $1" >&2
    exit 1
fi

source "$(dirname "${BASH_SOURCE[0]}")/_bootstrap.sh"

"$PY" "$SCRIPT_DIR/screenshot_beats.py" "$@"
