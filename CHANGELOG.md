# Changelog

All notable changes to this project. Dates are in 2026; the format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-11-17

Competition release (Version 1), as submitted to the 2nd LogisticSolver 2026.

### Added
- `competition/demo.py`: plans the report's synthetic 26-stop job with the real planner code, checks every rule and prints the plan sheet; no company data needed.
- Public repository: README with figures and results, this changelog, a requirements file for the planner, `competition/package.json` for the slide build, and the licence for the Noto Sans KR font.

### Changed
- Report, summary table: the 0.06 % benchmark gap is credited to the optimizer with the 15-nearest list, the setting it was measured with.
- Report, section 7.2: clearer reason why the GNN is not run on the benchmark (it is trained on the company's road km and volumes in m³).
- Report, section 4.6: the reference to Listing 3 now points at the checks the listing shows.
- Slides, slide 14: the yearly figures are "the 4-month totals × 365 / 123".
- Slide build creates its output folder when it is missing.

## [0.5.0] - 2026-11-16

### Added
- Korean edition of the report (`report_ko.md`, Korean figures in `competition/figs/ko/`) and of the slides (`node competition/make_deck.js ko`).

### Changed
- New title: "AI-Based Clustering and Automatic Dispatching for Bulky Product Delivery".
- Slides are fully editable: the rules, the GNN flow and the worked example are native shapes and text; the bar charts are native charts.

## [0.4.0] - 2026-11-13

Report submitted.

### Added
- Accuracy on a public benchmark (`competition/benchmark.py`, CVRPLIB set P): optimal on 4 of 5 instances, 0.06 % average gap.
- Google OR-Tools baseline (`competition/ortools_baseline.py`): 2,264 trucks.
- The optimizer with an 8-nearest list as the fair test of what the GNN adds: 1,941 trucks against 1,933 with the GNN.
- Hire-cost estimate from public broker list prices: about 14.5 % less than the real dispatch.

### Changed
- Report shortened to 19 pages without repeated content; every method step has a short "why".

## [0.3.0] - 2026-11-12

### Added
- Competition report (`competition/report.md`, PDF via `build.py`) and a 15-slide deck (`make_deck.js`), with figures and a synthetic sample job.

## [0.2.0] - 2026-11-11

### Changed
- The depot is placed at the company's real site in Changwon; every result was recomputed from it (road km about 0.9 % lower; no rule involves the depot, so it cannot change truck counts).

## [0.1.0] - 2026-11-10

### Added
- The planner (`cluster/ryry.py`): company rules, road km from a local OSRM server, baselines (real dispatch, k-means, agglomerative clustering, a greedy plan), the exact two-stage optimizer, and the GNN short list evaluated out of fold.
- Tests on toy jobs (`cluster/test_exact.py`, `cluster/test_ryry.py`).
