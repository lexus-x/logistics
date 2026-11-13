"""Exact answers for the packing questions the heuristic left undecided (cluster/results/pack_todo.json -> pack_cache.json).
  UV_CACHE_DIR=.uv-cache .bin/uv run --no-project --with ortools python -I cluster/pack_exact.py [seconds per question]
CP-SAT: each box gets a position and one of two orientations, no two boxes overlap. A question that hits the time limit
stays undecided (it is not written to the cache)."""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

from ortools.sat.python import cp_model

OUT = Path(__file__).resolve().parents[1] / "cluster/results"
S = 10  # millimetres: box sizes are given to 1 mm


def solve(task):
    k, (W, L, gap, boxes), limit = task
    m = cp_model.CpModel()
    W, L = round((W + gap) * S), round((L + gap) * S)
    xs, ys = [], []
    for i, (w, d) in enumerate(boxes):
        w, d = round((w + gap) * S), round((d + gap) * S)
        turn = m.NewBoolVar(f"t{i}")
        dx, dy = m.NewIntVar(min(w, d), max(w, d), f"dx{i}"), m.NewIntVar(min(w, d), max(w, d), f"dy{i}")
        m.Add(dx == w).OnlyEnforceIf(turn.Not())
        m.Add(dy == d).OnlyEnforceIf(turn.Not())
        m.Add(dx == d).OnlyEnforceIf(turn)
        m.Add(dy == w).OnlyEnforceIf(turn)
        x, y = m.NewIntVar(0, W, f"x{i}"), m.NewIntVar(0, L, f"y{i}")
        ex, ey = m.NewIntVar(0, W, f"ex{i}"), m.NewIntVar(0, L, f"ey{i}")
        xs.append(m.NewIntervalVar(x, dx, ex, f"ix{i}"))
        ys.append(m.NewIntervalVar(y, dy, ey, f"iy{i}"))
    m.AddNoOverlap2D(xs, ys)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = limit
    s.parameters.num_workers = 1
    r = s.Solve(m)
    return k, True if r in (cp_model.OPTIMAL, cp_model.FEASIBLE) else False if r == cp_model.INFEASIBLE else None


if __name__ == "__main__":
    limit = float(sys.argv[1]) if len(sys.argv) > 1 else 20
    todo = json.loads((OUT / "pack_todo.json").read_text())
    cache = json.loads(c.read_text()) if (c := OUT / "pack_cache.json").exists() else {}
    tasks = [(k, v, limit) for k, v in todo.items() if k not in cache]
    assert solve(("a", (160, 275, 0, [(80, 137.5)] * 4), 5))[1] is True and solve(("b", (160, 275, 0, [(100, 100)] * 3), 5))[1] is False
    print(f"{len(tasks)} questions, {limit:g} s each", flush=True)
    n = dict(fit=0, no=0, timeout=0)
    with Pool(7) as pool:
        for k, r in pool.imap_unordered(solve, tasks, chunksize=4):
            n["fit" if r else "no" if r is False else "timeout"] += 1
            if r is not None:
                cache[k] = r
    (OUT / "pack_cache.json").write_text(json.dumps(cache))
    print(n)
