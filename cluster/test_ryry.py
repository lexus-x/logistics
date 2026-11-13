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

# the proven minimum (column generation) is never above the true optimum, found by trying every group of 1-5 stops
from exact import all_columns  # noqa: E402
from ryry import lb_valid as lbv  # noqa: E402
from ryry_cg import cg_bound  # noqa: E402
for seed in range(6):
    r = np.random.default_rng(seed)
    xt = np.r_[r.normal(0, 25, (5, 2)), r.normal([70, 0], 25, (5, 2)), r.normal([0, 90], 30, (4, 2))]
    vt = r.uniform(0.4, 2.2, 14)
    best_t = len(optimize(xt, vt, mat(xt), all_columns(14), [greedy2(xt, vt)])[0])
    bound, info = cg_bound(xt, vt, {})
    assert lbv(vt) <= bound <= best_t, (seed, lbv(vt), bound, best_t, info)

# the rule switches reach every module (price-of-rules study); a fresh interpreter, as the worker processes are
import os  # noqa: E402
import subprocess  # noqa: E402
out = subprocess.run([sys.executable, "-I", "-c", "import sys; sys.path.insert(0, sys.argv[1]); import exact, ryry, ryry_cg; "
                      "print(ryry.K, exact.K, ryry_cg.K, max(ryry.PERMS), ryry.R, ryry.MAX14, round(ryry.C14 / ryry.CAP['1.4t'], 2), "
                      "round(ryry.C / (1.6 * 2.75 * 1.6), 2))", str(Path(__file__).parent)], capture_output=True, text=True,
                     env={**os.environ, "RULE_K": "6", "RULE_R": "75", "RULE_FILL": "0.7", "RULE_MAX14": "3"})
assert out.stdout.split() == ["6", "6", "6", "6", "75.0", "3", "1.0", "0.7"], (out.stdout, out.stderr[-300:])

# score counts big stops' trucks and rejects a plan that breaks a rule
j = dict(xy=np.r_[xy, [[0, 0]]], v=np.r_[v, CAP["11t-9.7m"] * 1.5])
M = (np.pad(Ds, ((0, 1), (0, 1)), constant_values=50.0),) * 2
assert score(j, M, np.arange(30), Ds, Ds, plans["opt"])["trucks"] == len(plans["opt"]) + 2
try:
    score(j, M, np.arange(30), Ds, Ds, [list(range(30))])
except AssertionError:
    # every valid load is listed, and prove() finds the true optimum from a poor plan and confirms it from the optimum
    from exact import all_columns, every_load, keep
    from ryry import solve2
    from ryry_cg import prove
    for seed in range(6):
        r6 = np.random.default_rng(seed)
        n6 = int(r6.integers(7, 12))
        x6, v6 = r6.uniform(0, 120, (n6, 2)), r6.uniform(0.3, 3.2, n6)
        D6 = np.zeros((n6 + 1, n6 + 1))
        D6[1:, 1:], D6[0, 1:] = np.linalg.norm(x6[:, None] - x6[None], axis=2), np.linalg.norm(x6 - 60, axis=1)
        full, brute = every_load(x6, v6, C14, R), all_columns(n6)
        assert all({tuple(q) for q in keep(x6, v6, C14, R, full[k])[0]} == {tuple(q) for q in keep(x6, v6, C14, R, brute[k])[0]} for k in full), seed
        best6 = solve2(x6, v6, D6, brute)[0]
        p6, f6, done6, _ = prove(x6, v6, D6, [[i] for i in range(n6)])
        assert done6 and len(p6) == len(best6) and f6 <= len(best6) and prove(x6, v6, D6, best6)[2], seed
        fit6 = lambda a: (a.sum(1) % 3 > 0, a.sum(1) % 2 == 0)  # noqa: E731  a toy physical check on multi-stop loads
        bestf = solve2(x6, v6, D6, brute, fit=fit6)[0]
        pf, _, donef, _ = prove(x6, v6, D6, [[i] for i in range(n6)], fit=fit6)
        assert donef and len(pf) == len(bestf) >= len(best6) and all(sum(c) % 3 for c in pf if len(c) > 1), seed
    print("ryry ok")
else:
    raise SystemExit("score accepted a 30-stop cluster")
