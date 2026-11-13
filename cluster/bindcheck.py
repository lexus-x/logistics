"""The gap map: where do the 4 rules bind on Amazon LMRRC? python -I cluster/bindcheck.py data/almrrc
A 'day' = the sampled routes of one station on one date (median 2 routes, not a full depot-day).
Map: radius R as a multiple of d4 (median distance to the 4th-nearest stop) x volume pressure p = (sumV/C)/(n/5).
Cell = median % by which a greedy that keeps all 4 constraints exceeds LB0 = max(ceil(n/5), ceil(sumV/C))."""
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
from exact import MULT, PRESS, check, d4, floor_, greedy, load_days, scale  # noqa: E402

gaps, d4s, ns, capped = defaultdict(list), [], [], []
for _, xy, v0, C in load_days(Path(sys.argv[1])):
    d4s.append(d4(xy))
    ns.append(len(xy))
    for p in PRESS:
        v = scale(v0, C, p)
        if p != "raw":
            capped.append(np.mean(v0 * (p * C / 5) / np.median(v0) > C))
        for m in MULT:
            R = 50.0 if m == "50km" else m * d4s[-1]
            g = greedy(xy, v, C, R)
            check(xy, v, C, R, g)
            gaps[p, m].append(len(g) / floor_(len(xy), v, C) - 1)

print(f"{len(d4s)} station-days, {np.median(ns):.0f} stops median; d4 median {np.median(d4s):.2f} km "
      f"(p10 {np.percentile(d4s, 10):.2f}, p90 {np.percentile(d4s, 90):.2f}); "
      f"bulky stops capped at C: {100 * np.mean(capped):.1f}%")
print("median % over LB0   " + "  ".join(f"R={m}{'xd4' if m != '50km' else ''}".rjust(9) for m in MULT))
for p in PRESS:
    print(f"pressure {p!s:>4}      " + "  ".join(f"{100 * np.median(gaps[p, m]):8.1f}%" for m in MULT))
