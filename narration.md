# Narration (optional voice-over)

A chalk figure is silent by default — the board shows, the caption tells. But a
figure already plays on a fixed schedule of beats, so it can carry an **optional
voice-over** that turns it into a narrated explainer. This is off unless you ask
for it, and it never changes the silent export.

> Three backends: macOS `say` (built in, no key), `openrouter` (GPT voices, needs
> `OPENROUTER_API_KEY`), and `gemini` (Gemini TTS, needs `GEMINI_API_KEY`; the
> most natural of the three). The TTS layer is a small seam
> (`BACKENDS` in `scripts/narrate.py`) so more can be added without changing the
> narration format below.

## 1. Declare the lines with the figure

The video is authoritative: narration is placed at **absolute timestamps**, not
concatenated, so it can never drift out of sync. Give each line the second at
which it should start — reuse the figure's own beat times (the `data-t` / status
beats). Keep narration WITH the figure (the skill's "one HTML file" principle)
in an embedded block:

```html
<script type="application/vo+json" id="vo">
[
  {"t": 0,  "text": "Ever wonder what happens when you tap play on a video?"},
  {"t": 7,  "text": "First, your tap zips off to your home router."},
  {"t": 15, "text": "The router hands it to your ISP."}
]
</script>
```

Fallbacks, in order: `--vo <file.json>` → a sidecar `<figure>_vo.json` next to
the HTML → the embedded block above.

**Timing rule.** Each line should fit inside its beat window: `start + spoken
length ≤ the next line's start`. `narrate.py` prints a fit table and flags any
`OVERFLOW` (an overrun only overlaps the next line briefly — it won't desync).
The final line may run past the figure's end; the video is extended with a
frozen last frame to cover it.

## 2. Export with a voice

```bash
bash scripts/export.sh my_chalk.html --narrate                                   # macOS say, Samantha
bash scripts/export.sh my_chalk.html --narrate --voice "Serena (Premium)"        # a Premium say voice, if installed
OPENROUTER_API_KEY=... bash scripts/export.sh my_chalk.html --narrate --tts openrouter --voice nova   # GPT voice
GEMINI_API_KEY=...     bash scripts/export.sh my_chalk.html --narrate --tts gemini --voice Kore       # Gemini TTS
```

Gemini voices (`--tts gemini`): Kore, Puck, Zephyr, Aoede, Charon, Fenrir, Leda, Orus and more. Model defaults to `gemini-3.1-flash-tts-preview`; override with `GEMINI_TTS_MODEL`.

GPT voices (`--tts openrouter`): alloy, ash, ballad, coral, echo, fable, nova, onyx,
sage, shimmer, verse. Model defaults to `openai/gpt-audio-mini`; override with
`OPENROUTER_TTS_MODEL`. Delivery style is a system prompt, override with `NARRATE_STYLE`.

`export.sh` renders the silent MP4 as usual, then muxes the voice-over onto it
(video stream copied, so no quality loss). Without `--narrate`, nothing changes.

Discover installed voices with `say -v '?'`; the **Premium / Enhanced** entries
are neural and sound best (e.g. `Serena (Premium)`, `Isha (Premium)`). Add more
in System Settings → Accessibility → Spoken Content → System Voice → Manage.

On a host where the backend isn't available (non-macOS, or `say` missing),
`narrate.py` prints a note and exits without changing the video — the silent
export still ships.

## 3. Run it directly (without re-exporting)

If you already have the MP4, add narration to it in place:

```bash
python3 scripts/narrate.py my_chalk.html my_chalk.mp4 --voice "Isha (Premium)"
```

## Adding another TTS backend

Implement a class with `name`, `available()`, and
`synth(text, out_m4a, voice)`, then register it in `BACKENDS`. The narration
format, timestamp mixing, and mux logic stay the same; only synthesis changes.
