// chalky.js: the hand-drawn imperfection pass. Last script in the file.
//
// One attribute on the slate picks a preset: <div class="slate" data-chalk="tidy|rough|shaky">.
// Every layer reads from that preset, nothing is tuned per figure:
//   slip     turbulence filters on text/chips, applied with probability that grows with width
//            (short strokes are easy to draw straight, long ones always waver somewhere)
//   dust     SVG strokes get heavier, patchy along their length, with a soft halo (#dust filter)
//   breaks   a fraction of strokes get dash gaps, wide enough to survive the dust halo
//   geo      circles vary in size, closed shapes stop short of meeting, each shape tilts on its own
//   ghost    a few individual shapes cloned faintly into random spots, like a half-erased earlier lesson
//   fade     long strokes thin toward their end (#fade gradient), the hand lifting
// Requires #slip1..3, #dust, and #fade from slip-filters.svg to be in the page.
// All randomness is deterministic per element index so screenshots and replay are identical.
// When you invent a new visual class for text, ADD IT to TEXT_SEL: this is the most common
// way the hand-drawn feel silently goes missing.
(function(){
  var CHALK = {
    tidy:  { slip: 1, dust: null,                                   weight: 1,    jitter: 0,   breaks: 0,   geo: null,                              ghost: null,                     fadeOver: 0,
             pClean: function(w){ return w < 60 ? 0.85 : w < 160 ? 0.5 : w < 280 ? 0.15 : 0; } },
    rough: { slip: 3, dust: {slope: 2.4, intercept: -0.25, blur: 1.2}, weight: 1.35, jitter: 0.6, breaks: 0.4, geo: {radius: 0.2,  gap: 0.05, rot: 2}, ghost: {count: 3, opacity: 0.1},  fadeOver: 80,
             pClean: function(){ return 0; } },
    shaky: { slip: 5, dust: {slope: 2.8, intercept: -0.45, blur: 1.6}, weight: 1.6,  jitter: 1.1, breaks: 0.8, geo: {radius: 0.45, gap: 0.13, rot: 5}, ghost: {count: 7, opacity: 0.16}, fadeOver: 40,
             pClean: function(){ return 0; } }
  };
  var TEXT_SEL = '.slate span, .slate button, .slate .status, .slate .title, .slate .tally, .slate td, .slate th';
  var STROKE_SEL = '.slate svg:not(.ghost) path, .slate svg:not(.ghost) circle, .slate svg:not(.ghost) rect';
  var SVG_NS = 'http://www.w3.org/2000/svg';

  var slate = document.querySelector('.slate');
  var preset = CHALK[(slate && slate.getAttribute('data-chalk')) || 'tidy'] || CHALK.tidy;

  // deterministic pseudo-random in [0,1) from an element index and a salt
  function rand(i, salt){ return ((i * salt + 11) % 100) / 100; }
  // strokes the pass may touch: never the replay button, never paths that animate their own dash
  function strokes(){
    return Array.prototype.filter.call(document.querySelectorAll(STROKE_SEL), function(n){
      return !n.closest('.replay') && !n.classList.contains('draw') && !n.classList.contains('cut');
    });
  }
  function isClosed(n){ return n.tagName === 'rect' || n.tagName === 'circle' || /z\s*$/i.test(n.getAttribute('d') || ''); }

  // 1. slip filters scale with the preset
  document.querySelectorAll('feDisplacementMap').forEach(function(m){
    m.setAttribute('scale', (parseFloat(m.getAttribute('scale')) * preset.slip).toFixed(2));
  });

  // 2. dust: heavier, patchy strokes with a halo
  var dustA = document.getElementById('dustA');
  if (dustA && preset.dust){
    dustA.setAttribute('slope', preset.dust.slope);
    dustA.setAttribute('intercept', preset.dust.intercept);
    var blur = document.querySelector('#dust feGaussianBlur');
    if (blur) blur.setAttribute('stdDeviation', preset.dust.blur);
    strokes().forEach(function(n){ n.style.filter = 'url(#dust)'; });
  }

  // 3. weight, jitter, breaks, geometry: one pass over every stroke
  strokes().forEach(function(n, i){
    var r1 = rand(i, 37), r2 = rand(i, 53), r3 = rand(i, 43);
    var sw = parseFloat(getComputedStyle(n).strokeWidth) || 2;
    n.style.strokeWidth = (sw * preset.weight * (1 + (r2 - 0.5) * preset.jitter)).toFixed(2);

    if (preset.breaks && r1 < preset.breaks){
      var gapK = preset.weight > 1.4 ? 3.2 : 2.2;   // gaps must outlive the dilate + halo
      var a = 8 + Math.round(r2 * 16), b = Math.round((2 + r1 * 3) * gapK), c = 12 + Math.round(r1 * 22);
      n.style.strokeDasharray = a + ' ' + b + ' ' + c + ' ' + b;
    }
    if (!preset.geo) return;
    if (n.tagName === 'circle'){
      var r = parseFloat(n.getAttribute('r')) || 0;
      n.setAttribute('r', (r * (1 + (r1 - 0.5) * 2 * preset.geo.radius)).toFixed(2));
      n.setAttribute('cx', (parseFloat(n.getAttribute('cx')) + (r2 - 0.5) * r * 0.4).toFixed(2));
    }
    if (isClosed(n) && preset.geo.gap && !n.style.strokeDasharray){
      // the corner never quite meets
      n.setAttribute('pathLength', '1');
      var g = preset.geo.gap * (0.6 + r3 * 0.8);
      n.style.strokeDasharray = (1 - g).toFixed(3) + ' ' + g.toFixed(3);
      n.style.strokeDashoffset = (r2 * 0.25).toFixed(3);
    }
    if (preset.geo.rot){
      n.style.transformBox = 'fill-box';
      n.style.transformOrigin = 'center';
      n.style.transform = 'rotate(' + ((r1 - 0.5) * 2 * preset.geo.rot).toFixed(2) + 'deg)';
    }
  });

  // 4. ghost fragments: a few shapes from an earlier lesson, scattered and half erased
  var main = document.querySelector('.slate > svg:not(.ghost)');
  if (preset.ghost && main){
    var cands = strokes().filter(function(n){
      return n.closest('svg') === main && !n.classList.contains('tick') && (!n.getTotalLength || n.getTotalLength() > 40);
    });
    var vb = (main.getAttribute('viewBox') || '0 0 860 400').split(/\s+/).map(Number);
    var layer = main.cloneNode(false);
    layer.removeAttribute('id'); layer.removeAttribute('filter'); layer.setAttribute('class', 'ghost');
    for (var k = 0; k < preset.ghost.count && cands.length; k++){
      var src = cands[(k * 7919 + 13) % cands.length];
      var box; try { box = src.getBBox(); } catch(e){ box = {x:0, y:0, width:40, height:40}; }
      var cx = box.x + box.width / 2, cy = box.y + box.height / 2;
      var g1 = rand(k, 37), g2 = rand(k, 61), g3 = rand(k, 83);
      var copy = src.cloneNode(true);
      copy.removeAttribute('id'); copy.removeAttribute('class');
      copy.style.opacity = ''; copy.style.strokeDasharray = ''; copy.style.filter = 'url(#dust)';
      var wrap = document.createElementNS(SVG_NS, 'g');
      wrap.setAttribute('transform',
        'translate(' + (vb[0] + g1 * (vb[2] - box.width) - box.x).toFixed(1) + ' ' + (vb[1] + g2 * (vb[3] - box.height) - box.y).toFixed(1) + ') ' +
        'rotate(' + ((g2 - 0.5) * 40).toFixed(1) + ' ' + cx + ' ' + cy + ') scale(' + (0.7 + g3 * 0.7).toFixed(2) + ')');
      wrap.style.opacity = (preset.ghost.opacity * (0.6 + g1 * 0.8)).toFixed(3);
      wrap.appendChild(copy); layer.appendChild(wrap);
    }
    main.parentNode.insertBefore(layer, main);
  }

  // 5. fade: long strokes thin toward the end
  if (preset.fadeOver){
    strokes().forEach(function(n){
      try { if (n.getTotalLength() > preset.fadeOver) n.style.stroke = 'url(#fade)'; } catch(e){}
    });
  }

  // 6. slip on text and chips, probability grows with width
  var slips = ['url(#slip1)', 'url(#slip2)', 'url(#slip3)'];
  document.querySelectorAll(TEXT_SEL).forEach(function(el, i){
    if (rand(i, 61) < preset.pClean(el.offsetWidth || 0)) return;
    el.style.filter = slips[i % 3];
  });
})();
