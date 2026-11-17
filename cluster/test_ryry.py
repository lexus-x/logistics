"""python -I cluster/test_ryry.py: routing, truck choice, bounds, the 1.4-ton limit and the GNN decoders on toy jobs."""
import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from exact import check, knn_columns  # noqa: E402
from ryry import (CAP, C, C14, MAX14, R, big_trucks, features, gnn_columns, gnn_greedy, greedy2, kmeans,  # noqa: E402
                  labels, lb_valid, optimize, predict, route_cost, score, train)

rng = np.random.default_rng(0)


def mat(xy):
    """Straight-line km with the depot at the origin as row/column 0."""
    p = np.r_[[[0.0, 0.0]], xy]
    return np.linalg.norm(p[:, None] - p[None], axis=2)


# route: depot plus 4 stops on a line at 10, 20, 30, 40 km; one-way, so the best order is outward (40 km)
km, order = route_cost(mat(np.c_[[10.0, 20, 30, 40], np.zeros(4)]), np.array([[3, 0, 2, 1]]))
assert km[0] == 40 and order[0].tolist() == [0, 1, 2, 3], (km, order)
Dr = rng.uniform(1, 9, (6, 6))  # asymmetric: still the brute-force best
best = min(Dr[0, p[0] + 1] + sum(Dr[p[i] + 1, p[i + 1] + 1] for i in range(4)) for p in itertools.permutations(range(5)))
assert abs(route_cost(Dr, np.array([[0, 1, 2, 3, 4]]))[0][0] - best) < 1e-9

# trucks and bounds
assert big_trucks(C14 * 1.01) == ["2.5t"] and big_trucks(CAP["11t-9.7m"] * 2.5) == ["11t-9.7m"] * 3
assert labels([[0, 1], [2], [3]], np.array([2.5, 2.5, C * 1.05, 1.0])) == ["1.4t", "1.4t", "1t"]
assert labels([[i] for i in range(12)], np.full(12, C * 1.05)).count("2.5t") == 2, "lone stops past 10 x 1.4-ton"

# the 1.4-ton limit binds: 33 stops of 1.5 m3 in one spot fit 2 per 1-ton or 3 per 1.4-ton.
# Best = 10 x 1.4-ton (30 stops) + 2 x 1-ton (3 stops) = 12 trucks, against 11 with unlimited 1.4-ton
xy33, v33 = rng.normal(0, 0.5, (33, 2)), np.full(33, 1.5)
opt33, _ = optimize(xy33, v33, mat(xy33), knn_columns(xy33, 15), [greedy2(xy33, v33)])
assert len(opt33) == 12 and labels(opt33, v33).count("1.4t") <= MAX14, (len(opt33), labels(opt33, v33))
assert lb_valid(v33) <= 12
for plan in (greedy2(xy33, v33), kmeans(xy33, v33)):
    assert labels(plan, v33).count("1.4t") <= MAX14 and len(plan) >= 12

# a toy job: 30 small stops in 3 far-apart towns; every method keeps the rules, the optimizer at least as good
xy = np.r_[rng.normal(0, 3, (10, 2)), rng.normal(200, 3, (10, 2)), rng.normal([0, 300], 3, (10, 2))]
v = rng.uniform(0.3, 1.5, 30)
Ds = mat(xy)
g = features(xy, v, Ds)
g["y"] = (np.abs(g["pairs"][:, 0] - g["pairs"][:, 1]) == 1).astype(np.float32)  # any labels: only the plumbing is tested
model, _ = train([g], epochs=5)
p = predict(model, g)
assert p.shape == (len(g["pairs"]),) and ((0 <= p) & (p <= 1)).all()
plans = {"gnn": gnn_greedy(xy, v, g["pairs"], p), "kmeans": kmeans(xy, v)}
plans["opt"], _ = optimize(xy, v, Ds, gnn_columns(30, g["pairs"], p), [plans["gnn"], plans["kmeans"]])
for name, cl in plans.items():
    check(xy, v, C14, R, [np.asarray(c) for c in cl])
    labels(cl, v)
assert len(plans["opt"]) <= min(len(plans["gnn"]), len(plans["kmeans"]))
assert all(any(len(c) == 1 and c[0] == i for c in gnn_columns(30, g["pairs"], p)[1]) for i in range(30)), "singletons always"

# score counts big stops' trucks and rejects a plan that breaks a rule
j = dict(xy=np.r_[xy, [[0, 0]]], v=np.r_[v, CAP["11t-9.7m"] * 1.5])
M = (np.pad(Ds, ((0, 1), (0, 1)), constant_values=50.0),) * 2
assert score(j, M, np.arange(30), Ds, Ds, plans["opt"])["trucks"] == len(plans["opt"]) + 2
try:
    score(j, M, np.arange(30), Ds, Ds, [list(range(30))])
except AssertionError:
    print("ryry ok")
else:
    raise SystemExit("score accepted a 30-stop cluster")
