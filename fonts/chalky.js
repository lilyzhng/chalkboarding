// chalky.js: probabilistic "slip" application, weighted by stroke length.
// Last script in the file. Physical intuition: short strokes are easy to draw
// straight, long ones always waver somewhere, so the probability of applying a
// turbulence filter grows with element width until it is certain.
// Requires the three #slip filters from slip-filters.svg to be in the page.
// When you invent a new visual class, ADD IT to the selector below: this is
// the most common way the hand-drawn feel silently goes missing.
(function(){
  var els = document.querySelectorAll('.slate span, .slate button, .slate td, .slate th, .slate .status');
  var slips = ['url(#slip1)', 'url(#slip2)', 'url(#slip3)'];
  els.forEach(function(el, i){
    var w = el.offsetWidth || 0;
    var r = ((i * 61 + 17) % 100) / 100;          // deterministic pseudo-random: identical across reloads and screenshots
    var pClean = w < 60 ? 0.85 : w < 160 ? 0.5 : w < 280 ? 0.15 : 0;
    if (r < pClean) return;
    el.style.filter = slips[i % 3];
  });
})();
