# fonts/: the chalk hand

The chalkboard look is one font plus three layers of deliberate imperfection.
This folder holds all of them so you can see, and reuse, exactly what makes text
read as hand-drawn instead of typeset.

| File | What it is |
|---|---|
| `PencilPete.ttf` | The chalk face used for everything on the slate. Copy it next to your HTML; figures load it with a relative `url("PencilPete.ttf")`. |
| `slip-filters.svg` | Three SVG turbulence filters (`#slip1..3`) with different frequencies and seeds, the `#dust` chalk-stroke filter (patchy line plus halo), and the `#fade` gradient for long strokes. Paste once after `<body>`. |
| `chalky.js` | The imperfection pass, driven by `data-chalk="tidy\|rough\|shaky"` on the slate: slip filters with probability that grows with width, chalk dust on SVG strokes, dash breaks, shape geometry wobble, scattered ghost fragments, long-stroke fade. Deterministic randomness keeps screenshots identical across reloads. Last script in the file. |
| `chalky.css` | The `@font-face`, the `--tilt` variable and per-preset values, micro-rotations that multiply by it, irregular corner radii (`10px 8px 11px 7px`, four different values, always), the dirty-slate `::before` wipes, the ghost layer, and the reduced-motion reset. |

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
