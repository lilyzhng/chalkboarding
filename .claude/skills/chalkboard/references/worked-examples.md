# Worked examples: from idea to figure

The files in `examples/` are finished figures. This document is what makes
them *reproducible*: for the two richest ones it records the regeneration
prompt (what you'd ask for), the phase-1 ASCII mock it implies, and the
phase-2 implementation notes that aren't obvious from a prompt alone. Use the
example closest to your new figure as a starting point — read its source
alongside its recipe here.

(Provenance note: which model/agent originally generated each figure was not
recorded in git — history was squashed through deploy commits. That's exactly
why these recipes exist: regeneration should depend on the skill, not on
remembering who or what drew it first.)

## The kangaroo — `dflash_diffusion_analogy_chalk-v5.html`

**Regeneration prompt:**

> A chalkboard figure for the diffusion analogy: two side-by-side canvases
> painting the same 32×32 pixel image of a kangaroo (it's for a Sydney
> venue). Left panel "Paint sequentially — pixel by pixel" fills the image
> one cell at a time in raster order and takes ~7s. Right panel "Denoise in
> parallel — diffusion" starts as pure noise and converges every pixel at
> once in ~3.2s. When the parallel one finishes, a hook question appears:
> "What about *drafting tokens* in parallel?"

**Phase-1 mock:**

```
+--------------------------------------------------------------+
| +--------------------------+  +----------------------------+ |
| : Paint sequentially       :  : Denoise in parallel        : |
| : pixel by pixel           :  : diffusion  (all at once ✓) : |
| :   ▓▓▓▓▓▓▓░░░░░░░         :  :   ▒▒▓▒▓▓▒▓▒▒▓▒▓            : |
| :   (raster fill, cursor)  :  :   (noise -> kangaroo)      : |
| :   cell 340 of 1024...    :  :   denoising every pixel... : |
| +--------------------------+  +----------------------------+ |
|        a diffusion canvas for a Sydney local · NeurIPS       |
|      What about _drafting tokens_ in parallel?   [replay]    |
+--------------------------------------------------------------+

Beats: t=0 both start · t≈3.2 right converges + done badge + hook question
       t=7.0 left finally finishes · t=7.3 freeze
```

**Implementation notes:**

- The image is a **hard-coded 32-row bitmap** of `'X'`/`'.'` strings (`ROO`
  array) — traced from the Twemoji kangaroo's alpha channel. For a new
  subject, trace any small emoji/icon at 32×32 the same way. Grids stay
  ≤32×32; this is a chalk sketch, not a framebuffer.
- Each canvas is a CSS grid of `<i>` cells built once up front.
- Serial panel: `filled = floor(t/T_P * N)` index cutoff; the current cell
  gets a bright box-shadow "cursor"; unfilled cells flicker faintly
  (`Math.random() < 0.10` → low-alpha noise) so the untouched area feels
  alive.
- Parallel panel: per-cell random delay (0–0.55s) + smoothstep blend from
  random noise alpha to the target alpha, so convergence looks organic, not
  linear.
- Final texture must be **deterministic per cell**
  (`0.72 + ((i*37+11)%23)/100`), so the finished kangaroo looks hand-filled
  with chalk and is identical every replay/screenshot.
- The narrative trick: the *done* badge on the right appears while the left
  is still grinding — the time asymmetry IS the message. The hook question
  fades in tied to the right panel's completion, not the loop's end.

## Go to school — `figure5_chalk.html`

**Regeneration prompt:**

> A chalkboard figure contrasting independent top-1 drafting with path
> selection. Shared setup line: verified prefix "The fastest way to __ __ __
> __". Left panel "INDEPENDENT TOP-1": four candidate columns (pos 1–4),
> each picks its own top token, producing "get **to to** school" ✗ — with a
> little chalk drawing of a walker stopped at a construction barrier, and an
> acceptance curve that sags at later positions. Right panel "PATH
> SELECTION": same columns but picks form a coherent path, "get **to school
> quickly**" ✓ — chalk drawing of a runner, and a flat acceptance curve.

**Phase-1 mock:**

```
+--------------------------------------------------------------+
|  verified prefix: "The fastest way to __ __ __ __"           |
| +--------------------------+  +----------------------------+ |
| : INDEPENDENT TOP-1        :  : PATH SELECTION             : |
| : pos1  pos2  pos3  pos4   :  : pos1  pos2  pos3  pos4     : |
| : [get*][to*] [to*][school*]  : [get*][to*] [school*][quickly*] |
| : learn started school qui..  : ...same cols, diff picks   : |
| : "get to to school" ✗     :  : "get to school quickly" ✓  : |
| : (stick figure: blocked)  :  : (stick figure: running)    : |
| : acceptance: \_ tail sags :  : acceptance: ---- flat      : |
| +--------------------------+  +----------------------------+ |
|                                                    [replay]  |
+--------------------------------------------------------------+

Beats: 0.5 left grid · 2.2 left result ✗ · 2.5 pictogram · 2.9 note
       3.6 right grid · 5.4 right result ✓ · 7.6 acceptance curves draw
       9.4 "tail sags" annotation · freeze
```

**Implementation notes:**

- Beats are **declarative** here: every revealed element carries
  `class="el" data-t="2.2"`, and `paint(t)` is just "toggle `.show` on
  every `.el` whose `data-t ≤ t`". Prefer this variant when a figure is
  many small reveals rather than continuous motion — the beat table lives
  in the markup itself.
- Candidate columns: the chosen token gets `.pick` (brighter border); the
  colliding token additionally `.dup`, the failure tokens wrapped in
  `.bad` (and the fix in `.ok`) inside the quoted result line.
- The pictograms are tiny **hand-drawn inline SVGs** (~170×52): stick
  figures from circles + stroked paths, `stroke-linecap:round`,
  `stroke-width:1.7`, chalk color, slip filter on the whole `<svg>`.
  Draw meaning, not clip-art: blocked walker + barrier vs runner + motion
  dashes. Give each an `aria-label`.
- Acceptance curves are polyline paths revealed by the
  `stroke-dasharray/dashoffset` draw-on recipe; the sagging tail vs flat
  shape is the quantitative punchline, annotated with a chalk
  "← tail sags" note that appears late, like a teacher circling back.

## Dog and cat — `figure7_chalk.html`

**Regeneration prompt:**

> A chalkboard figure making strict vs relaxed verification *felt*. Setup
> line: `"The best pet is a ___"`, where the target model says cat 50% /
> dog 50%. Two chalk toggle buttons: "strict rejection sampling" keeps the
> output at the target's 50/50; "relaxed rule" drifts it to 20/80. Show a
> 🐈 and a 🐕 whose sizes ARE the distribution — under the relaxed rule the
> dog visibly balloons. Verdict line: "the output keeps the target's 50/50"
> vs "the best pet becomes a dog".

**Phase-1 mock:**

```
+--------------------------------------------------------------+
|        "The best pet is a ___"                               |
|                                                              |
|   [strict rejection sampling]*   [ relaxed rule ]            |
|                                                              |
|        🐈  50%              🐕  50%                          |
|        CAT                  DOG                              |
|   (emoji font-size = share: relaxed -> small cat, HUGE dog)  |
|                                                              |
|        the output keeps the target's 50/50                   |
+--------------------------------------------------------------+

No timeline: this is a TOGGLE figure. Beats table is just the two states:
strict -> 50/50 · relax -> 20/80 + verdict swap.
```

**Implementation notes:**

- This is the **mode-toggle** variant: no clock, no replay eraser — the two
  chalk buttons are the whole control surface, and `render(mode)` plays the
  role of `paint(t)` (same idempotency rule: each mode renders from
  scratch).
- The data-carrying trick: `fontSize = 40 + 130 * share` — the emoji IS the
  bar chart. No axes, no bars, and the point lands harder because it's a
  dog getting fat.
- Numbers stay on screen (`50%`/`80%` under each pet) so the joke never
  replaces the quantity — fun carries the data, it doesn't hide it.
- Toggle buttons are chalk pills: current mode gets `.on` (brighter border
  + fill); both slip-filtered like everything else.
- The verdict line is the wink, written deadpan: "the best pet becomes a
  dog". One wink per figure.

## The rest, in one line each

- `rejection_sampling_chalk-v1.html` — mostly-static diagram; shows the style
  works without a timeline (no beats, no playhead).
- `figure6_chalk.html` — the full decoding race: many moving chips, one shared
  time axis; the maximal version of the chips + progress pattern.
- `dflash_flat_cost_chalk-v1.html` — slider-driven: `paint(sliderValue)`
  instead of `paint(clockTime)`; SVG cost curves + a reading line.
- `dflash_kv_injection_chalk-v1.html` — the multi-diagram figure: several
  labeled SVG panels on one board; shows how far pure hand-drawn SVG
  (paths + text, slip-filtered) can carry an architecture explanation.
- `figure1_chalk.html` — twin timeline panels (vanilla vs speculative), the
  canonical chips/chunks/playhead/status construction.
