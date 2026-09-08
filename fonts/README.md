# fonts/: the chalk hand

The chalkboard look is one font plus three layers of deliberate imperfection.
This folder holds all of them so you can see, and reuse, exactly what makes text
read as hand-drawn instead of typeset.

| File | What it is |
|---|---|
| `PencilPete.ttf` | The chalk face used for everything on the slate. Copy it next to your HTML; figures load it with a relative `url("PencilPete.ttf")`. |
| `slip-filters.svg` | Three SVG turbulence filters (`#slip1..3`) with different frequencies and seeds, so neighbouring elements never share the same waver. Paste once after `<body>`. |
| `chalky.js` | Applies a slip filter to each element **with probability that grows with its width**: short strokes stay clean, long ones always waver somewhere, like real handwriting. Deterministic randomness keeps screenshots identical across reloads. Last script in the file. |
| `chalky.css` | The `@font-face`, alternating micro-rotations (±0.25° on panels, ±1.1° on chips), irregular corner radii (`10px 8px 11px 7px`, four different values, always), dashed and dotted strokes over solid, streaky chalk fills, and the reduced-motion reset. |

## Why three layers

- **Turbulence** bends the strokes. One filter on everything reads as a Photoshop effect; three filters applied selectively read as a hand.
- **Probability by length** is the physical rule a real hand follows. A three-letter label is easy to write straight. A full sentence never is.
- **Geometry** does the rest: nothing sits perfectly level, no two corners match, no line is solid.

## Using it in a new figure

1. Copy `PencilPete.ttf` next to your HTML.
2. Paste `slip-filters.svg` right after `<body>`.
3. Include `chalky.css` in your `<style>` (or copy the rules you need).
4. Paste `chalky.js` as the last `<script>` and add every custom class you invent to its selector list.

`template.html` at the repo root already has all four wired in.

## Licenses

`PencilPete.ttf` is a third-party font. Check its license before redistributing in your own project.
