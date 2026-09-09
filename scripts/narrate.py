#!/usr/bin/env python3
"""Mux an optional voice-over onto a figure's MP4: lines from the figure's
<script type="application/vo+json"> block, placed at their beat times. See SKILL.md.

Usage: python3 scripts/narrate.py <figure.html> <figure.mp4> [--tts say|openrouter|gemini] [--voice NAME] [--vo FILE] [--out FILE]
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


STYLE = os.environ.get("NARRATE_STYLE", "Warm, natural, unhurried teacher voice.")
READ_EXACTLY = "Read this exactly as written, word for word. Do not add, remove, or rephrase anything. "
# gpt-audio is a chat model: without this framing it answers the line instead of reading it.
TTS_ENGINE = "You are a text-to-speech engine. Speak the user's text verbatim. Never answer, comment, or add words. "
HTTP_TIMEOUT = 120
TTS_RATE = 24000        # pcm16 sample rate both cloud backends return
AAC = ["-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k"]
MAX_TEMPO = 1.12        # speed a long line up by at most 12% before delaying the next one
GAP = 0.25              # breath between lines, seconds
OVERRUN_SLACK = 0.2     # seconds a line may spill past the next beat before we act
# Recommended voices per backend. `--voice female` / `--voice male` resolve to
# these; a bare `--tts` with no `--voice` uses the female pick.
RECOMMENDED = {
    "gemini":     {"female": "Kore",     "male": "Puck"},
    "openrouter": {"female": "coral",    "male": "ballad"},
    "say":        {"female": "Samantha", "male": "Daniel"},
}


def _encode(pcm, rate, out_wav):
    """Write raw 16-bit mono PCM as 48k stereo AAC for muxing."""
    raw = out_wav + ".pcm"
    open(raw, "wb").write(pcm)
    sp.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(rate), "-ac", "1",
            "-i", raw] + AAC + [out_wav], check=True)
    os.remove(raw)


class SayBackend:
    """macOS built-in `say`. Discover voices with `say -v '?'`."""
    name = "say"

    @staticmethod
    def available():
        return sys.platform == "darwin" and _which("say")

    @staticmethod
    def synth(text, out_wav, voice):
        aiff = out_wav + ".aiff"
        sp.run(["say"] + (["-v", voice] if voice else []) + ["-o", aiff, text], check=True)
        sp.run(["ffmpeg", "-y", "-loglevel", "error", "-i", aiff] + AAC + [out_wav], check=True)
        os.remove(aiff)


class OpenRouterBackend:
    """GPT voices via OpenRouter. Audio is streamed as base64 pcm16 at 24 kHz."""
    name = "openrouter"
    URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = os.environ.get("OPENROUTER_TTS_MODEL", "openai/gpt-audio-mini")

    @staticmethod
    def available():
        return bool(os.environ.get("OPENROUTER_API_KEY"))

    @classmethod
    def synth(cls, text, out_wav, voice):
        body = {
            "model": cls.MODEL, "stream": True, "modalities": ["text", "audio"],
            "audio": {"voice": voice, "format": "pcm16"},
            "messages": [{"role": "system", "content": TTS_ENGINE + STYLE},
                         {"role": "user", "content": f'Read aloud exactly: "{text}"'}],
        }
        req = urllib.request.Request(cls.URL, data=json.dumps(body).encode(), headers={
            "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
            "Content-Type": "application/json",
        })
        pcm = bytearray()
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            for raw in r:
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                d = json.loads(line[5:])
                if "error" in d:
                    raise RuntimeError(d["error"].get("message", str(d["error"])))
                for ch in d.get("choices", []):
                    pcm += base64.b64decode(ch.get("delta", {}).get("audio", {}).get("data", ""))
        if not pcm:
            raise RuntimeError("no audio returned")
        _encode(pcm, TTS_RATE, out_wav)


class GeminiBackend:
    """Gemini TTS. Returns base64 pcm16; sample rate comes from the mime type."""
    name = "gemini"
    MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.1-flash-tts-preview")

    @staticmethod
    def available():
        return bool(os.environ.get("GEMINI_API_KEY"))

    @classmethod
    def synth(cls, text, out_wav, voice):
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/{cls.MODEL}:generateContent"
               f"?key={os.environ['GEMINI_API_KEY']}")
        body = {
            "contents": [{"parts": [{"text": f"{READ_EXACTLY}{STYLE}\n\n{text}"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}},
        }
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            part = json.load(r)["candidates"][0]["content"]["parts"][0]["inlineData"]
        m = re.search(r"rate=(\d+)", part.get("mimeType", ""))
        _encode(base64.b64decode(part["data"]), int(m.group(1)) if m else TTS_RATE, out_wav)


BACKENDS = {b.name: b for b in (SayBackend, OpenRouterBackend, GeminiBackend)}


def resolve_voice(tts, voice):
    """Map the female/male aliases to the backend's recommended voice."""
    if voice and voice.lower() in ("female", "male"):
        return RECOMMENDED[tts][voice.lower()]
    return voice or RECOMMENDED[tts]["female"]


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
              " or <figure>_vo.json); leaving the video silent.")
        return 0

    backend = BACKENDS[args.tts]
    if not backend.available():
        hint = {"openrouter": "set OPENROUTER_API_KEY",
                "gemini": "set GEMINI_API_KEY", "say": "macOS only"}.get(args.tts, "")
        print(f"! narrate: TTS backend '{args.tts}' is unavailable ({hint}); leaving the video silent.")
        return 0
    voice = resolve_voice(args.tts, args.voice)
    if voice and args.tts == "say" and voice not in installed_say_voices():
        print(f"! narrate: voice '{voice}' not installed (see `say -v '?'`); using the system default")
        voice = None

    vlen = _dur(args.video)
    if vlen < beats[-1]["t"]:
        print(f"! narrate: video is {vlen:.0f}s but the last line starts at {beats[-1]['t']:.0f}s; "
              f"the animation will freeze. Re-export with --seconds {math.ceil(beats[-1]['t'])} or more.")
    tmp = tempfile.mkdtemp(prefix="chalk_vo_")
    clips = []
    print("beat  beat_t  start  dur   ends   window  note")
    prev_end = 0.0
    for i, b in enumerate(beats):
        clip = os.path.join(tmp, f"l{i}.m4a")
        backend.synth(b["text"], clip, voice)
        d = _dur(clip)
        nxt = beats[i + 1]["t"] if i + 1 < len(beats) else vlen
        window = nxt - b["t"]
        note = "ok"
        # never overlap the previous line: start at the beat, or after the previous line ends
        start = max(b["t"], prev_end + GAP if i else 0.0)
        # if this line would still run into the next beat, compress it a little first
        if start + d > nxt + OVERRUN_SLACK and i + 1 < len(beats):
            tempo = min(MAX_TEMPO, d / max(0.1, nxt - start))
            if tempo > 1.01:
                fast = os.path.join(tmp, f"l{i}f.m4a")
                sp.run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-filter:a", f"atempo={tempo:.3f}"] + AAC + [fast], check=True)
                clip, d = fast, _dur(fast)
                note = f"sped {tempo:.2f}x"
        if start > b["t"] + 0.05:
            note += f", delayed +{start - b['t']:.1f}s"
        if start + d > nxt + OVERRUN_SLACK and i + 1 < len(beats):
            note += ", still overruns"
        clips.append((start, clip, d))
        prev_end = start + d
        print(f"{i:>3}  {b['t']:6.1f}  {start:5.1f}  {d:4.1f}  {start+d:5.1f}  {window:6.1f}  {note}")

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
            "-filter_complex", ";".join(filt), "-map", "[out]"] + AAC + [track], check=True)

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
            "-map", "0:v:0", "-map", "1:a:0", *vcodec] + AAC + ["-shortest", tmp_out], check=True)
    os.replace(tmp_out, out)
    print(f"\nok voice-over ({voice or 'system default'}) muxed -> {out}  ({_dur(out):.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
