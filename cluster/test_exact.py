"""python cluster/test_exact.py: the rules check, column builders, greedy, exact and shortlist solves on toy layouts."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from exact import all_columns, check, floor_, greedy, knn_columns, radius, solve  # noqa: E402

rng = np.random.default_rng(0)
C = 10.0
assert abs(radius(np.array([[0.0, 0], [2, 0]]), np.array([[0, 1]]))[0] - 1) < 1e-12, "radius is from the centroid"
assert sum(len(c) for c in all_columns(6).values()) == 62, "all 1..5-subsets of 6 stops"

# two tight groups of 5, 100 km apart: 2 clusters by every method
xy = np.r_[rng.normal(0, 0.1, (5, 2)), rng.normal(100, 0.1, (5, 2))]
for cols in (all_columns(10), knn_columns(xy, 4)):
    assert len(solve(xy, np.ones(10), C, 1.0, cols)[0]) == 2
assert len(greedy(xy, np.ones(10), C, 1.0)) == 2

# 4 stops of 0.6 C cannot share a truck: the optimum is 4 while the floor says 3
xy4, v4 = rng.normal(0, 0.1, (4, 2)), np.full(4, 6.0)
assert len(solve(xy4, v4, C, 1.0, all_columns(4))[0]) == 4 and floor_(4, v4, C) == 3

# exact <= shortlist <= greedy, even with k too small for the shortlist to help on its own
xy12, v12 = rng.uniform(0, 3, (12, 2)), np.ones(12)
g = greedy(xy12, v12, C, 1.5)
short = solve(xy12, v12, C, 1.5, knn_columns(xy12, 1), extra=g)[0]
ex = solve(xy12, v12, C, 1.5, all_columns(12))[0]
assert len(ex) <= len(short) <= len(g), (len(ex), len(short), len(g))

# stops at the same spot never make a cluster with a repeated stop
for c in knn_columns(np.array([[0.0, 0], [0, 0], [1, 0]]), 2).values():
    assert (np.diff(c, axis=1) != 0).all()

# check() rejects a stop used twice and a cluster that is too wide
for bad in ([[0, 1], [1, 2, 3]], [[0, 1, 2, 3]]):
    try:
        check(xy4, np.ones(4), C, 0.001, [np.array(c) for c in bad])
    except AssertionError:
        continue
    raise SystemExit(f"check accepted {bad}")
print("exact ok")
