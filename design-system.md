# Chalkboard design system

The exact visual language distilled from the NeurIPS 2026 figure set. Copy
these values verbatim, the style's coherence comes from every figure sharing
them.

## Tokens

```css
:root{
  /* falls back gracefully when standalone; inherits the site's tokens when embedded */
  --_serif: var(--serif, Georgia, 'Iowan Old Style', 'Times New Roman', serif);
  --_ink: var(--ink, #2A2A26);            /* text OUTSIDE the board (captions, h2) */
  --chalk:#F5F4EF;                        /* primary chalk ink */
  --chalk-dim:rgba(245,244,239,.55);      /* secondary chalk: axes, subtitles, status */
  --board:#12291d;                        /* deep green slate */
  --frame:#7A5230;                        /* wooden frame */
}
```

All chalk-colored things derive from `245,244,239` at different alphas:
- borders of active elements: `.75`
- dashed panel borders: `.45`
- gridlines / track dots: `.13`–`.3`
- fills inside chips: `.05` (barely-there chalk residue)

## Page + board construction

```css
*{box-sizing:border-box}
html{zoom:0.8}                            /* figures are authored ~25% oversize */
body{margin:0;padding:0 0 4px;background:transparent;font-family:var(--_serif)}
.wrap{max-width:940px;margin:0 auto}
.board{background:var(--frame);border-radius:16px;padding:12px;position:relative}
.slate{
  position:relative;font-family:'PencilPete',cursive;
  border-radius:10px;padding:30px 34px 52px;color:var(--chalk);
  background:
    radial-gradient(ellipse 60% 40% at 20% 30%, rgba(255,255,255,0.045), transparent 60%),
    radial-gradient(ellipse 50% 45% at 75% 70%, rgba(255,255,255,0.035), transparent 60%),
    radial-gradient(ellipse 40% 30% at 55% 15%, rgba(255,255,255,0.03), transparent 60%),
    var(--board);
}
```

The three faint radial gradients are the "chalk dust in raking light" effect,
without them the slate looks like flat vector green and the illusion dies.

Leave extra bottom padding (~52px) on the slate for the replay button; on
narrow layouts bump it (`@media(max-width:640px)`) so content never collides
with the eraser.

Anything outside the board (an `h2` title, a caption) uses `--_serif` and
`--_ink`, normal typography, the contrast between crisp serif surroundings
and chalky board is part of the look.

## The chalky font

```html
<style>@font-face{font-family:"PencilPete";src:url("PencilPete.ttf") format("truetype");}</style>
```

- `PencilPete.ttf` sits **next to the output HTML** (relative URL: keeps the
  figure portable and iframe-friendly). Copy it from this repo's `fonts/`.
- Everything inside `.slate` inherits `'PencilPete',cursive`.
- The font runs small: body-ish text is `1.15–1.35rem`, panel titles `1.3–1.5rem`
  bold with `letter-spacing:.08em–.18em` (chalk capitals are written spaced out).

## Discontinuity: the hand-drawn system

Three layers, all cheap, together they sell "a person drew this".

### 1. Turbulence slip filters

Once per file, an invisible SVG right after `<body>`:

```html
<svg width="0" height="0" style="position:absolute">
  <filter id="slip1" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.010" numOctaves="2" seed="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3" xChannelSelector="R" yChannelSelector="G"/></filter>
  <filter id="slip2" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.014" numOctaves="2" seed="9" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3.5" xChannelSelector="R" yChannelSelector="G"/></filter>
  <filter id="slip3" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="17" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="2.5" xChannelSelector="R" yChannelSelector="G"/></filter>
</svg>
```

Three different frequencies/seeds so neighboring elements never share the
same waver (that would read as a Photoshop filter, not a hand).

### 2. Probabilistic application, weighted by length

Last script in the file. The physical intuition: short strokes are easy to
draw straight, long ones always waver somewhere. So application probability
grows with element width until it's certain:

```html
<script>
(function(){
  // hand-drawn slips: long strokes are harder to draw straight, so the longer
  // the element, the more likely (and eventually certain) a waver somewhere.
  var els = document.querySelectorAll('.slate span, .slate button, .slate .status, .slate td, .slate th /*, + every custom class you added */');
  var slips = ['url(#slip1)', 'url(#slip2)', 'url(#slip3)'];
  els.forEach(function(el, i){
    var w = el.offsetWidth || 0;
    var r = ((i * 61 + 17) % 100) / 100;          // deterministic pseudo-random
    var pClean = w < 60 ? 0.85 : w < 160 ? 0.5 : w < 280 ? 0.15 : 0;
    if (r < pClean) return;
    el.style.filter = slips[i % 3];
  });
})();
</script>
```

**When you invent a new class, add it to this selector list**, this is the
most common way the effect silently goes missing. Deterministic randomness
(`i*61+17 % 100`) keeps the figure identical across reloads/screenshots.
Same rule for anything structural in a figure (which cells fill first, which
chip wobbles): derive it from the index, never `Math.random()`. Real
randomness is fine only for decorative flicker that is meant to look alive.

For inline SVG strokes, apply a slip directly: `filter:url(#slip1)` on the
path or group.

### 3. Geometry that refuses to be perfect

- Alternating micro-rotations on containers: `.panel.v{transform:rotate(-0.3deg)}`,
  `.panel.s{transform:rotate(0.25deg)}`; badges get a bit more (±1.2–1.4°).
- Chips alternate: `.chip:nth-child(odd){transform:rotate(-1.1deg)}` / even `0.9deg`.
- Irregular corner radii: `border-radius:10px 8px 11px 7px`, four different
  values, always.
- Prefer dashed/dotted strokes over solid: panels `1.5px dashed rgba(...,.45)`,
  axes `2px dotted rgba(...,.3)`.
- Chalk progress fills are streaky, not solid:
  `repeating-linear-gradient(90deg, rgba(245,244,239,.85) 0 6px, rgba(245,244,239,.45) 6px 9px)`.

All rotations must be neutralized under reduced motion:

```css
@media(prefers-reduced-motion:reduce){
  *{transition-duration:.01ms!important}
  .chip,.chunk,.panel{transform:none!important}
}
```

### 4. Chalkiness presets

One attribute on the slate sets all three imperfection systems at once:

```html
<div class="slate" data-chalk="normal">   <!-- tidy | normal | rough -->
```

| Preset | Slip scale | Waver probability | `--tilt` | Grain (gaps in strokes) | Fade (long strokes thin out) | Reads as |
| --- | --- | --- | --- | --- | --- | --- |
| tidy | 0.5x | only elements over 280px, half of them | 0.3 | none | none | a careful teacher, fresh chalk |
| normal | 1x | the length-weighted curve above | 1 | light dust, no visible gaps | none | every example in this repo |
| rough | 2.6x | everything over 60px | 2.2 | visible gaps, chalk skipping on slate | SVG paths over 120px fade to 22% at the end | end of a long lecture |

Five imperfection systems, one attribute. Grain is `#grain`, a noise-masked alpha
filter applied to every SVG stroke on the slate (`filterUnits="userSpaceOnUse"`,
because a perfectly straight line has a zero-width bounding box and would
otherwise vanish). Fade is `#fade`, a horizontal gradient stroke applied to
paths whose `getTotalLength()` exceeds the preset's threshold.

Grain noise is `baseFrequency="0.32"`. Anything much finer is sub-pixel at figure
size and reads as nothing, which is how the first rough preset shipped invisible.
Tune by screenshotting normal and rough stacked and asking whether a reader can
tell them apart at a glance; if not, the preset is not doing its job.

Every `rotate()` in the CSS multiplies by `var(--tilt)`, so new classes should too:
`transform:rotate(calc(-0.8deg * var(--tilt)))`. The slip script reads the attribute
and rescales the `feDisplacementMap` values at load. Set the preset from the
questionnaire; never hand-edit filter numbers per figure.

## The replay eraser

Standard control, bottom-right of the slate, a chalk-drawn replay arrow next
to a skeuomorphic blackboard eraser:

```html
<button class="replay" id="replay" type="button" aria-label="replay"><svg viewBox="0 0 24 24" width="22" height="22" fill="none"><path d="M20.49 15 a9 9 0 1 1 -2.12 -9.36 L23 10" stroke="#F5F4EF" stroke-width="1.8" stroke-linecap="round" fill="none"/><polyline points="23 4 23 10 17 10" stroke="#F5F4EF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg><span class="eraser"></span></button>
```

```css
.replay{position:absolute;bottom:18px;right:28px;z-index:2;display:flex;align-items:center;gap:9px;background:none;border:none;cursor:pointer;padding:0}
.replay svg{display:block;filter:url(#slip2)}
.replay .eraser{
  width:34px;height:17px;border-radius:3px;flex:none;
  background:linear-gradient(#e9e7e2 0%, #cfccc5 58%, #57544d 59%, #45423c 100%);
  box-shadow:0 1.5px 2.5px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.7);
}
.replay:hover .eraser{filter:brightness(1.08)}
.replay:focus-visible{outline:2px solid rgba(245,244,239,.6);outline-offset:3px}
```

## Embedding contract (do not vary)

Host pages embed figures as iframes and size them from a message the figure
posts. Every figure ends with:

```js
window.addEventListener('beforeprint', function(){
  try { if (typeof raf !== 'undefined' && raf) cancelAnimationFrame(raf); } catch(e){}
  try { paint(1e9); } catch(e){}      // print = final frame
});
function postHeight(){
  parent.postMessage({
    chalkHeight: Math.ceil(document.body.getBoundingClientRect().height),
    chalkSrc: location.pathname.split('/').pop()
  }, '*');
}
window.addEventListener('load', postHeight);
window.addEventListener('resize', postHeight);
if (document.fonts && document.fonts.ready) document.fonts.ready.then(postHeight);
setTimeout(postHeight, 1500);
```

Plus `background:transparent` on body and `html{zoom:0.8}` (figures are
authored oversize and zoomed down, text stays crisp, chalk texture tightens).
