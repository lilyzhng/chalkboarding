#!/usr/bin/env python3
"""Mux an optional voice-over onto a figure's MP4: lines from the figure's
<script type="application/vo+json"> block, placed at their timestamps via macOS `say`.

Usage: python3 scripts/narrate.py <figure.html> <figure.mp4> [--voice NAME] [--tts say] [--vo FILE] [--out FILE]
"""
import argparse
import json
import math
import os
import re
import subprocess as sp
import sys
import tempfile


# ---------------------------------------------------------------------------
# TTS backends — a tiny seam (name / available / synth, optional voice_ok) so
# ElevenLabs / Azure / Qwen3-TTS can be added later without touching the figure
# format or the mux logic. If none is available, narrate.py leaves the video
# silent rather than failing.
# ---------------------------------------------------------------------------
class SayBackend:
    """macOS built-in `say`. Discover voices with `say -v '?'`; premium/enhanced
    neural voices (e.g. 'Serena (Premium)', 'Isha (Premium)') sound best."""
    name = "say"

    @staticmethod
    def available():
        return sys.platform == "darwin" and _which("say")

    @staticmethod
    def voice_ok(voice):
        # `say` silently falls back to the default voice for an unknown name,
        # so check it's actually installed before we trust the log.
        out = sp.run(["say", "-v", "?"], capture_output=True, text=True).stdout
        names = {ln.split("  ")[0].strip() for ln in out.splitlines() if ln.strip()}
        return voice in names

    @staticmethod
    def synth(text, out_wav, voice):
        aiff = out_wav + ".aiff"
        cmd = ["say"]
        if voice:
            cmd += ["-v", voice]
        cmd += ["-o", aiff, text]
        sp.run(cmd, check=True)
        # normalize to 48k stereo aac for a clean mix/mux
        sp.run(["ffmpeg", "-y", "-loglevel", "error", "-i", aiff,
                "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", out_wav],
               check=True)
        os.remove(aiff)


BACKENDS = {b.name: b for b in (SayBackend,)}
DEFAULT_VOICE = {"say": "Serena (Premium)"}


def _which(x):
    return sp.run(["which", x], capture_output=True).returncode == 0


def _dur(path):
    out = sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout.strip())


def load_beats(html_path, vo_arg):
    """Return a sorted list of {'t': float, 'text': str}."""
    # 1) explicit --vo file  2) sidecar <figure>_vo.json  3) embedded block
    sidecar = os.path.splitext(html_path)[0] + "_vo.json"
    if vo_arg:
        beats = json.load(open(vo_arg))
    elif os.path.exists(sidecar):
        beats = json.load(open(sidecar))
    else:
        html = open(html_path, encoding="utf-8").read()
        m = re.search(r'<script[^>]*type=["\']application/vo\+json["\'][^>]*>(.*?)</script>',
                      html, re.S | re.I)
        if not m:
            return None
        beats = json.loads(m.group(1))
    beats = [{"t": float(b["t"]), "text": str(b["text"]).strip()} for b in beats]
    beats.sort(key=lambda b: b["t"])
    return beats


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("video")
    ap.add_argument("--voice", default=None, help="TTS voice name (backend-specific)")
    ap.add_argument("--tts", default="say", choices=sorted(BACKENDS), help="TTS backend")
    ap.add_argument("--vo", default=None, help="sidecar narration JSON (overrides embedded)")
    ap.add_argument("--out", default=None, help="output MP4 (default: overwrite <video>)")
    args = ap.parse_args()

    beats = load_beats(args.html, args.vo)
    if not beats:
        print("i narrate: no narration found (embedded <script type=\"application/vo+json\">"
              " or <figure>_vo.json) — leaving the video silent.")
        return 0

    backend = BACKENDS[args.tts]
    if not backend.available():
        print(f"! narrate: TTS backend '{args.tts}' is unavailable on this host "
              f"(macOS `say` only, for now) — leaving the video silent.")
        return 0
    voice = args.voice or DEFAULT_VOICE.get(args.tts)
    if voice and hasattr(backend, "voice_ok") and not backend.voice_ok(voice):
        print(f"! narrate: voice '{voice}' not installed (see `say -v '?'`); "
              f"using the system default")
        voice = None

    vlen = _dur(args.video)
    tmp = tempfile.mkdtemp(prefix="chalk_vo_")
    clips = []
    print("beat  start   dur   ends   window  fit")
    for i, b in enumerate(beats):
        clip = os.path.join(tmp, f"l{i}.m4a")
        backend.synth(b["text"], clip, voice)
        d = _dur(clip)
        clips.append((b["t"], clip, d))
        nxt = beats[i + 1]["t"] if i + 1 < len(beats) else vlen
        fit = "ok" if b["t"] + d <= nxt + 0.2 else "OVERFLOW"
        print(f"{i:>3}  {b['t']:5.1f}  {d:4.1f}  {b['t']+d:5.1f}  {nxt-b['t']:5.1f}   {fit}")

    audio_end = max(t + d for t, _, d in clips)
    final_len = max(vlen, math.ceil(audio_end * 10) / 10)

    # one track: each clip delayed to its start, summed (no gain normalization)
    inputs, filt = [], []
    for i, (start, clip, _) in enumerate(clips):
        inputs += ["-i", clip]
        ms = int(round(start * 1000))
        filt.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(clips)))
    filt.append(f"{mix}amix=inputs={len(clips)}:normalize=0:dropout_transition=0,"
                f"apad,atrim=0:{final_len}[out]")
    track = os.path.join(tmp, "narration.m4a")
    sp.run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
            "-filter_complex", ";".join(filt), "-map", "[out]",
            "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", track], check=True)

    # extend the video with a frozen last frame if narration runs past the end
    pad = final_len - vlen
    src = args.video
    if pad > 0.05:
        padded = os.path.join(tmp, "vpad.mp4")
        sp.run(["ffmpeg", "-y", "-loglevel", "error", "-i", args.video,
                "-vf", f"tpad=stop_mode=clone:stop_duration={pad:.2f}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", padded], check=True)
        src = padded

    out = args.out or args.video
    tmp_out = os.path.join(tmp, "narrated.mp4")
    vcodec = ["-c:v", "copy"] if src == args.video else \
             ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18"]
    sp.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", track,
            "-map", "0:v:0", "-map", "1:a:0", *vcodec,
            "-c:a", "aac", "-b:a", "192k", "-shortest", tmp_out], check=True)
    os.replace(tmp_out, out)
    print(f"\nok voice-over ({voice or 'system default'}) muxed -> {out}  ({_dur(out):.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
