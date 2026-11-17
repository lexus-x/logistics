# AI-Based Clustering and Automatic Dispatching for Bulky Product Delivery

**Team ANALOG**, Changwon National University. Entry to the 2nd LogisticSolver 2026 (Smart Logistics Problem-Solving Competition). This repository holds Version 1, as submitted.

A home-appliance maker ships bulky goods from one depot in Changwon to customers all over South Korea, with trucks hired per trip. Today a dispatcher groups the addresses into trucks by hand. Our planner does it in two steps: a graph neural network (GNN) keeps each stop's 8 most likely truck partners, and an exact optimizer picks the plan with the fewest trucks, then the fewest road km. Every plan keeps the company's rules: at most 5 addresses per truck, at most 60 % of the box volume, every stop within 50 km of the load's centre, and at most ten 1.4-ton trucks per job.

| | English | 한국어 |
|---|---|---|
| Report | [PDF](competition/build/ANALOG_LogisticSolver2026_Report.pdf) | [PDF](competition/build/ANALOG_LogisticSolver2026_Report_KO.pdf) |
| Slides | [PowerPoint](competition/build/ANALOG_LogisticSolver2026_Slides.pptx) | [PowerPoint](competition/build/ANALOG_LogisticSolver2026_Slides_KO.pptx) |

## Results

97 real dispatch jobs (6,395 stops, April to August 2026), the same roads and rules for every plan:

| | Real dispatch | GNN + optimizer | Change |
|---|--:|--:|--:|
| Trucks | 2,517 | **1,933** | **−23.2 %** |
| Road km | 655,444 | **516,628** | **−21.2 %** |
| Rule breaks | | **0** | |
| Planning time per job | by hand | **6.8 s** | |

On the public CVRPLIB benchmark (set P) the optimizer is 0.06 % from the proven optimum on average.

## Try it

No company data needed:

```bash
git clone https://github.com/lexus-x/logistics.git && cd logistics
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -I competition/demo.py        # the report's worked example: 26 stops, 6 trucks
.venv/bin/python -I cluster/test_exact.py      # tests
.venv/bin/python -I cluster/test_ryry.py
.venv/bin/python -I competition/benchmark.py   # CVRPLIB set P, about 30 s
```

## What is where

| Path | Contents |
|---|---|
| `cluster/` | The planner (`ryry.py`), candidate loads and the rule check (`exact.py`), saved per-job results |
| `competition/` | Report and slide sources, the demo and the benchmark; `build/` holds the PDFs and decks |

The company's records are not in this repository: saved results hold job IDs, stop indices and numbers only, and maps show unlabeled dots at national scale. Method, data handling and limitations are in the report.

Fonts are under the SIL Open Font License 1.1 (`competition/fonts/`); icons are Tabler Icons, MIT (`competition/figs/icons/`).
