# Chalkboarding

A coding-agent skill that turns an idea into a figure that looks like a teacher drew it on a chalkboard, and animates it as if you were sitting in the class: things appear in the order the teacher would draw them, and an eraser button replays the lesson. One HTML file, no dependencies. Embed it in a page, print the final frame for a paper, or export an MP4 for Twitter.

The trick is to never think and draw in the same step. Sketch the layout in ASCII first, trace shapes instead of freehanding them, then render.

Built for the NeurIPS 2026 education tutorial [*Speculative Decoding: How It Evolved, When It Stays Lossless, and What's Next*](https://neurips2026-speculative-decoding.vercel.app/). Works with any coding agent that can read files and run a shell.

## Examples

### Figure 1. Kangaroo: painting an image sequentially vs in parallel

https://github.com/user-attachments/assets/d4eff0ee-45d7-4bdc-b8d8-57984cc0f88f

**Concept.** Two ways to generate the same image: pixel by pixel, or all pixels at once as a diffusion model does. The parallel canvas finishes first.
**Why this figure.** It introduces the idea of drafting tokens in parallel by contrast with the sequential way everyone already knows. The kangaroo was traced from an emoji with `scripts/trace_bitmap.py`, so the task became filling a grid instead of drawing an animal.

### Figure 2. Rejection sampling: the target checks every draft token

https://github.com/user-attachments/assets/b71646c8-2cb6-4e42-96da-a616fe2a583a

**Concept.** The draft proposes "NeurIPS 2026 is in San Diego". For each token, the target compares its probability p with the draft's q and accepts with probability min(1, p/q). "San Diego" is rejected and corrected to "Sydney"; everything after it is discarded.
**Why this figure.** This is the rule that makes speculative decoding lossless, and it is easiest to believe when you watch it run on one sentence with the numbers visible.

### Figure 3. Drafting cost vs block size

https://github.com/user-attachments/assets/7f75ebc7-65be-41d9-b850-fd208a1d1d23

**Concept.** How much a drafter costs to propose a block of γ tokens. An autoregressive drafter (EAGLE-3) pays one layer-pass per token, a diagonal. A parallel drafter (DFlash) pays a flat five. The lines cross at the break-even block size.
**Why this figure.** A chart that draws itself as the slider sweeps from 1 to 16, then stays draggable, so the reader can find the break-even point with their own hand.

### Figure 4. Go to school: independent top-1 vs path selection

https://github.com/user-attachments/assets/a6be0baa-2bb7-4260-9b30-df08cc7472aa

**Concept.** Same prefix, "The fastest way to ___ ___ ___ ___", drafted two ways. When each position picks its own top token, neighbors collide into "get to to school". When adjacent positions are scored together, one coherent path wins: "get to school quickly".
**Why this figure.** It shows why parallel drafts lose acceptance at later positions and how path selection fixes it, with a walker stuck at a barrier and a runner reaching the school as the two outcomes.

### Figure 5. How the internet works: a click's journey, with voice-over

Contributed by [@rajpdus](https://github.com/rajpdus).

https://github.com/user-attachments/assets/815e5c1e-3a50-4eda-bc58-c1ee4baec079

**Concept.** You tap play on a cat video. The click travels to your router, your ISP, across the internet to a server, which chops the video into packets that race back and reassemble on your screen.
**Why this figure.** The first narrated example. Lines are declared against the figure's beats and voiced by Gemini TTS with `--narrate`, so the board shows and a teacher tells.

Four more live in `examples/`, each with an MP4 in `examples/media/`: dog and cat (strict vs relaxed verification), the decoding race, twin timelines, and KV injection. `worked-examples.md` records the prompt, the ASCII mock, and the implementation tricks for the richest ones.

### Key Features

- **The Chalk Hand**: One font plus three layers of imperfection: SVG turbulence filters applied with probability that grows with stroke length, alternating micro-rotations, irregular corner radii. Everything that makes text read as hand-drawn lives in `fonts/`.
- **Trace, Don't Freehand**: Coding models have weak spatial sense. `scripts/trace_bitmap.py` turns any image (an emoji, a logo, a silhouette) into the pixel bitmap a figure consumes. The kangaroo was traced from the Twemoji kangaroo's alpha channel.
- **Replay, Reduced Motion, Print**: One `paint(t)` function renders any moment from scratch, so the eraser button, `prefers-reduced-motion`, and `beforeprint` all fall out for free.
- **Be Fun**: A great teacher reaches for silly concrete examples. Rejection sampling is "The best pet is a ___" with a cat and a dog. Parallel denoising is painting a kangaroo. The skill pushes for a character and an everyday story before it draws boxes.

## Installation

### Claude Code

Clone directly into your skills directory:

```bash
git clone https://github.com/lilyzhng/chalkboarding.git ~/.claude/skills/chalkboarding
```

Then type `/chalkboarding` in Claude Code (the skill's `name` in `SKILL.md` matches). To use it in one project only, clone it anywhere and point Claude Code at `SKILL.md`.

### Other Coding Agents

Agents such as Codex, Kimi Code, OpenCode, Gemini CLI, or any local coding assistant can use the same skill. The simplest path is to send the agent this repo link and ask it to use the Chalkboarding skill:

```text
https://github.com/lilyzhng/chalkboarding
```

If the agent can read GitHub repos or browse files, it should start from `SKILL.md` and load the support files it references only when needed (see [Architecture](#architecture)).

Some agents can also install the skill for you if they have filesystem access and a known local skills directory. If not, they can follow `SKILL.md` directly for the current session. Whatever the agent, the one file that must be copied is `fonts/PencilPete.ttf`: it goes next to every generated figure.

## Usage

### Create a New Figure

```text
/chalkboarding

> "A chalkboard figure for the diffusion analogy: two canvases painting the
>  same kangaroo, one pixel by pixel, one denoising all pixels at once"
```

The skill will:

1. Ask three questions, one at a time: paste the idea, pick the shape (line chart, two-panel contrast, step-by-step walkthrough, architecture diagram, help me decide, or chat with me), and how it moves (plays itself, toggle, slider)
2. Sketch an ASCII mock with an animation beat table, and iterate until you approve it
3. Trace any complex imagery from a reference instead of freehanding it
4. Convert the mock into chalkboard HTML from `template.html` using the design system
5. Screenshot start, mid, and final frames and check that the final frame carries the whole message alone

### Export a Demo Video or GIF

```bash
bash scripts/export.sh my_chalk.html                          # 1200px MP4, cropped to the board
bash scripts/export.sh my_chalk.html --seconds 10             # match the figure's own length
bash scripts/export.sh toggle_chalk.html --click "#mRelax@4"  # click a control mid-clip
```

Add `--gif` if you need a GIF. Add `--narrate --tts gemini --voice female` for a voice-over (needs `GEMINI_API_KEY`; `--tts openrouter` for GPT voices, or plain `--narrate` for macOS `say`).

### Trace an Image into a Pixel Grid

```bash
python3 scripts/trace_bitmap.py kangaroo.png --size 32   # prints the X/. bitmap array
```

## Architecture

`SKILL.md` is a workflow map. Supporting files load on demand:

| File | Purpose | Loaded When |
| --- | --- | --- |
| `SKILL.md` | Three-phase workflow and the non-negotiables | Always |
| `design-system.md` | Exact colors, board construction, the chalk hand | Phase 2 (build) |
| `animation-patterns.md` | `paint(t)` model, chips, fills, playheads, pixel grids, SVG draw-on | Phase 2 (build) |
| `worked-examples.md` | Prompt, mock, and implementation notes for the example figures | Phase 2, when picking a starting point |
| `template.html` | Complete working skeleton with everything wired in | Phase 2 (build) |
| `chalkboard.css` | The template's base CSS as a standalone file | When pasting into an existing page |
| `fonts/` | The chalk face and the three-layer discontinuity system | Phase 2 (build) |
| `scripts/trace_bitmap.py` | Image to pixel-grid bitmap | Phase 2, for complex imagery |
| `scripts/qa.sh` | Start / mid / end QA screenshots. Installs its own Playwright on first run | Phase 3 (QA) |
| `scripts/export.sh` | Crisp MP4 (and GIF) export, cropped to the board. Needs ffmpeg | Sharing |
| `scripts/screenshot_beats.py`, `scripts/export_media.py` | The Python behind the two wrappers, if you already have Playwright | |

## Requirements

- A local coding agent with filesystem access and the ability to run shell commands
- For QA screenshots and media export: Python with `playwright` (`pip install playwright && playwright install chromium`) and `ffmpeg` on PATH. Sandboxed agents may need the sandbox off for the headless Chromium commands.
- For tracing: Python with `Pillow`

## Credits

Created by [@lily_gpupoor](https://x.com/lily_gpupoor) and [@Madisonkanna](https://x.com/Madisonkanna). Voice-over by [@rajpdus](https://github.com/rajpdus).

## License

MIT for the code. The font in `fonts/` is third-party; check its license before redistributing.
