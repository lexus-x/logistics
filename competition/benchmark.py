"""Accuracy on a public benchmark: the Version 1 optimizer on CVRPLIB (Augerat et al. 1995, set P).
  .venv/bin/python -I competition/benchmark.py [k]     # k nearest partners, default 15 (8 = the shipped list size)
Instances: the five set-P instances whose proven-optimal routes visit at most 5 customers, i.e. the ones that fit
the company's 5-address rule. Same method as on the company data: candidate loads from each customer's 15 nearest
neighbours (1 to 5 customers, capacity respected), best visiting order of each load, then set partitioning
(stage A fewest vehicles, stage B shortest distance, 60 s each). Distances follow CVRPLIB: rounded Euclidean,
round trips from the depot. Writes competition/benchmark/results.json (k = 15) or results_k<k>.json."""
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_array

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "cluster"))
from exact import knn_columns  # noqa: E402  (K = 5 customers per load)

NAMES = ["P-n16-k8", "P-n22-k8", "P-n23-k8", "P-n55-k15", "P-n60-k15"]


def read(name):
    lines = (HERE / "benchmark/P" / f"{name}.vrp").read_text().split("\n")
    head = {k.strip(): v.strip() for k, v in (ln.split(":", 1) for ln in lines if ":" in ln)}
    n, Q = int(head["DIMENSION"]), int(head["CAPACITY"])
    i = lines.index(next(ln for ln in lines if ln.startswith("NODE_COORD_SECTION")))
    xy = np.array([[float(t) for t in lines[i + 1 + k].split()[1:3]] for k in range(n)])
    j = lines.index(next(ln for ln in lines if ln.startswith("DEMAND_SECTION")))
    q = np.array([int(lines[j + 1 + k].split()[1]) for k in range(n)])
    D = np.rint(np.linalg.norm(xy[:, None] - xy[None], axis=2))  # CVRPLIB EUC_2D: rounded to the nearest integer
    sol = (HERE / "benchmark/P" / f"{name}.sol").read_text().split("\n")
    routes = [[int(t) for t in ln.split(":")[1].split()] for ln in sol if ln.startswith("Route")]
    opt = int(next(ln for ln in sol if ln.startswith("Cost")).split()[1])
    return xy, q, Q, D, routes, opt


def tour(D, c):
    """Shortest round trip depot -> customers c (1-based node ids) -> depot, over every visiting order."""
    best = np.inf
    for p in itertools.permutations(c):
        best = min(best, D[0, p[0]] + sum(D[a, b] for a, b in zip(p, p[1:])) + D[p[-1], 0])
    return best


def run(name, k=15):
    xy, q, Q, D, routes, opt = read(name)
    assert sum(tour(D, r) for r in routes) == opt, "distance convention differs from CVRPLIB"
    t0 = time.time()
    cols = knn_columns(xy[1:], k)  # customers only; indices 0..n-2
    loads = [tuple(int(i) + 1 for i in c) for a in cols.values() for c in a if q[c + 1].sum() <= Q]
    cost = np.array([tour(D, c) for c in loads])
    m, n = len(loads), len(xy) - 1
    A = csc_array((np.ones(sum(map(len, loads))), (np.concatenate([np.array(c) - 1 for c in loads]),
                   np.repeat(np.arange(m), [len(c) for c in loads]))), shape=(n, m))
    cover = LinearConstraint(A, 1, 1)
    a = milp(np.ones(m), integrality=np.ones(m), bounds=Bounds(0, 1), constraints=[cover], options={"time_limit": 60})
    k = int(round(a.x.sum()))
    b = milp(cost, integrality=np.ones(m), bounds=Bounds(0, 1),
             constraints=[cover, LinearConstraint(np.ones((1, m)), k, k)], options={"time_limit": 60})
    plan = [loads[j] for j in np.flatnonzero(b.x > 0.5)]
    ours = int(sum(tour(D, c) for c in plan))
    # self-check: every customer exactly once, capacity respected
    assert sorted(i for c in plan for i in c) == list(range(1, n + 1)) and all(q[list(c)].sum() <= Q for c in plan)
    return dict(name=name, customers=n, capacity=Q, vehicles_opt=len(routes), optimum=opt, candidates=m,
                vehicles=len(plan), cost=ours, gap=round(100 * (ours - opt) / opt, 2), s=round(time.time() - t0, 1),
                proven=bool(a.status == 0 and b.status == 0))


if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    out = [run(nm, k) for nm in NAMES]
    for r in out:
        print(r)
    (HERE / ("benchmark/results.json" if k == 15 else f"benchmark/results_k{k}.json")).write_text(json.dumps(out, indent=1))
