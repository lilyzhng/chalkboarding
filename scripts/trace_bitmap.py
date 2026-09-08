#!/usr/bin/env python3
"""Trace an image into a chalkboard pixel-grid bitmap.

Coding models have poor spatial sense: asked to draw a kangaroo freehand they
produce mush, but given a silhouette to trace they do fine. This script is the
"trace" step: it converts any image (an emoji PNG, a logo, a photo silhouette)
into the X/. row-string bitmap that pixel-grid figures consume (see the ROO
array in example1_kangaroo.html).

Usage:
    python3 trace_bitmap.py kangaroo.png                 # 32x32, alpha channel
    python3 trace_bitmap.py opera_house.jpg --mode dark  # trace dark pixels
    python3 trace_bitmap.py logo.png --size 24 --threshold 0.35

Then paste the printed JS array into your figure. Tip: emoji PNGs (e.g. from
the Twemoji repo) trace beautifully via their alpha channel, that's how the
kangaroo was made.
"""
import argparse
import sys

from PIL import Image


def trace(img, cols, rows, mode, threshold):
    img = img.convert("RGBA")
    # crop to the content's bounding box first so the subject fills the grid
    if mode == "alpha":
        bbox = img.getchannel("A").getbbox()
    else:
        gray = img.convert("L")
        lut = (lambda v: 255 if v < 128 else 0) if mode == "dark" else (lambda v: 255 if v >= 128 else 0)
        bbox = gray.point(lut).getbbox()
    if bbox:
        img = img.crop(bbox)
    # box-filter downsample = average coverage per cell
    small = img.resize((cols, rows), Image.BOX)
    out = []
    for y in range(rows):
        row = []
        for x in range(cols):
            r, g, b, a = small.getpixel((x, y))
            if mode == "alpha":
                v = a / 255
            else:
                lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                v = (1 - lum) if mode == "dark" else lum
                v *= a / 255
            row.append("X" if v >= threshold else ".")
        out.append("".join(row))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image")
    p.add_argument("--size", default="32", help="grid size: N or COLSxROWS (default 32)")
    p.add_argument("--mode", choices=["alpha", "dark", "light"], default="alpha",
                   help="what counts as filled: alpha channel (default), dark pixels, or light pixels")
    p.add_argument("--threshold", type=float, default=0.5, help="cell coverage needed to mark X (0..1, default 0.5)")
    p.add_argument("--name", default="BITMAP", help="JS variable name (default BITMAP)")
    args = p.parse_args()

    if "x" in args.size:
        cols, rows = (int(v) for v in args.size.split("x"))
    else:
        cols = rows = int(args.size)

    rows_out = trace(Image.open(args.image), cols, rows, args.mode, args.threshold)

    filled = sum(r.count("X") for r in rows_out)
    if filled == 0:
        sys.exit("traced nothing, try --mode dark/light or a lower --threshold")

    # preview for the terminal
    print("\n".join(r.replace(".", "·").replace("X", "█") for r in rows_out))
    print(f"\n// {filled}/{cols*rows} cells filled")
    print(f"var {args.name} = [")
    for r in rows_out:
        print(f'  "{r}",')
    print("];")


if __name__ == "__main__":
    main()
