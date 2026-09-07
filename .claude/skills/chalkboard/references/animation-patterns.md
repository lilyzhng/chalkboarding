# Animation patterns

The figures animate like a lecture: a fixed script of beats, replayable,
frozen-frame safe. Everything below assumes the core model.

## The core model: idempotent paint(t)

One function renders the entire board for any time `t` (seconds), from
scratch. No per-frame accumulation, no tweens that depend on the previous
frame. Beats are named constants up top:

```js
(function(){
  var T_ROUND1 = 1.65, T_ROUND2 = 3.3, V_DONE = 10.0, END = 11.5;

  function paint(t){
    // toggle classes / set widths purely as a function of t
    chip.classList.toggle('show', t >= T_ROUND1);
    fill.style.width = (Math.min(t, V_DONE) / AXIS * 100) + '%';
    done.style.opacity = t >= V_DONE ? '1' : '0';
  }

  var replay = document.getElementById('replay');
  var t0 = performance.now(), raf = null;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function tick(){
    var t = (performance.now() - t0) / 1000;
    if (t >= END){ paint(END); raf = null; return; }   // freeze, don't loop
    paint(t);
    raf = requestAnimationFrame(tick);
  }
  function play(){
    if (raf) cancelAnimationFrame(raf);
    if (reduced){ paint(END); return; }                // reduced motion = final frame
    t0 = performance.now(); paint(0);
    raf = requestAnimationFrame(tick);
  }
  replay.addEventListener('click', play);
  play();
})();
```

Why idempotent: replay, `prefers-reduced-motion`, `beforeprint`, and
screenshot QA all just call `paint(someT)` and get a correct frame. If you
ever find yourself appending DOM inside `tick()`, build the DOM once up
front (hidden) and reveal it in `paint`.

Elements animate in with `opacity:0` + `transition:opacity .3s` and a `.show`
class — the transition gives each appearance a chalk-stroke softness without
per-frame work.

Pacing: total loop 8–12s. End frozen on the final frame (auto-loop is
annoying next to prose); the eraser is the loop.

## Recipes

**Chips appearing over time** (tokens, items): build all `.chip` spans up
front, `paint` toggles `.show` by `t >= (i+1)*STEP`. Chips: irregular radius,
alternating rotation, border `.75` alpha, fill `.05` alpha.

**Grouped chunk reveal** (batches, rounds): wrap chips in a `.chunk` with a
transparent dashed border; on its beat, set border-color visible and show all
child chips at once — reads as "circled a group on the board".

**Progress fill**: absolutely-positioned `.fill` with the streaky
repeating-linear-gradient, `paint` sets `width` as a % of the axis. Under it,
a dotted `.trackbase`.

**Time axis + playhead**: dotted-bottom-border track; ticks and second labels
generated in a loop at `sec/AXIS*100%`; playhead is a 0-width, 2px-left-border
div whose `left` tracks `t`.

**Status line**: dim one-liner per lane, rewritten by `paint` — narrates the
current beat ("round 2: drafting + verifying…"). Give it `min-height` so the
layout doesn't jump. **Done badge**: outlined pill, `opacity:0→1` at its beat,
slight rotation.

**SVG curve draw-on** (plots): stroke the path with
`pathLength`-normalized dashes:

```css
.draw{stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset 1.15s ease .15s}
.draw.on{stroke-dashoffset:0}
```

(set `pathLength="1"` on the path). Gridlines: `stroke:rgba(245,244,239,.13);
stroke-dasharray:5 6`. Axis text in PencilPete, `fill:rgba(245,244,239,.5)`.
Slip-filter the curve itself.

**Pixel-grid canvases** (denoising, raster fills): CSS grid of `<i>` cells,
32 columns. Serial fill = index cutoff; parallel converge = per-cell random
delay + smoothstep blend from noise alpha to a fixed per-cell texture alpha
(`0.72 + ((i*37+11)%23)/100` — deterministic, looks hand-filled). Keep grids
≤ 32×32: this is a chalk sketch, not a framebuffer.

**Interactive sliders**: for explorable figures, a labeled `<input type=range>`
can replace the timeline — `paint` becomes a function of slider value instead
of clock time. Same idempotency rule.

## QA screenshot harness

Playwright + the preinstalled Chromium; capture beats by faking the clock via
paint if exposed, or simply waiting:

```js
const { chromium } = require('playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 980, height: 900 } });
  await p.goto('file://' + process.argv[2]);
  for (const [name, ms] of [['start', 300], ['mid', 3000], ['end', 12500]]) {
    await p.waitForTimeout(name === 'start' ? ms : ms - 300);
    await p.screenshot({ path: `shot_${name}.png`, fullPage: true });
  }
  await b.close();
})();
```

Look at all three images before delivering. The `end` shot is what print and
reduced-motion readers get — it must tell the whole story alone.
