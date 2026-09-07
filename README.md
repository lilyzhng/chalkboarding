# chalkboarding

Animated chalkboard-style figures: a green slate in a wooden frame, hand-drawn
chalk lettering with a deliberately wobbly stroke, and elements that animate
onto the board like a lecture unfolding. Originally built for the NeurIPS 2026
education paper figure set.

Each figure is one self-contained HTML file. It embeds in any page via iframe
(the figure posts its own height to the parent), replays via an eraser button,
respects `prefers-reduced-motion`, and prints as a frozen final frame.

## The skill

`.claude/skills/chalkboard/` is a Claude Code skill that produces figures in
this style. Clone the repo and the skill is active in this project; copy the
directory to `~/.claude/skills/` to use it everywhere.

Workflow it enforces:

1. **ASCII mock first** — layout and animation beats sketched as an ASCII
   wireframe in chat, iterated cheaply until approved.
2. **Convert to chalkboard** — from a working template, using the design
   system: board construction, the chalky font, turbulence "slip" filters
   applied probabilistically by stroke length, micro-rotations, irregular
   radii.
3. **QA** — Playwright screenshots at start / mid / final frame before
   delivering; the final frame must carry the whole message on its own.

- `.claude/skills/chalkboard/SKILL.md` — the workflow
- `.claude/skills/chalkboard/references/design-system.md` — exact visual language
- `.claude/skills/chalkboard/references/animation-patterns.md` — animation recipes
- `.claude/skills/chalkboard/assets/template.html` — working skeleton
- `.claude/skills/chalkboard/references/worked-examples.md` — how to regenerate
  the example figures: prompt → ASCII mock → implementation notes
- `.claude/skills/chalkboard/assets/*.ttf` — chalk fonts

## Examples

`examples/` holds representative figures from the NeurIPS set (open directly
in a browser; the font file must sit next to them):

- `rejection_sampling_chalk-v1.html` — rejection sampling; static-leaning diagram
- `dflash_diffusion_analogy_chalk-v5.html` — the kangaroo: pixel-grid serial vs
  parallel canvases
- `figure5_chalk.html` — the "go to school" example: independent top-1 vs path
  selection, SVG curve draw-on
- `figure6_chalk.html` — the full decoding race (from the numbered site-figure set)
- `dflash_flat_cost_chalk-v1.html` — DFlash drafting cost vs block size,
  interactive slider
- `dflash_kv_injection_chalk-v1.html` — DFlash KV injection: the multi-diagram
  figure (SVG-heavy, many labeled panels)
- `figure1_chalk.html` — twin timeline panels, chips + chunks, playhead

## Before open-sourcing

- Verify font licenses/provenance (`PencilPete.ttf`, `ChalkBoard.ttf`) permit
  redistribution, and add a proper LICENSE for the code.
- Scrub examples of anything paper-confidential before flipping to public.
