"""Standard-tool baseline: Google OR-Tools routing on the 97 real jobs and on the 5 CVRPLIB set-P instances.
  UV_CACHE_DIR=.uv-cache .bin/uv run --no-project --with ortools --with numpy --with scipy python -I competition/ortools_baseline.py
Real jobs, same treatment as the k-means and agglomerative baselines: small-truck stops only (big stops ride alone and
are added by score()), same road matrices, same rule check and scoring. Model: open routes from the depot (the way back
costs 0, trucks are hired one way), arc cost = road metres, a large fixed cost per truck (fewest trucks first, then km),
volume capacity (10 trucks at the 1.4-ton limit, lone over-1-ton stops on a truck of their own, the rest at the 1-ton
limit), at most 5 stops per truck, no two stops more than 100 km apart on one truck. PATH_CHEAPEST_ARC + guided local
search, 30 s per job. OR-Tools cannot express the 50 km radius rule, so a truck that breaks it is split by the rule-based
greedy, as k-means groups are. -> cluster/results/ryry_ortools.jsonl, competition/benchmark/ortools.json"""
import json
import math
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "cluster"))
sys.path.insert(0, str(HERE))
from ryry import C, C14, K, MAX14, R, finish, greedy2, load, matrices, pool_run, radius, rows, split  # noqa: E402

LIMIT_S, BIG = 30, 10**9  # BIG: fixed cost per truck, far above any job's total metres
U = 10_000  # volume unit 0.0001 m3; demands rounded up, capacities down, so the model never overfills a truck


def solve(D, demand, caps, stops, forbid=(), open_routes=True):
    """OR-Tools routing. D: (n+1)x(n+1) costs, node 0 = depot. caps / stops: per vehicle. Returns routes of node ids >= 1."""
    n = len(D)
    man = pywrapcp.RoutingIndexManager(n, len(caps), 0)
    rt = pywrapcp.RoutingModel(man)
    Di = np.rint(D).astype(np.int64)
    if open_routes:
        Di[:, 0] = 0
    cost = rt.RegisterTransitCallback(lambda a, b: int(Di[man.IndexToNode(a), man.IndexToNode(b)]))
    rt.SetArcCostEvaluatorOfAllVehicles(cost)
    rt.SetFixedCostOfAllVehicles(BIG)
    dem = rt.RegisterUnaryTransitCallback(lambda a: int(demand[man.IndexToNode(a)]))
    rt.AddDimensionWithVehicleCapacity(dem, 0, [int(c) for c in caps], True, "volume")
    one = rt.RegisterUnaryTransitCallback(lambda a: int(man.IndexToNode(a) != 0))
    rt.AddDimensionWithVehicleCapacity(one, 0, [int(s) for s in stops], True, "count")
    for a, b in forbid:
        rt.NextVar(man.NodeToIndex(a)).RemoveValue(man.NodeToIndex(b))
    p = pywrapcp.DefaultRoutingSearchParameters()
    p.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    p.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    p.time_limit.seconds = LIMIT_S
    sol = rt.SolveWithParameters(p)
    assert sol is not None, "OR-Tools found no solution"
    out = []
    for k in range(len(caps)):
        i, r = sol.Value(rt.NextVar(rt.Start(k))), []
        while not rt.IsEnd(i):
            r.append(man.IndexToNode(i))
            i = sol.Value(rt.NextVar(i))
        if r:
            out.append(r)
    return out


def run_job(task):
    jid, j, M = task
    s, xy, v, Ds, Ts = split(j, M)
    row = dict(job=jid)
    if len(s) < 2:
        return finish(row, j, M, s, Ds, Ts, {"ortools": [[i] for i in range(len(s))]})
    t = time.time()
    lone = int((v > C + 1e-9).sum())  # such a stop can only ride alone unless on one of the 10 1.4-ton trucks
    caps = [math.floor(C14 * U)] * (MAX14 + lone) + [math.floor(C * U)] * (len(s) - lone)
    stops = [K] * MAX14 + [1] * lone + [K] * (len(s) - lone)
    far = np.linalg.norm(xy[:, None] - xy[None], axis=2) > 2 * R  # two stops this far apart can never share a truck
    forbid = [(a + 1, b + 1) for a, b in zip(*np.nonzero(far))]
    routes = solve(Ds * 1000, np.r_[0, np.ceil(v * U)], caps, stops, forbid)
    kept = [[i - 1 for i in r] for r in routes if radius(xy, np.array([[i - 1 for i in r]]))[0] <= R + 1e-9]
    broken = [[i - 1 for i in r] for r in routes if radius(xy, np.array([[i - 1 for i in r]]))[0] > R + 1e-9]
    used = [sum(len(c) > 1 and v[c].sum() > C + 1e-9 for c in kept)]  # 1.4-ton loads so far, shared with the repair
    for c in broken:  # same repair as k-means: the rule-based greedy re-splits the group, biggest stop first
        m = np.array(c)
        kept += [m[g].tolist() for g in greedy2(xy[m], v[m], order=np.argsort(-v[m]), used=used)]
    row["ortools_s"], row["ortools_split"] = round(time.time() - t, 1), len(broken)
    return finish(row, j, M, s, Ds, Ts, {"ortools": kept})  # finish() -> score() runs the rule check


def bench():
    from benchmark import NAMES, read, tour
    out = []
    for name in NAMES:
        xy, q, Q, D, routes, opt = read(name)
        n = len(xy) - 1
        t = time.time()
        plan = solve(D, q, [Q] * n, [5] * n, open_routes=False)
        assert sorted(i for r in plan for i in r) == list(range(1, n + 1)) and all(q[r].sum() <= Q for r in plan)
        cost = int(sum(tour(D, r) for r in plan))  # each route in its best order, as for our optimizer
        out.append(dict(name=name, optimum=opt, vehicles_opt=len(routes), vehicles=len(plan), cost=cost,
                        gap=round(100 * (cost - opt) / opt, 2), s=round(time.time() - t, 1)))
        print(out[-1], flush=True)
    (HERE / "benchmark/ortools.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    jobs, Ms = load(), matrices()
    pool_run(run_job, [(jid, j, Ms[jid]) for jid, j in jobs.items()], "ortools")
    o, g = rows("ortools"), rows("gnn")
    assert len(o) == len(jobs) and all(sorted(i for c in r["plans"]["ortools"] for i in c) ==
                                       [i for i in range(len(jobs[jid]["v"])) if jobs[jid]["v"][i] <= C14 + 1e-9]
                                       for jid, r in o.items()), "every small stop exactly once"
    tot = {f: round(sum(r["ortools"][f] for r in o.values())) for f in ("trucks", "km", "hours")}
    print("OR-Tools:", tot, "median s", statistics.median(r["ortools_s"] for r in o.values() if "ortools_s" in r),
          "jobs split", sum(r.get("ortools_split", 0) > 0 for r in o.values()),
          "fewer / more trucks than GNN + optimizer:", sum(o[j]["ortools"]["trucks"] < g[j]["gnn_opt"]["trucks"] for j in o),
          sum(o[j]["ortools"]["trucks"] > g[j]["gnn_opt"]["trucks"] for j in o))
    bench()
