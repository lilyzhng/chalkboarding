---
name: chalkboarding
description: >
  Create animated chalkboard-style HTML figures, a green slate in a wooden frame,
  hand-drawn chalk lettering, wobbly strokes, and elements that animate onto the
  board like a lecture unfolding. Use this skill whenever the user asks for a
  "chalkboard figure", "chalk figure", "blackboard diagram", a figure for a paper,
  blog, talk, or teaching material in the chalkboard style, or wants to convert a
  sketch/mock/idea into one. Also use it when iterating on any existing *_chalk.html
  figure. The workflow starts with a cheap ASCII mock for layout sign-off, then
  converts it into the chalkboard design system.
---

# Chalkboard figures

Build a self-contained HTML file that looks like a hand-drawn chalkboard and
animates like a lecture: elements appear in a narrative order, a playhead or
status line tells the viewer where they are, and an eraser button replays the
whole thing. The output embeds cleanly in a webpage via iframe and prints as a
static final frame for papers.

The whole workflow is one idea applied repeatedly: **divide and conquer**.
Never ask yourself to conceive and render in the same step, split every hard
visual goal into a structure step and a manifestation step. The ASCII mock
separates *what the figure says* from *how it looks*; tracing separates *the
shape* from *the drawing of it*; `paint(t)` separates *the story's beats*
from *the rendering of any moment*. Whenever part of a figure feels too hard
to produce directly, don't push harder, find the split.

## Phase 0: intake (one questionnaire, always)

Before drawing anything, run ONE intake questionnaire. Use the native
structured multiple-choice UI if the environment has one (in Claude Code that
is the AskUserQuestion tool, with all three questions in a single call);
otherwise ask all three in one concise message with lettered options. Run it
even when the user handed you a description or a sketch up front: pre-fill
the recommended option from what they gave and mark it "(Recommended)", but
still ask. Do not propose a mock or any graphics before the answers are in.

1. **What is the idea?** (header "Idea"). Offer 2-3 candidate one-line
   read-backs of the paragraph or sentence they pasted, e.g. "the one thing
   this figure says is ___". Each option is a different emphasis (mechanism,
   payoff, contrast). They pick one or type their own.
2. **What does it look like?** (header "Layout"). Options:

   A. Line chart: curves on axes, where a crossing or a gap is the point
   B. Two-panel contrast: same input, two methods, side by side
   C. Step-by-step walkthrough: one beat at a time
   D. Architecture diagram: labeled components and what flows between them

   Write each option's description in terms of THEIR figure, not generic
   text. "Other" is where they describe it in their own words.
3. **How does it move?** (header "Motion"). Plays itself once (default),
   buttons the reader toggles, or a slider the reader drags.

Then go to Phase 1. If one of the figures in `examples/` happens to share the
shape they described, you may open it in Phase 2 as a starting point, but do
not go looking for the closest one, and never bend their picture to fit ours.

Do not skip phase 1 for anything non-trivial, layout
mistakes are 10x cheaper to fix in ASCII than in styled HTML.

## Phase 1: ASCII mock

Turn the idea into an ASCII wireframe in the conversation, at roughly the real
aspect ratio (figures are ~940px wide). Show:

- every panel/box/row with its border and label
- placeholder text where real labels go
- the replay button position (bottom-right)
- an **animation beat table** under the mock: what appears at which second

Example mock:

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

Conventions: `:` dashed panel borders, `[x]` chips, `(...)` grouped chunks,
`=` filled / `-` unfilled progress. Annotate anything that moves with `<-`.

Then approve the mock with a SECOND questionnaire (same native UI). One
question, header "Mock": approve as drawn (Recommended) / one or two concrete
layout alternatives you can see (e.g. flat grids vs a 3D slab, stacked vs side
by side) / "change beats or labels" where they say what to change via Other.
Iterate until they approve the layout and the story beats. If the
user is not available (a batch run, an unattended agent), write the mock and
beat table to `<topic>_mock.md` next to the output and proceed as if approved,
so there is still a contract to check the figure against. The mock
is the contract: the number of panels, the reading order, and the beat table
carry over 1:1 into phase 2.

While mocking, push for **one idea per figure**. A chalkboard reads like a
teacher's board, not a dashboard, if the mock needs more than ~2 panels or
~3 beats-per-panel to make its point, suggest splitting into two figures.

And push to **be fun**. The style works because it feels like a great teacher
at a board, and great teachers reach for silly, concrete, everyday examples:
rejection sampling is "The best pet is a ___" with a cat and a dog, parallel
denoising is painting a kangaroo, path selection is racing to school. So at
mock time, before drawing boxes, ask: *what's the everyday story here, and
who's the character?* An emoji can be the character, and can carry data
(a 🐕 that literally grows as its probability share grows beats a bar chart).
Small winks are welcome (a venue in-joke, a deadpan verdict line like "the
best pet becomes a dog"), one per figure; it's seasoning, not the meal.
Abstract boxes-and-arrows is the fallback, not the default.

**What never goes on the board:** a verdict or moral sentence ("the price is
..."), a source or attribution line ("after X, 'title'"), or any prose that
explains the figure. The board shows the thing; the figure caption in the host
page says what it means and where it came from. Every figure you deliver
should come with a one-line caption for that purpose, written separately.
Labels on the slate stay short and concrete: names, numbers, one-line status.

## Phase 2: convert to chalkboard HTML

Start from `template.html` (a complete working skeleton) and read
`design-system.md` for the visual language: exact colors, board
construction, the chalky font, and the hand-drawn discontinuity system.
For animation recipes (chips, progress fills, playheads, SVG curve draw-on,
pixel grids), read `animation-patterns.md`. Before building,
skim `worked-examples.md` and open the example figure closest to
what you're making, it records regeneration prompts, mocks, and the
implementation tricks (bitmap tracing, declarative `data-t` beats,
hand-drawn SVG pictograms) that the finished files don't explain.

The non-negotiables that make the style read as "chalkboard", all already
wired in the template:

1. **Board**: wooden frame `#7A5230` wrapping a deep-green slate `#12291d`
   with faint radial "chalk dust" lighting. Chalk ink is `#F5F4EF`,
   secondary ink `rgba(245,244,239,.55)`.
2. **Chalky font**: `PencilPete.ttf` for everything on the slate, loaded via
   `@font-face` with a relative `url("PencilPete.ttf")`, copy the font from
   this repo's `fonts/` (or reuse one already in the project) so it sits
   next to the output HTML.
3. **Discontinuity (hand-drawn feel)**: three SVG turbulence filters
   (`#slip1..3`) plus the standard end-of-body script that applies them
   probabilistically, the longer an element, the more likely it wavers,
   exactly like real handwriting. Add every new visual class to that
   script's selector list (SVG `<text>` is not covered by it: put
   `filter:url(#slip1)` on the SVG element directly). Complement with small alternating rotations
   (±0.25°–1.4°) and irregular border-radii like `10px 8px 11px 7px`.
4. **Animation model**: one idempotent `paint(t)` function, beat times as
   named constants at the top of the script, a single rAF loop, and the
   eraser replay button. Never accumulate state per frame, `paint(t)` must
   render any `t` from scratch so replay, reduced-motion (jump to final
   frame), and `beforeprint` (paint final frame) all fall out for free.
5. **Embedding contract**: `background: transparent` on body, `html{zoom:0.8}`,
   and the `postHeight()` snippet that posts `{chalkHeight, chalkSrc}` to the
   parent, this is how host pages size the iframe. Keep it verbatim.

### Complex imagery: trace, don't freehand

You (a coding model) have weak spatial intuition: freehanding a recognizable
kangaroo or an opera house from imagined coordinates produces mush. Don't
try. Split drawing into **trace** (get the shape from a reference) and
**render** (fill it in chalk):

- If you're unsure what the concept even looks like, first find one or two
  reference images (web search) and study them, that's how the diffusion
  analogy figure locked in "left: paint pixel by pixel, right: denoise all
  at once" before any drawing happened.
- For pixel-grid subjects, trace a real image instead of inventing cells:
  `python3 scripts/trace_bitmap.py <image> --size 32` converts any PNG (an
  emoji from the Twemoji repo, a logo, a silhouette) into the `X`/`.` bitmap
  array the pixel-grid recipe consumes. The kangaroo was traced from the
  Twemoji kangaroo's alpha channel this way.
- For SVG pictograms, same principle at lower fidelity: describe the pose in
  a handful of landmark points taken from a reference (head circle, spine
  line, limb angles), then connect them with round-capped strokes, trace
  the skeleton, not the outline.

Freehand is fine only for things with trivial geometry: stick figures,
arrows, boxes, simple charts.

Name the file `<topic>_chalk.html` (append `-v2`, `-v3` when iterating so old
versions stay comparable).

## Phase 3: QA before delivering

Screenshot the figure with `python3 scripts/screenshot_beats.py <file> --beats
<start>,<mid>,<end>` and actually look at the images. Pick the three beats from
your own beat table: start just after t=0, mid right after the key beat, end
past your `END` constant (the defaults `0.3,3,12.5` fit a 10-12s figure, not
yours). Add `--replay` to also click the eraser and shoot the reset. Needs
Python `playwright` with Chromium (`pip install playwright && playwright
install chromium`); in a sandboxed agent, headless Chromium may need the
sandbox off for that one command. Check:

- nothing overflows the slate; chips wrap instead of clipping
- the board height is identical at t=0 and at END (reserve space for every
  late-appearing line with fixed heights; measure both screenshots)
- the final frame is self-sufficient, a reader who only ever sees the frozen
  frame (print, reduced motion) still gets the full message, including
  every label and the "done" state
- text contrast: primary chalk on board, secondary at .55 alpha, nothing dimmer
- the chalky waver is visible on long strokes but labels stay legible
- replay actually resets everything (the `--replay` shot must match the start shot)

Sharing it afterwards: `python3 scripts/export_media.py <file>` renders a
crisp MP4 cropped to the board.
