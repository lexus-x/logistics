"""Plan the synthetic example job of the report (Figure 5, Table 13) with the real planner code; no company data needed.
  python -I competition/demo.py
Distances are 1.3 x the straight line, as in the report's example; real jobs use road km from OSRM (cluster/osrm.sh)."""
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "cluster"))
from exact import check, knn_columns  # noqa: E402
from ryry import C, C14, R, greedy2, optimize, route_cost  # noqa: E402

job = json.loads((HERE / "synthetic_job.json").read_text())
names = [s["stop"] for s in job["stops"]]
xy = np.array([[s["x_km"], s["y_km"]] for s in job["stops"]])
v = np.array([s["volume_m3"] for s in job["stops"]])
p = np.r_[[job["depot"]], xy]
D = 1.3 * np.linalg.norm(p[:, None] - p[None], axis=2)  # row and column 0 = the depot

# candidate loads from each stop's 8 nearest partners, a greedy plan as the safety net, then the exact selection
plan, info = optimize(xy, v, D, knn_columns(xy, 8), [greedy2(xy, v)])
check(xy, v, C14, R, [np.asarray(c) for c in plan])  # every stop once; <= 5 stops, <= 60 % volume, 50 km radius per truck
floor = math.ceil(v.sum() / C14 - 1e-9)  # no truck that may carry several stops holds more than C14
assert len(plan) == floor, (len(plan), floor)

routes = [(o[0], k[0]) for k, o in (route_cost(D, np.array([c])) for c in plan)]
routes.sort(key=lambda r: D[0, r[0][0] + 1])  # nearest first stop first
print(f"{len(xy)} stops, {info['cols']:,} candidate loads, solved in {info['t']:.1f} s\n")
print("| Truck | Stops in visiting order | Volume (m³) | Truck size | Share of the 60 % limit | km |")
print("|--:|---|--:|---|--:|--:|")
for t, (o, km) in enumerate(routes, 1):
    vol = v[o].sum()
    cap, size = (C, "1-ton") if vol <= C + 1e-9 else (C14, "1.4-ton")
    print(f"| {t} | {' → '.join(names[i] for i in o)} | {vol:.2f} | {size} | {100 * vol / cap:.0f} % | {km:,.0f} |")
print(f"\n{len(plan)} trucks, {sum(k for _, k in routes):,.0f} km. Every rule met; {v.sum():.1f} m³ needs at least "
      f"{floor} trucks of {C14:.2f} m³, so no plan uses fewer.")
