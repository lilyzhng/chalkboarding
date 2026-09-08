#!/usr/bin/env python3
"""Render a chalkboard figure's animation to a crisp MP4 (and optionally a GIF).

Chalkboard figures animate once and freeze on their final frame, so a
recording of the page is exactly the artifact you want for Twitter, slides,
or a README. Screen recording gives soft 1x frames, so instead this script
drives the page with Playwright's virtual clock and screenshots every frame
at 2x device pixels, cropped to the wooden board, then encodes with ffmpeg.
Deterministic: the same figure always produces the same frames.

Usage:
    python3 scripts/export_media.py examples/example5_decoding_race.html
    python3 scripts/export_media.py my_chalk.html --seconds 11 --fps 30 --width 1200
    python3 scripts/export_media.py my_chalk.html --gif            # also write a GIF

Output: <name>.mp4 (and <name>.gif with --gif) next to the input, or in --out.
The result is cropped to the board itself, so there is no page background.

Requires: playwright (python) with Chromium, and ffmpeg on PATH.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from playwright.sync_api import sync_playwright

VIEWPORT_W = 980   # authoring width (940) + a little margin
VIEWPORT_H = 900
SCALE = 2          # device pixels per CSS pixel: 2x keeps chalk strokes sharp


def board_box(page):
    """Bounding box of the wooden board in CSS pixels. Figures use
    html{zoom:0.8}; getBoundingClientRect() already accounts for that."""
    return page.evaluate("""() => {
        const el = document.querySelector('.board') || document.querySelector('.wrap') || document.body;
        const r = el.getBoundingClientRect();
        return {x: Math.round(r.left), y: Math.round(r.top), width: Math.round(r.width), height: Math.round(r.height)};
    }""")


def render_frames(html_path, seconds, fps, frames_dir):
    url = "file://" + os.path.abspath(html_path)
    n_frames = int(seconds * fps)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": VIEWPORT_W, "height": VIEWPORT_H},
            device_scale_factor=SCALE,
        )
        page = ctx.new_page()
        # Virtual clock, PAUSED: performance.now() and requestAnimationFrame
        # advance only when we call run_for, so every frame lands exactly on
        # its timestamp regardless of how long a screenshot takes.
        page.clock.install(time=0)
        page.clock.pause_at(1000)
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")

        # Measure at the END so the crop is right when panels animate in.
        page.clock.run_for(int(seconds * 1000))
        box = board_box(page)
        if box["height"] > VIEWPORT_H - box["y"]:
            page.set_viewport_size({"width": VIEWPORT_W, "height": box["y"] + box["height"] + 8})
        # Restart the animation from t=0: reload under the same paused clock.
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")

        step_ms = 1000.0 / fps
        for i in range(n_frames):
            page.screenshot(path=os.path.join(frames_dir, f"f{i:05d}.png"), clip=box)
            page.clock.run_for(int(round(step_ms)))
        browser.close()
    return box


def encode(frames_dir, out_base, fps, width, want_gif):
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found on PATH (brew install ffmpeg)")
    pattern = os.path.join(frames_dir, "f%05d.png")
    scale = f"scale={width}:-2:flags=lanczos"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern,
         "-vf", scale, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
         "-movflags", "+faststart", out_base + ".mp4"],
        check=True,
    )
    print("wrote", out_base + ".mp4")
    if want_gif:
        palette = out_base + ".palette.png"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern,
             "-vf", f"{scale},palettegen=stats_mode=diff", palette],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern, "-i", palette,
             "-lavfi", f"{scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
             "-loop", "0", out_base + ".gif"],
            check=True,
        )
        os.remove(palette)
        print("wrote", out_base + ".gif")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", nargs="+", help="figure HTML file(s)")
    ap.add_argument("--seconds", type=float, default=12, help="animation length to render (default 12)")
    ap.add_argument("--fps", type=int, default=30, help="frame rate (default 30)")
    ap.add_argument("--width", type=int, default=1200, help="output width in px (default 1200)")
    ap.add_argument("--out", help="output directory (default: next to the input)")
    ap.add_argument("--gif", action="store_true", help="also write a GIF (larger and softer than the MP4)")
    args = ap.parse_args()

    for html in args.html:
        name = os.path.splitext(os.path.basename(html))[0]
        out_dir = args.out or os.path.dirname(os.path.abspath(html))
        os.makedirs(out_dir, exist_ok=True)
        frames_dir = tempfile.mkdtemp(prefix="chalk-frames-")
        try:
            render_frames(html, args.seconds, args.fps, frames_dir)
            encode(frames_dir, os.path.join(out_dir, name), args.fps, args.width, args.gif)
        finally:
            shutil.rmtree(frames_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
