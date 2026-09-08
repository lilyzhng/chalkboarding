#!/usr/bin/env python3
"""QA screenshots of a chalkboard figure at start, mid-animation, and final frame.

Phase 3 of the skill: look at these three images before delivering. The final
frame is what print and reduced-motion readers get, so it must carry the whole
message on its own.

Usage:
    python3 scripts/screenshot_beats.py examples/example5_decoding_race.html
    python3 scripts/screenshot_beats.py my_chalk.html --beats 0.3,3,12.5 --out shots/
    python3 scripts/screenshot_beats.py my_chalk.html --beats 0.3,3.6,8.5 --replay

Pick the beats from your beat table: start just after 0, mid right after the
key beat, end past END. Writes <name>_start.png, <name>_mid.png, <name>_end.png,
and with --replay clicks the eraser after the end shot and writes
<name>_replay.png 0.4s later (it should look like the start shot).
Requires: playwright (python) with Chromium.
"""
import argparse
import os

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--beats", default="0.3,3,12.5", help="seconds for start,mid,end (default 0.3,3,12.5)")
    ap.add_argument("--out", default=".", help="output directory")
    ap.add_argument("--replay", action="store_true", help="after the end shot, click #replay and shoot the reset")
    args = ap.parse_args()
    beats = [float(x) for x in args.beats.split(",")]
    names = ["start", "mid", "end"][: len(beats)]
    base = os.path.splitext(os.path.basename(args.html))[0]
    os.makedirs(args.out, exist_ok=True)

    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 980, "height": 900})
        page.goto("file://" + os.path.abspath(args.html))
        elapsed = 0.0
        for name, t in zip(names, beats):
            page.wait_for_timeout(int((t - elapsed) * 1000))
            elapsed = t
            path = os.path.join(args.out, f"{base}_{name}.png")
            page.screenshot(path=path, full_page=True)
            print("wrote", path)
        if args.replay:
            page.click("#replay")
            page.wait_for_timeout(400)
            path = os.path.join(args.out, f"{base}_replay.png")
            page.screenshot(path=path, full_page=True)
            print("wrote", path)
        b.close()


if __name__ == "__main__":
    main()
