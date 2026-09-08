#!/usr/bin/env bash
# export.sh: render a chalkboard figure to a crisp MP4 (and optionally a GIF).
#
# Usage:
#   bash scripts/export.sh <figure.html> [flags]
#
# Examples:
#   bash scripts/export.sh my_chalk.html                      # my_chalk.mp4 next to the input
#   bash scripts/export.sh my_chalk.html --gif                # also my_chalk.gif (autoplays in a README)
#   bash scripts/export.sh my_chalk.html --seconds 9 --fps 30 --width 1200
#   bash scripts/export.sh toggle_chalk.html --click "#mRelax@4"   # click an element at 4s
#   bash scripts/export.sh my_chalk.html --narrate --voice "Serena (Premium)"  # + voice-over (macOS)
#
# What this does:
#   1. First run only: creates a private Python env in ~/.cache/chalkboarding,
#      installs Playwright and Chromium into it. No system Python is touched.
#   2. Checks ffmpeg is installed (brew install ffmpeg).
#   3. Runs export_media.py: drives the page on a virtual clock, screenshots
#      every frame at 2x, crops to the board, encodes with ffmpeg.
#   4. Optional: with --narrate, muxes a voice-over onto the MP4 (see narration.md).
#
# Flags after the HTML path are passed to export_media.py, EXCEPT --narrate,
# --voice and --tts, which control the optional voice-over step.
set -euo pipefail

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: bash scripts/export.sh <figure.html> [--gif] [--seconds N] [--fps N] [--width N] [--out DIR] [--click SEL@SEC] [--narrate] [--voice NAME] [--tts say]"
    exit 1
fi
if [[ ! -f "$1" ]]; then
    echo "File not found: $1" >&2
    exit 1
fi

HTML="$1"; shift

# Split our voice-over flags out of the flags meant for export_media.py.
NARRATE=0
VOICE=""
TTS="say"
PASS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --narrate) NARRATE=1; shift ;;
        --voice)   VOICE="$2"; shift 2 ;;
        --tts)     TTS="$2"; shift 2 ;;
        *)         PASS+=("$1"); shift ;;
    esac
done

source "$(dirname "${BASH_SOURCE[0]}")/_bootstrap.sh"

if ! command -v ffmpeg &>/dev/null; then
    err "ffmpeg is required for encoding."
    err "  macOS:  brew install ffmpeg"
    err "  Ubuntu: sudo apt install ffmpeg"
    exit 1
fi
ok "ffmpeg found"

info "Rendering..."
"$PY" "$SCRIPT_DIR/export_media.py" "$HTML" ${PASS[@]+"${PASS[@]}"}

OUT_BASE="${HTML%.html}"

if [[ "$NARRATE" == "1" ]]; then
    if [[ -f "$OUT_BASE.mp4" ]]; then
        info "Adding voice-over..."
        "$PY" "$SCRIPT_DIR/narrate.py" "$HTML" "$OUT_BASE.mp4" \
            ${VOICE:+--voice "$VOICE"} --tts "$TTS" || warn "voice-over step failed; MP4 left silent"
    else
        warn "--narrate given but no $OUT_BASE.mp4 was produced; skipping voice-over"
    fi
fi

echo ""
ok "Done"
for f in "$OUT_BASE.mp4" "$OUT_BASE.gif"; do
    [[ -f "$f" ]] && echo "  $f  ($(du -h "$f" | cut -f1 | xargs))"
done
echo ""
echo "  MP4: crisp, for X, slides, and GitHub attachments (click to play)."
echo "  GIF: softer and larger, but autoplays and loops in a README <img>."
