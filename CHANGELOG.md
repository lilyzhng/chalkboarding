# Changelog

All notable changes to chalkboarding are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Add a bullet under Unreleased in every PR.

## [Unreleased]

### Added
- `.github/pull_request_template.md` and this changelog.

## [0.1.0] - 2026-09-07

First public cut of the skill.

### Added
- Flat coding-agent skill layout: `SKILL.md`, `design-system.md`, `animation-patterns.md`, `worked-examples.md`, `narration.md`, `template.html`.
- Chalk hand in `fonts/` (PencilPete, slip filters, `chalky.js`, `chalky.css`).
- Chalkiness presets `data-chalk tidy|rough|shaky`, chosen in the intake questionnaire. Re-chalking writes `<topic>_chalk-<preset>.html` beside the original.
- `scripts/export.sh` (MP4/GIF via Playwright, `--click` for interactive figures) and `scripts/qa.sh` (beat screenshots, `--replay`).
- `scripts/trace_bitmap.py` for the trace-don't-freehand rule.
- Eight examples in `examples/` with recorded MP4s: kangaroo, rejection sampling, go-to-school, dog-and-cat, decoding race, flat cost, DFlash cost, KV injection.
- Phase 0 intake as one native questionnaire, mock approval as a second; Phase 4 share and export.
- Anti-slop rules: emoji budget 1-2, crowds as chalk pictograms, verdicts in the caption never on the board, no em dashes.

### Fixed
- Board centers when opened directly instead of in an iframe.
- example8 animation restored after copy-in; font paths unified to `../fonts/`.
