---
name: chalkboarding
description: >
  Turns an idea into a figure that looks like a teacher drew it on a chalkboard
  and animates it like a lesson: things appear in the order the teacher would
  draw them, an eraser replays. One HTML file. Use when the user says
  "chalkboard figure", "chalk figure", or "blackboard diagram", wants a sketch
  or idea turned into one, or iterates on any *_chalk.html file.
---

# Chalkboard figures

One self-contained HTML file that looks like a hand-drawn chalkboard and plays
like a lecture. Embeds via iframe, prints as the final frame, exports to MP4.

## Core Principles

1. **Divide and conquer.** Never conceive and render in the same step. Every hard visual goal splits into a structure step and a manifestation step. When something feels too hard to produce directly, find the split.
2. **Ask before drawing.** One native questionnaire before any mock, a second one to approve the mock. Even when the user handed you a description.
3. **One idea per figure.** A teacher's board, not a dashboard. More than ~2 panels or ~3 beats per panel means two figures.
4. **Be fun.** Great teachers reach for silly, concrete, everyday examples. An emoji can be the character and carry the data. Abstract boxes-and-arrows is the fallback, not the default.
5. **The board shows, the caption tells.** No verdicts, morals, sources, or explanatory prose on the slate. Deliver a one-line caption separately.
6. **Idempotent `paint(t)`.** One function renders any moment from scratch. Replay, reduced motion, and print all fall out for free.
7. **Trace, don't freehand.** You have weak spatial intuition. Get shapes from references, then render them in chalk.

The three splits behind principle 1:

| Split | Structure | Manifestation |
| --- | --- | --- |
| ASCII mock | what the figure says | how it looks |
| Tracing | the shape | the drawing of it |
| `paint(t)` | the story's beats | the rendering of any moment |

## Design Rules (NON-NEGOTIABLE)

All wired into `template.html`. Full spec in `design-system.md`.

| Rule | Value |
| --- | --- |
| Frame | wood `#7A5230` |
| Slate | deep green `#12291d` with faint radial chalk-dust lighting |
| Chalk ink | `#F5F4EF`, secondary `rgba(245,244,239,.55)`, nothing dimmer |
| Font | `PencilPete.ttf` for everything on the slate, relative `url("PencilPete.ttf")`, copied next to the output |
| Hand-drawn waver | SVG turbulence filters `#slip1..3` applied probabilistically by the end-of-body script; longer element = more likely to waver |
| Micro-imperfection | alternating rotations ±0.25° to 1.4°, irregular radii like `10px 8px 11px 7px` |
| Animation | one `paint(t)`, beat constants at the top, single rAF loop, eraser replay button, freeze on final frame |
| Fixed heights | status, tally, badge lines use `height` + `line-height` + `nowrap`, never `min-height`; board height never changes mid-play |
| Embedding | `background:transparent` on body, `html{zoom:0.8}`, `postHeight()` posting `{chalkHeight, chalkSrc}` verbatim |
| File name | `<topic>_chalk.html`, append `-v2`, `-v3` when iterating |

Gotchas:

- Every new visual class goes into the slip script's selector list.
- SVG `<text>` is not covered by the script. Put `filter:url(#slip1)` on the SVG element directly.
- Never accumulate state inside the rAF tick. Build DOM once, reveal in `paint`.

## Board Content Rules

| On the slate | Off the slate (caption) |
| --- | --- |
| names, numbers, one-line status | verdict or moral ("the price is ...") |
| the character and its data | source or attribution ("after X, 'title'") |
| done badges, beat labels | prose that explains the figure |

One wink per figure (a venue in-joke, a deadpan verdict line). Seasoning, not the meal.

---

## Phase 0: Intake Questionnaire

Run ONE questionnaire with all three questions in a single call. Use the native structured UI (AskUserQuestion in Claude Code); otherwise one message with lettered options. Pre-fill the recommended option from anything the user gave and mark it "(Recommended)". Do not propose a mock or graphics before the answers are in.

| # | Header | Question | Options |
| --- | --- | --- | --- |
| 1 | Idea | What is the one thing this figure says? | 2-3 one-line read-backs of their text, each a different emphasis (mechanism / payoff / contrast) |
| 2 | Layout | What does it look like? | A. Line chart: a crossing or gap is the point. B. Two-panel contrast: same input, two methods. C. Step-by-step walkthrough: one beat at a time. D. Architecture diagram: components and flows |
| 3 | Motion | How does it move? | Plays itself once (default) / buttons the reader toggles / slider the reader drags |

Write each layout option in terms of THEIR figure, not generic text. "Other" is where they describe it in their own words.

If a figure in `examples/` shares the shape they chose, you may open it in Phase 2 as a starting point. Do not go looking for the closest one, and never bend their picture to fit ours.

## Phase 1: ASCII Mock

Layout mistakes are 10x cheaper to fix in ASCII than in styled HTML. Never skip this for anything non-trivial.

Before drawing boxes, ask: what's the everyday story here, and who's the character? Rejection sampling is "The best pet is a ___" with a cat and a dog. Parallel denoising is painting a kangaroo. Path selection is racing to school.

The mock shows, at roughly the real aspect ratio (~940px wide):

- every panel, box, and row with its border and label
- placeholder text where real labels go
- the replay button, bottom-right
- a **beat table** underneath: what appears at which second

```
+--------------------------------------------------------------+
| time ->  |0s----1s----2s----3s----4s----5s---...---10s|      |
| +----------------------------------------------------------+ |
| : VANILLA DECODING                          (done · 10.0s) : |
| : [Happiness][can][be][found]...   <- one chip per second  : |
| : ============------------------   <- chalk progress fill  : |
| :  target pass 4 of 10...          <- status line          : |
| +----------------------------------------------------------+ |
| +----------------------------------------------------------+ |
| : SPECULATIVE DECODING                    (done · 3.3s ✓)  : |
| : ([..5 chips..]) ([..5 chips..])  <- chunks per round     : |
| +----------------------------------------------------------+ |
|                                              [eraser/replay] |
+--------------------------------------------------------------+

Beats: t=0 start · t=1.65 chunk 1 · t=3.3 chunk 2 + done badge
       t=10 vanilla done · t=11.5 freeze (loop end)
```

| Symbol | Meaning |
| --- | --- |
| `:` | dashed panel border |
| `[x]` | chip |
| `(...)` | grouped chunk |
| `=` / `-` | filled / unfilled progress |
| `<-` | annotation on anything that moves |

**Approve with a SECOND questionnaire.** One question, header "Mock":

- Approve as drawn (Recommended)
- One or two concrete layout alternatives you can see (flat grids vs 3D slab, stacked vs side by side)
- Change beats or labels (they say what via Other)

Iterate until approved. The mock is the contract: panel count, reading order, and beat table carry 1:1 into Phase 2. If no user is available (batch run, unattended agent), write the mock and beat table to `<topic>_mock.md` next to the output and proceed as if approved.

## Phase 2: Build the HTML

Read in this order:

| File | For |
| --- | --- |
| `template.html` | the working skeleton to start from |
| `design-system.md` | exact colors, board construction, font, waver system |
| `animation-patterns.md` | recipes: chips, progress fills, playheads, SVG draw-on, pixel grids, sliders |
| `worked-examples.md` | prompts, mocks, and tricks behind the richest examples |

Open the example closest to the approved mock as a starting point.

### Complex imagery: trace, don't freehand

Freehanding a kangaroo or an opera house from imagined coordinates produces mush. Split into **trace** (shape from a reference) and **render** (fill in chalk).

| Subject | Method |
| --- | --- |
| Unclear concept | find 1-2 reference images first, study them, then draw |
| Pixel grid | `python3 scripts/trace_bitmap.py <image> --size 32` turns any PNG (Twemoji emoji, logo, silhouette) into the `X`/`.` bitmap the grid recipe consumes |
| SVG pictogram | take a handful of landmark points from a reference (head circle, spine, limb angles), connect with round-capped strokes. Trace the skeleton, not the outline |
| Trivial geometry | freehand is fine: stick figures, arrows, boxes, simple charts |

## Phase 3: QA Before Delivering

```
python3 scripts/screenshot_beats.py <file> --beats <start>,<mid>,<end> --replay
```

Pick the three beats from your own beat table: just after t=0, right after the key beat, past your `END` constant. The defaults `0.3,3,12.5` fit a 10-12s figure, not yours. Needs `pip install playwright && playwright install chromium`; a sandboxed agent may need the sandbox off for that one command.

Look at every image and check:

- [ ] nothing overflows the slate; chips wrap instead of clipping
- [ ] board height identical at t=0 and at END (measure both screenshots)
- [ ] final frame is self-sufficient: print and reduced-motion readers get every label and the done state
- [ ] contrast: primary chalk, secondary at .55 alpha, nothing dimmer
- [ ] waver visible on long strokes, labels still legible
- [ ] the `--replay` shot matches the start shot

Deliver the file plus the one-line caption.

## Export

```
python3 scripts/export_media.py <file>          # 1200px MP4 cropped to the board
python3 scripts/export_media.py <file> --gif    # add a GIF (autoplays and loops in a README)
```

GitHub renders MP4 attachments as a click-to-play player. A GIF via `<img>` autoplays and loops.
