"""A longer search and a provable lower bound on trucks for Ryry's jobs.
  python -I cluster/ryry_cg.py one <job index>   # time one job
  python -I cluster/ryry_cg.py run               # all jobs -> cluster/results/ryry_cg.jsonl
  python -I cluster/ryry_cg.py summary
Long run: prove() lists every load a truck may carry and solves the job exactly (the true optimum, with proof).
Where a job has too many loads to list, or the solver runs out of time, it falls back to set partitioning over the GNN's
top-12 short list plus each stop's 15 nearest, 240 s, with the earlier plans as safety nets, so it is never worse than them.
Bound on those fallback jobs: the LP relaxation of the set partitioning, solved by column generation with exact pricing
over a relaxed rule set (every pair within 100 km instead of every stop within 50 km of the centre, which any real cluster
also meets), so it can only be below the true optimum. If the time cap ends column generation early, the bound is
z / (1 - min reduced cost), which is valid for any duals (Farley / Lagrangian bound)."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_array, csc_array
from scipy.spatial.distance import pdist, squareform

sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
from exact import every_load, keep, knn_columns, radius  # noqa: E402
from ryry import (C, C14, K, MAX14, OUT, R, big_trucks, features, finish, gnn_columns, greedy2, load, matrices,  # noqa: E402
                  pool_run, rows, solve2, split)

LONG, CG_CAP = 240, 90


def merge(*cs):
    out = {}
    for c in cs:
        for s, a in c.items():
            if len(a):
                out.setdefault(s, []).append(a)
    return {s: np.unique(np.concatenate(a), axis=0) for s, a in out.items()}


def lp(n, v, cols, cap=MAX14, x=False):
    """Restricted master: min trucks, each stop once, <= cap multi-stop 1.4-ton groups. Returns (z, y, mu), plus the
    relaxed answer itself when x is set."""
    sizes = np.array([len(c) for c in cols])
    A = csc_array((np.ones(sizes.sum()), (np.concatenate(cols), np.repeat(np.arange(len(cols)), sizes))), shape=(n, len(cols)))
    t14 = np.array([len(c) > 1 and v[list(c)].sum() > C + 1e-9 for c in cols], float)
    side = dict(A_ub=t14[None], b_ub=[cap]) if t14.any() else {}
    res = linprog(np.ones(len(cols)), A_eq=A, b_eq=np.ones(n), bounds=(0, None), method="highs", **side)
    assert res.status == 0, res.message
    out = (res.fun, res.eqlin.marginals, (res.ineqlin.marginals[0] if t14.any() else 0.0))
    return out + (res.x,) if x else out


def heur(v, y, mu, far):
    """Cheap pricing: from each stop, add the highest-dual compatible stops; keep every negative reduced cost prefix."""
    out = []
    for s in np.flatnonzero(y > 1e-9):
        cand = np.flatnonzero(~far[s] & (y > 1e-9))
        g, vol = [s], v[s]
        for c in cand[np.argsort(-y[cand])]:
            if len(g) == K:
                break
            if c == s or vol + v[c] > C14 + 1e-9 or far[c, g].any():
                continue
            g.append(int(c))
            vol += v[c]
            if 1 - y[g].sum() - (mu if vol > C + 1e-9 else 0) < -1e-6:
                out.append(tuple(sorted(g)))
    return out


def price_true(xy, v, y, mu, ids, D, fit=None):
    """Pricing under the real rules, for planning: from each stop, add partners by price and by price per m3 while the
    load stays within volume, radius (from the centre) and, when given, the physical check fit(stops) -> bool.
    Every load returned is one a truck may carry, and would improve the relaxed answer."""
    out, seen = [], set()
    for s in ids:
        near = ids[(D[s, ids] <= 2 * R + 1e-9) & (ids != s)]
        for order in (np.argsort(-y[near]), np.argsort(-y[near] / v[near])):
            g, vol = [int(s)], v[s]
            for c in near[order]:
                if len(g) == K:
                    break
                if vol + v[c] > C14 + 1e-9 or radius(xy, np.array([g + [int(c)]]))[0] > R + 1e-9:
                    continue
                k = tuple(sorted(g + [int(c)]))
                if fit is not None and k not in seen and not fit(k):
                    continue
                g.append(int(c))
                vol += v[c]
                if k not in seen and 1 - y[g].sum() - (mu if vol > C + 1e-9 else 0) < -1e-6:
                    out.append(k)
                seen.add(k)
    return out


def dive(xy, v, cols, fit=None, limit=60):
    """A planner that makes its own candidate loads (column-generation dive). Repeat: solve the relaxed problem over the
    stops still open, price new loads under the real rules, then fix the loads the relaxed answer uses in full (or the
    single most-used one) and close their stops. Returns (plan, every load seen): the plan is valid by itself, and the
    loads feed the exact solver."""
    n, t0 = len(xy), time.time()
    D = squareform(pdist(xy))
    cols = list(dict.fromkeys(tuple(sorted(map(int, c))) for c in cols))
    seen, open_, plan, cap = set(cols), np.ones(n, bool), [], MAX14
    t14 = lambda c: len(c) > 1 and v[list(c)].sum() > C + 1e-9  # noqa: E731
    while open_.any():
        ids = np.flatnonzero(open_)
        pos = np.full(n, -1)
        pos[ids] = np.arange(len(ids))
        sub = [c for c in cols if open_[list(c)].all()]
        while True:
            z, y, mu, x = lp(len(ids), v[ids], [tuple(pos[list(c)]) for c in sub], cap, x=True)
            if time.time() - t0 > limit:
                break
            yy = np.zeros(n)
            yy[ids] = y
            new = [c for c in price_true(xy, v, yy, mu, ids, D, fit) if c not in seen]
            if not new:
                break
            cols += new
            sub += new
            seen.update(new)
        pick = [c for c, xc in zip(sub, x) if xc > 0.999] or [sub[int(np.argmax(x))]]
        for c in pick:
            plan.append(list(c))
            open_[list(c)] = False
            cap -= t14(c)
    return plan, cols


def prove(xy, v, Ds, plan, fit=None, cap=1_500_000, limit=LONG, max_left=None):
    """The exact answer, by listing every load a truck may carry (possible when the rules leave few enough).
    1. The relaxed problem over ALL loads gives a floor z on the trucks and a price per stop.
    2. Any plan with T trucks satisfies T >= z + (the summed reduced costs of its loads), so a load whose reduced cost
       exceeds len(plan) - 1 - z cannot be part of a plan better than the one in hand.
    3. The exact solver runs over the few loads that remain: its optimum is the true optimum; if it finds nothing
       better (or nothing at all), the plan in hand is optimal.
    fit(idx) -> (ok, needs a 1.4-ton) adds the physical check, applied only to the loads that remain; the floor from
    steps 1-2 ignores it, which keeps it valid. Returns (plan, floor or None, proven optimal, info)."""
    t0, n, ub = time.time(), len(xy), len(plan)
    full = every_load(xy, v, C14, R, cap)
    if full is None:
        return plan, None, False, dict(loads=None)
    idx = {s: keep(xy, v, C14, R, a)[0] for s, a in full.items()}
    idx = {s: a for s, a in idx.items() if len(a)}
    m = sum(len(a) for a in idx.values())
    off = np.cumsum([0] + [len(a) for a in idx.values()])
    A = csc_array((np.ones(sum(a.size for a in idx.values())), (np.concatenate([a.ravel() for a in idx.values()]),
                   np.concatenate([np.repeat(np.arange(off[g], off[g + 1]), a.shape[1]) for g, a in enumerate(idx.values())]))), shape=(n, m))
    t14 = np.concatenate([(v[a].sum(1) > C + 1e-9) & (a.shape[1] > 1) for a in idx.values()]).astype(float)
    res = linprog(np.ones(m), A_eq=A, b_eq=np.ones(n), A_ub=t14[None], b_ub=[MAX14], bounds=(0, None), method="highs")
    assert res.status == 0, res.message
    z, y, mu = res.fun, res.eqlin.marginals, res.ineqlin.marginals[0]
    floor_ = math.ceil(z - 1e-6)
    info = dict(loads=int(m), z=round(float(z), 4), lp_s=round(time.time() - t0, 1))
    if floor_ >= ub:
        return plan, floor_, True, info
    room = ub - 1 - z + 1e-6
    left = {s: a[1 - y[a].sum(1) - mu * ((v[a].sum(1) > C + 1e-9) & (s > 1)) <= room] for s, a in idx.items()}
    left = {s: a for s, a in left.items() if len(a)}
    info["left"] = int(sum(len(a) for a in left.values()))
    if max_left is not None and info["left"] > max_left:  # too many loads to run the physical check on
        return plan, floor_, False, info
    cl, si = solve2(xy, v, Ds, left, limit=limit, fit=fit) if left else (None, dict(status=2))
    info.update(status=si["status"], s=round(time.time() - t0, 1))
    done = si["status"] in (0, 2)  # solved to the end, or shown that no plan exists within the loads that remain
    if cl is not None and len(cl) < ub:
        return [list(map(int, c)) for c in cl], floor_, done, info
    return plan, floor_, done, info


def run_exact(task):
    """Test of prove() on one job, starting from the long-run plan."""
    jid, j, M, long_plan = task
    s, xy, v, Ds, Ts = split(j, M)
    pos = {int(k): i for i, k in enumerate(s)}
    plan, floor_, done, info = prove(xy, v, Ds, [[pos[k] for k in c] for c in long_plan])
    return finish(dict(job=jid, proven=done, floor=None if floor_ is None else floor_ + sum(len(big_trucks(x)) for x in j["v"][j["v"] > C14 + 1e-9]), info=info),
                  j, M, s, Ds, Ts, {"exact": plan})


def exact_price(v, y, mu, far_pairs, limit=30):
    """Max y.z + mu*w over groups of 2-5 stops, load <= C14 (w = 1 when over a 1-ton), no pair over 100 km.
    Returns (column, value found, upper bound on the max value)."""
    n = len(v)
    cons = [LinearConstraint(np.r_[v, -(C14 - C)][None], -np.inf, C), LinearConstraint(np.r_[v, 0][None], -np.inf, C14),
            LinearConstraint(np.r_[np.ones(n), 0][None], 2, K)]
    if len(far_pairs):
        m = len(far_pairs)
        A = coo_array((np.ones(2 * m), (np.repeat(np.arange(m), 2), far_pairs.ravel())), shape=(m, n + 1))
        cons.append(LinearConstraint(A.tocsc(), -np.inf, 1))
    res = milp(np.r_[-y, -mu], integrality=np.ones(n + 1), bounds=Bounds(0, 1), constraints=cons, options={"time_limit": limit})
    if res.x is None:
        return None, -np.inf, -res.mip_dual_bound if res.mip_dual_bound is not None else np.inf
    ub = -res.mip_dual_bound if res.mip_dual_bound is not None and res.status != 0 else -res.fun
    return tuple(np.flatnonzero(res.x[:n] > 0.5).tolist()), -res.fun, ub


def cg_bound(xy, v, pool):
    """Lower bound on the trucks for the small stops. Returns (bound, info)."""
    n, t0 = len(xy), time.time()
    D = squareform(pdist(xy))
    far = D > 2 * R + 1e-9
    far_pairs = np.argwhere(np.triu(far, 1))
    cols = [(i,) for i in range(n)] + [tuple(map(int, c)) for a in pool.values() for c in a if len(c) > 1]
    seen = set(cols)
    it, rc_min, z = 0, -np.inf, None
    while True:
        z, y, mu = lp(n, v, cols)
        it += 1
        new = [c for c in dict.fromkeys(heur(v, y, mu, far)) if c not in seen]
        if new and time.time() - t0 < CG_CAP:
            cols += new
            seen.update(new)
            continue
        col, val, ub = exact_price(v, y, mu, far_pairs)
        rc_min = 1 - ub
        if rc_min >= -1e-6 or time.time() - t0 >= CG_CAP or col is None or col in seen:
            break
        cols.append(col)
        seen.add(col)
    lbz = z / (1 - min(0.0, rc_min))
    return math.ceil(lbz - 1e-6), dict(z=round(z, 4), rc_min=round(float(rc_min), 5), iters=it, cols=len(cols),
                                       converged=bool(rc_min >= -1e-6), s=round(time.time() - t0, 1))


def run_job(task):
    jid, j, M, p, nets_job = task
    s, xy, v, Ds, Ts = split(j, M)
    n_big = sum(len(big_trucks(x)) for x in j["v"][j["v"] > C14 + 1e-9])
    row = dict(job=jid)
    if len(s) < 2:
        row.update(bound=n_big + len(s), cg={})
        return finish(row, j, M, s, Ds, Ts, {"long": [[i] for i in range(len(s))]})
    pos = {int(k): i for i, k in enumerate(s)}
    nets = [[[pos[k] for k in c] for c in plan] for plan in nets_job] + [greedy2(xy, v, order=np.argsort(-v))]
    pairs = features(xy, v, Ds)["pairs"]
    pool = merge(gnn_columns(len(xy), pairs, p, top=12), knn_columns(xy, 15))
    t = time.time()
    best = min(nets, key=len)
    plan, floor_, proven, pinfo = prove(xy, v, Ds, best)  # the true optimum, where every load can be listed
    if proven:  # the truck count is settled: only the road km are left to choose, over the usual candidates
        cl, info = solve2(xy, v, Ds, pool, extra=[c for n in nets for c in n] + plan, limit=LONG, k=len(plan))
        cl, info, b, cg = cl or plan, dict(info, exact=True, prove=pinfo), len(plan), dict(exact=True, converged=True)
    else:
        cl, info = solve2(xy, v, Ds, pool, extra=[c for n in nets for c in n] + plan, limit=LONG)
        if cl is None or len(cl) > len(plan):
            cl, info["fallback"] = plan, True
        b, cg = cg_bound(xy, v, {k: keep(xy, v, C14, R, a)[0] for k, a in pool.items()})
        b = max(b, floor_ or 0)
    row.update(long_info=info, long_s=round(time.time() - t, 1))
    row.update(bound=n_big + b, cg=cg)
    return finish(row, j, M, s, Ds, Ts, {"long": [list(map(int, c)) for c in cl]})


def run_pb(task):
    """Test of the dive on one job: the dive's own plan, then the exact solver over the old candidates plus the dive's."""
    jid, j, M, p, nets_job = task
    s, xy, v, Ds, Ts = split(j, M)
    pos = {int(k): i for i, k in enumerate(s)}
    nets = [[[pos[k] for k in c] for c in plan] for plan in nets_job]
    pool = merge(gnn_columns(len(xy), features(xy, v, Ds)["pairs"], p, top=12), knn_columns(xy, 15))
    feas = [tuple(c) for a in pool.values() for c in keep(xy, v, C14, R, a)[0]]
    t = time.time()
    plan, cols = dive(xy, v, feas)
    td = time.time() - t
    cl, info = solve2(xy, v, Ds, pool, extra=[c for n in nets for c in n] + plan + [list(c) for c in cols[len(feas):]], limit=120)
    best = min(nets + [plan], key=len)
    if cl is None or len(cl) > len(best):
        cl, info["fallback"] = best, True
    row = dict(job=jid, dive_trucks=len(plan), new_cols=len(cols) - len(feas), dive_s=round(td, 1), info=info, s=round(time.time() - t, 1))
    return finish(row, j, M, s, Ds, Ts, {"dive": plan, "pb": [list(map(int, c)) for c in cl]})


def tasks():
    jobs, Ms, base, gnn = load(), matrices(), rows("base"), rows("gnn")
    z = np.load(OUT / "ryry_gnn_oof.npz")
    P = {str(j): z[f"p{i}"] for i, j in enumerate(z["jobs"])}
    return [(jid, j, Ms[jid], P.get(jid, np.zeros(0)), [base[jid]["plans"]["opt"], gnn[jid]["plans"]["gnn_opt"]])
            for jid, j in jobs.items()]


def summary():
    base, gnn, cg = rows("base"), rows("gnn"), rows("cg")
    jobs = sorted(cg)
    old = sum(gnn[j]["gnn_opt"]["trucks"] for j in jobs)
    new = sum(cg[j]["long"]["trucks"] for j in jobs)
    lb = sum(cg[j]["bound"] for j in jobs)
    print(f"{len(jobs)} jobs. GNN + optimizer {old} -> long run {new}; proven lower bound {lb} (was {sum(base[j]['lb_valid'] for j in jobs)}); "
          f"gap {100 * (new / lb - 1):.2f} %; jobs proven optimal {sum(cg[j]['long']['trucks'] <= cg[j]['bound'] for j in jobs)}; "
          f"column generation converged on {sum(cg[j]['cg'].get('converged', True) for j in jobs)}; "
          f"road km {sum(gnn[j]['gnn_opt']['km'] for j in jobs):,.0f} -> {sum(cg[j]['long']['km'] for j in jobs):,.0f}")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "one":
        t = tasks()[int(sys.argv[2])]
        t0 = time.time()
        r = run_job(t)
        print({k: r[k] for k in ("bound", "cg", "long_s")}, "long", r["long"]["trucks"], "was", rows("gnn")[t[0]]["gnn_opt"]["trucks"],
              f"{time.time() - t0:.0f} s")
    elif mode == "run":
        pool_run(run_job, tasks(), "cg")
        summary()
    elif mode == "exact":  # prove() on every job the long run has not proven optimal -> ryry_exact.jsonl
        cg, jobs, Ms = rows("cg"), load(), matrices()
        pool_run(run_exact, [(jid, j, Ms[jid], cg[jid]["plans"]["long"]) for jid, j in jobs.items() if cg[jid]["long"]["trucks"] > cg[jid]["bound"]], "exact")
        ex = rows("exact")
        print(f"{len(ex)} jobs above their proven minimum. Long run {sum(cg[j]['long']['trucks'] for j in ex)} trucks; exact {sum(r['exact']['trucks'] for r in ex.values())}; "
              f"proven optimal now {sum(r['proven'] for r in ex.values())}; improved {sum(r['exact']['trucks'] < cg[j]['long']['trucks'] for j, r in ex.items())}; "
              f"too many loads to list {sum(r['info']['loads'] is None for r in ex.values())}; solver ran out of time {sum(r['info'].get('status') == 1 for r in ex.values())}")
    elif mode == "pb":  # the dive on every job the long run has not proven optimal -> ryry_pb.jsonl
        cg = rows("cg")
        pool_run(run_pb, [t[:4] + ([cg[t[0]]["plans"]["long"]],) for t in tasks() if cg[t[0]]["long"]["trucks"] > cg[t[0]]["bound"]], "pb")
        pb = rows("pb")
        print(f"{len(pb)} jobs above their proven minimum. Long run {sum(cg[j]['long']['trucks'] for j in pb)} trucks; dive alone "
              f"{sum(r['dive']['trucks'] for r in pb.values())}; dive + exact solver {sum(r['pb']['trucks'] for r in pb.values())}; "
              f"proven minimum {sum(cg[j]['bound'] for j in pb)}; jobs improved {sum(r['pb']['trucks'] < cg[j]['long']['trucks'] for j, r in pb.items())}")
    elif mode == "summary":
        summary()
