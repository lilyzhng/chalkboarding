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
4. **Be fun, and hand-drawn.** Great teachers reach for silly, concrete, everyday examples, and draw them in chalk. Stick figures and chalk pictograms, not emoji. Abstract boxes-and-arrows is the fallback, not the default.
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
| Chalkiness | `data-chalk="tidy\|rough\|shaky"` on `.slate`, from question 4. One attribute sets random slate wipes, chalk stroke weight and dust halo, slip and tilt, dash breaks, fade, shape geometry, and a few scattered ghost fragments. Never hand-tune per figure; never ghost the whole figure; never use regular stripes |
| Micro-imperfection | alternating rotations ±0.25° to 1.4°, irregular radii like `10px 8px 11px 7px` |
| Animation | one `paint(t)`, beat constants at the top, single rAF loop, eraser replay button, freeze on final frame |
| Fixed heights | status, tally, badge lines use `height` + `line-height` + `nowrap`, never `min-height`; board height never changes mid-play |
| Embedding | `background:transparent` on body, `html{zoom:0.8}`, `postHeight()` posting `{chalkHeight, chalkSrc}` verbatim. The `body.standalone` rule centers the board when the file is opened directly instead of in an iframe |
| File name | `<topic>_chalk.html`, append `-v2`, `-v3` when iterating. A chalkiness change on an existing figure writes `<topic>_chalk-<preset>.html` beside the original, never over it, so the two can be compared |

Gotchas:

- Every new visual class goes into the slip script's selector list.
- SVG `<text>` is not covered by the script. Put `filter:url(#slip1)` on the SVG element directly.
- Never accumulate state inside the rAF tick. Build DOM once, reveal in `paint`.

## Anti-Slop Rules

The style works because it looks like a human drew it. Anything mass-produced breaks that.

| Rule | Do | Don't |
| --- | --- | --- |
| Emoji budget | at most 1-2 per figure, each a named character that carries data (the 🐕 that grows with its share) | rows or grids of repeated emoji, emoji as bullets, emoji as decoration |
| People and objects | chalk stick figures and pictograms as inline SVG, round-capped strokes, 5-10 paths each (see the walker and runner in `examples/example4_go_to_school.html`) | 🧑‍🎓 x 40, 👤 icons, clip art, photos |
| Crowds and quantities | draw the scale: a row of chalk desks, tally marks, a bar that shrinks, a pie cut thinner | repeating a glyph N times |
| Mock vs manifest | emoji are fine as placeholders in the ASCII mock | carrying mock emoji into the HTML |
| Labels | short, concrete, sometimes lowercase, like a teacher's shorthand | title-case headings, marketing lines, exclamation marks |
| Symmetry | slight rotations, uneven radii, a line that wavers | pixel-perfect alignment, identical repeated elements |

If a mock uses an emoji, decide at manifest time: is this the one character (keep it) or a crowd (draw it in chalk)?

## Board Content Rules

| On the slate | Off the slate (caption) |
| --- | --- |
| names, numbers, one-line status | verdict or moral ("the price is ...") |
| the character and its data | source or attribution ("after X, 'title'") |
| done badges, beat labels | prose that explains the figure |

One wink per figure (a venue in-joke, a deadpan verdict line). Seasoning, not the meal.

---

## Phase 0: Intake Questionnaire

Run ONE questionnaire with all four questions in a single call. Use the native structured UI (AskUserQuestion in Claude Code); otherwise one message with lettered options. Pre-fill the recommended option from anything the user gave and mark it "(Recommended)". Do not propose a mock or graphics before the answers are in.

| # | Header | Question | Options |
| --- | --- | --- | --- |
| 1 | Idea | What is the one thing this figure says? | 2-3 one-line read-backs of their text, each a different emphasis (mechanism / payoff / contrast) |
| 2 | Layout | What does it look like? | A. Line chart: a crossing or gap is the point. B. Two-panel contrast: same input, two methods. C. Step-by-step walkthrough: one beat at a time. D. Architecture diagram: components and flows |
| 3 | Motion | How does it move? | Plays itself once (default) / buttons the reader toggles / slider the reader drags |
| 4 | Chalk | How chalky? | Tidy (default): a careful teacher, light dust, faint waver on long strokes / Rough: end of a long day, strokes skip and break, long lines fade, shapes tilt / Shaky: a first-day teacher, circles come out different sizes, boxes do not close at the corner, most lines broken, everything tilts |

Write each layout option in terms of THEIR figure, not generic text. "Other" is where they describe it in their own words.

If a figure in `examples/` shares the shape they chose, you may open it in Phase 2 as a starting point. Do not go looking for the closest one, and never bend their picture to fit ours.

## Phase 1: ASCII Mock

Layout mistakes are 10x cheaper to fix in ASCII than in styled HTML. Never skip this for anything non-trivial.

Before drawing boxes, ask: what's the everyday story here, and who's the character? Rejection sampling is "The best pet is a ___" with a cat and a dog. Parallel denoising is painting a kangaroo. Path selection is racing to school. Emoji are allowed here as placeholders; in Phase 2 they become chalk drawings (see Anti-Slop Rules).

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
bash scripts/qa.sh <file> --beats <start>,<mid>,<end> --replay
```

Pick the three beats from your own beat table: just after t=0, right after the key beat, past your `END` constant. The defaults `0.3,3,12.5` fit a 10-12s figure, not yours. First run installs Playwright into `~/.cache/chalkboarding` by itself. A sandboxed agent may need the sandbox off for that one command.

Look at every image and check:

- [ ] nothing overflows the slate; chips wrap instead of clipping
- [ ] board height identical at t=0 and at END (measure both screenshots)
- [ ] final frame is self-sufficient: print and reduced-motion readers get every label and the done state
- [ ] contrast: primary chalk, secondary at .55 alpha, nothing dimmer
- [ ] waver visible on long strokes, labels still legible
- [ ] the `--replay` shot matches the start shot
- [ ] emoji count is 0-2 and none repeat; every crowd is drawn in chalk
- [ ] if the preset is not tidy, a side-by-side tidy-vs-preset screenshot shows a difference at a glance

Deliver the file plus the one-line caption.

## Phase 4: Share & Export

After delivering the file and caption, ask with the native questionnaire (header "Export"):

- MP4 (Recommended): crisp, for X, slides, and GitHub attachments (click to play)
- GIF: softer and larger, but autoplays and loops in a README `<img>`
- Both
- No thanks

If they decline, stop. Otherwise run the wrapper. It installs Playwright by itself on first run and needs ffmpeg (`brew install ffmpeg`).

```bash
bash scripts/export.sh <file>                 # <file>.mp4 next to the input
bash scripts/export.sh <file> --gif           # also <file>.gif
bash scripts/export.sh <file> --seconds 9     # match the figure's END constant
bash scripts/export.sh toggle_chalk.html --click "#mRelax@4"   # click a control mid-clip
```

Then tell the user the output path and size, and that redoing the export overwrites the same file.

### Voice-over (optional, macOS)

A figure is silent by default. To turn it into a narrated explainer, declare
spoken lines against the figure's beats and export with `--narrate`:

```bash
bash scripts/export.sh <file> --narrate                                  # macOS say
OPENROUTER_API_KEY=... bash scripts/export.sh <file> --narrate --tts openrouter --voice nova   # GPT voice
```

Narration is placed at absolute timestamps (the video stays authoritative, so
it never drifts out of sync). Off unless asked for. Backends: macOS `say`
(no key) or `openrouter` (GPT voices, needs `OPENROUTER_API_KEY`). Full format
and timing rules in `narration.md`.
