#!/usr/bin/env python3
"""Add an OPTIONAL voice-over to a chalkboard figure's exported MP4.

The video is authoritative: the figure already plays on a fixed beat schedule,
so narration lines are placed at absolute timestamps (not concatenated), which
means they can never drift out of sync. A line that overruns its beat only
overlaps the next one briefly; a fit-check warns when that happens.

Narration lives WITH the figure (the skill's "one self-contained HTML file"
principle): an embedded JSON block, or a sidecar file.

    <script type="application/vo+json" id="vo">
    [ {"t": 0,  "text": "Ever wonder what happens when you tap play?"},
      {"t": 7,  "text": "First, your tap zips to your home router."} ]
    </script>

Times are seconds, aligned to the figure's own beats. Sidecar fallback:
`<figure>_vo.json` next to the HTML, or `--vo <file>`.

TTS is pluggable; only macOS `say` is implemented today. On a non-macOS host
(or if the chosen backend is unavailable) this exits 0 without changing the
video, so a silent export still ships.

Usage:
    python3 scripts/narrate.py <figure.html> <figure.mp4> [--voice NAME]
                               [--tts say] [--vo FILE] [--out FILE]
"""
import argparse
import base64
import json
import math
import os
import re
import shutil
import subprocess as sp
import sys
import tempfile
import urllib.request


# ---------------------------------------------------------------------------
# TTS backends — a tiny seam so ElevenLabs / Azure / Qwen3-TTS can be added
# later without touching the figure format or the mux logic.
# ---------------------------------------------------------------------------
class SayBackend:
    """macOS built-in `say`. Discover voices with `say -v '?'`; premium/enhanced
    neural voices (e.g. 'Serena (Premium)', 'Isha (Premium)') sound best."""
    name = "say"

    @staticmethod
    def available():
        return sys.platform == "darwin" and _which("say")

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


class OpenRouterBackend:
    """GPT voices via OpenRouter (openai/gpt-audio-mini by default). Needs
    OPENROUTER_API_KEY. Audio output requires streaming; chunks arrive as base64
    pcm16 at 24 kHz and are concatenated, then encoded with ffmpeg. Voices: alloy,
    ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse."""
    name = "openrouter"
    URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = os.environ.get("OPENROUTER_TTS_MODEL", "openai/gpt-audio-mini")
    STYLE = os.environ.get("NARRATE_STYLE",
                           "Warm, natural, unhurried teacher voice.")

    @staticmethod
    def available():
        return bool(os.environ.get("OPENROUTER_API_KEY"))

    @classmethod
    def synth(cls, text, out_wav, voice):
        body = {
            "model": cls.MODEL, "stream": True,
            "modalities": ["text", "audio"],
            "audio": {"voice": voice or "nova", "format": "pcm16"},
            "messages": [
                {"role": "system", "content": "You are a voice-over reader. Read the user text "
                 "aloud exactly as written, word for word. Do not add, remove, or rephrase "
                 "anything. " + cls.STYLE},
                {"role": "user", "content": text},
            ],
        }
        req = urllib.request.Request(cls.URL, data=json.dumps(body).encode(), headers={
            "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/lilyzhng/chalkboarding",
        })
        pcm = bytearray()
        with urllib.request.urlopen(req, timeout=120) as r:
            for raw in r:
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    d = json.loads(payload)
                except ValueError:
                    continue
                if "error" in d:
                    raise RuntimeError(d["error"].get("message", str(d["error"])))
                for ch in d.get("choices", []):
                    a = (ch.get("delta") or {}).get("audio") or {}
                    if a.get("data"):
                        pcm += base64.b64decode(a["data"])
        if not pcm:
            raise RuntimeError("no audio returned")
        raw_path = out_wav + ".pcm"
        open(raw_path, "wb").write(pcm)
        sp.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1",
                "-i", raw_path, "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", out_wav],
               check=True)
        os.remove(raw_path)


class GeminiBackend:
    """Gemini TTS (gemini-3.1-flash-tts-preview by default). Needs GEMINI_API_KEY.
    Returns pcm16 at 24 kHz, encoded with ffmpeg. Voices include Kore, Puck,
    Zephyr, Aoede, Charon, Fenrir, Leda, Orus; full list in the Gemini docs."""
    name = "gemini"
    MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.1-flash-tts-preview")
    STYLE = os.environ.get("NARRATE_STYLE", "Warm, natural, unhurried teacher voice.")

    @staticmethod
    def available():
        return bool(os.environ.get("GEMINI_API_KEY"))

    @classmethod
    def synth(cls, text, out_wav, voice):
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/{cls.MODEL}:generateContent"
               f"?key={os.environ['GEMINI_API_KEY']}")
        body = {
            "contents": [{"parts": [{"text": f"Read this exactly as written, word for word. {cls.STYLE}\n\n{text}"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice or "Kore"}}}},
        }
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.load(r)
        part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
        pcm = base64.b64decode(part["data"])
        rate = 24000
        m = re.search(r"rate=(\d+)", part.get("mimeType", ""))
        if m:
            rate = int(m.group(1))
        raw_path = out_wav + ".pcm"
        open(raw_path, "wb").write(pcm)
        sp.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(rate), "-ac", "1",
                "-i", raw_path, "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", out_wav],
               check=True)
        os.remove(raw_path)


BACKENDS = {b.name: b for b in (SayBackend, OpenRouterBackend, GeminiBackend)}

# Recommended voices per backend. `--voice female` / `--voice male` resolve to
# these; a bare `--tts` with no `--voice` uses the female pick.
RECOMMENDED = {
    "gemini":     {"female": "Kore",     "male": "Puck"},
    "openrouter": {"female": "coral",    "male": "ballad"},
    "say":        {"female": "Samantha", "male": "Daniel"},
}
DEFAULT_VOICE = {k: v["female"] for k, v in RECOMMENDED.items()}


def resolve_voice(tts, voice):
    """Map the female/male aliases to the backend's recommended voice."""
    if voice and voice.lower() in ("female", "male"):
        return RECOMMENDED[tts][voice.lower()]
    return voice or DEFAULT_VOICE.get(tts)


def installed_say_voices():
    out = sp.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    return {line.split("  ")[0].strip() for line in out.splitlines() if line.strip()}


def _which(x):
    return shutil.which(x) is not None


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
    ap.add_argument("--voice", default=None, help="voice name, or `female` / `male` for the backend's recommended voice")
    ap.add_argument("--tts", default="say", choices=sorted(BACKENDS), help="TTS backend: say (macOS), openrouter (GPT voices), gemini (Gemini TTS)")
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
        hint = {"openrouter": "set OPENROUTER_API_KEY (optional; any OpenRouter key works)",
                "gemini": "set GEMINI_API_KEY", "say": "macOS only"}.get(args.tts, "")
        print(f"! narrate: TTS backend '{args.tts}' is unavailable: {hint} — leaving the video silent.")
        return 0
    if False:
        print(f"! narrate: TTS backend '{args.tts}' is unavailable on this host "
              f"(say needs macOS; openrouter needs OPENROUTER_API_KEY; gemini needs GEMINI_API_KEY) — leaving the video silent.")
        return 0
    voice = resolve_voice(args.tts, args.voice)
    if voice and args.tts == "say" and voice not in installed_say_voices():
        print(f"! narrate: voice '{voice}' not installed (see `say -v '?'`); using the system default")
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
    print(f"\nok voice-over ({voice}) muxed -> {out}  ({_dur(out):.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
