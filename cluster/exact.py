"""Exact and shortlist clustering for bulky delivery, on Amazon LMRRC station-days.
A cluster is feasible if it has <= 5 stops, total volume <= truck capacity C and every stop within R of its centroid;
a solution puts every stop in exactly one cluster. Objective: fewest clusters, then smallest total radius.
  greedy    seeds farthest from the centre first, adds nearest stops while the rules hold (the simple method)
  exact     set partitioning over ALL feasible clusters (small n only): the true optimum
  shortlist set partitioning over clusters of each stop + any <= 4 of its k nearest neighbours, plus the greedy
            clusters as a safety net, so it is never worse than greedy

  python cluster/exact.py small    # 40-stop neighbourhoods: floor vs greedy vs exact vs shortlist (k = 5, 10)
  python cluster/exact.py large    # whole station-days: floor vs greedy vs shortlist (k = 10)
  python cluster/exact.py summary  # tables from cluster/results/*.jsonl
Map cell = volume pressure p x radius R (a multiple of d4, the median distance to the 4th-nearest stop, or 50 km).
Rows append to cluster/results/<mode>.jsonl as they finish; a rerun skips finished rows."""
import itertools
import json
import math
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_array
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
K = 5  # max stops per cluster
PRESS = ("raw", 0.5, 1.0)
MULT = (1, 2, 4, "50km")
CFG = {"small": dict(ks=(5, 10), limit=900), "large": dict(ks=(10,), limit=300)}


def load_days(d=ROOT / "data/almrrc"):
    """Station-day = the sampled routes of one station on one date. Returns [(key, xy km, volume cm3, capacity cm3)]."""
    routes = json.load(open(d / "eval_route_data.json"))
    pk = json.load(open(d / "eval_package_data.json"))
    days = {}
    for rid, r in routes.items():
        g = days.setdefault(f'{r["station_code"]}_{r["date_YYYY_MM_DD"]}', ([], [], []))
        g[2].append(r["executor_capacity_cm3"])
        for sid, s in r["stops"].items():
            if s["type"] == "Dropoff":
                g[0].append((s["lat"], s["lng"]))
                g[1].append(sum(math.prod(p["dimensions"].values()) for p in pk[rid].get(sid, {}).values()))
    out = []
    for key in sorted(days):
        ll, v, cap = days[key]
        ll, v, C = np.array(ll), np.array(v, float), float(np.median(cap))
        if len(v) < 50 or v.max() > C:
            continue
        lat0 = math.radians(ll[:, 0].mean())
        out.append((key, np.c_[np.radians(ll[:, 1]) * math.cos(lat0), np.radians(ll[:, 0])] * 6371.0, v, C))
    return out


def scale(v, C, p):
    """Volumes at pressure p: the day's median stop fills p/5 of a truck."""
    # shortcut: a stop bigger than a truck would be split over trucks in practice; capped at C so every stop fits
    return v if p == "raw" else np.minimum(v * (p * C / 5) / np.median(v), C)


def d4(xy):
    return float(np.median(cKDTree(xy).query(xy, k=5)[0][:, 4]))


def floor_(n, v, C):
    """No solution can use fewer clusters than this."""
    return max(math.ceil(n / K), math.ceil(v.sum() / C - 1e-9))


def radius(xy, idx):
    """Max distance from each cluster's centroid; idx is (clusters, size)."""
    pts = xy[idx]
    return np.linalg.norm(pts - pts.mean(1, keepdims=True), axis=2).max(1)


def keep(xy, v, C, R, idx):
    """The feasible clusters among idx (all one size) and their radii."""
    r = radius(xy, idx)
    ok = (v[idx].sum(1) <= C * (1 + 1e-9)) & (r <= R + 1e-9)
    return idx[ok], r[ok]


def check(xy, v, C, R, clusters):
    assert np.array_equal(np.sort(np.concatenate(clusters)), np.arange(len(xy))), "every stop exactly once"
    for c in clusters:
        assert len(c) <= K and v[c].sum() <= C * (1 + 1e-9) and radius(xy, np.array([c]))[0] <= R + 1e-9, c


def greedy(xy, v, C, R, look=30):
    free = np.ones(len(xy), bool)
    out = []
    for s in np.argsort(-np.linalg.norm(xy - xy.mean(0), axis=1)):
        if not free[s]:
            continue
        cl = [s]
        free[s] = False
        cand = np.flatnonzero(free)
        for c in cand[np.argsort(np.linalg.norm(xy[cand] - xy[s], axis=1))[:look]]:
            if len(cl) == K:
                break
            if v[cl].sum() + v[c] <= C * (1 + 1e-9) and radius(xy, np.array([cl + [c]]))[0] <= R + 1e-9:
                cl.append(c)
                free[c] = False
        out.append(cl)
    return out


def all_columns(n):
    return {s: np.array(list(itertools.combinations(range(n), s))) for s in range(1, min(K, n) + 1)}


def every_load(xy, v, C, R, cap=400_000):
    """Every set of 1..K stops that may share a truck, by size, or None when there are more than cap. Built size by
    size: a set grows by a later stop while the volume fits and every pair stays within 2R (two stops farther apart can
    never be within R of one centre). The radius itself is left to keep(): a set can pass it while a subset fails."""
    n = len(xy)
    near = np.linalg.norm(xy[:, None] - xy[None], axis=2) <= 2 * R + 1e-9
    cur, out, total = np.arange(n)[:, None], {1: np.arange(n)[:, None]}, n
    for size in range(2, K + 1):
        vol, nxt = v[cur].sum(1), []
        for j in range(1, n):
            grow = cur[(cur[:, -1] < j) & (vol + v[j] <= C * (1 + 1e-9))]  # the cheap tests first
            grow = grow[near[grow, j].all(1)]
            if len(grow):
                nxt.append(np.c_[grow, np.full(len(grow), j)])
                total += len(grow)
                if total > cap:  # stop before a whole size is built: it can be tens of millions of rows
                    return None
        if not nxt:
            break
        out[size] = cur = np.concatenate(nxt)
    return out


def knn_columns(xy, k):
    """Each stop plus any <= 4 of its k nearest neighbours, deduplicated."""
    k = min(k, len(xy) - 1)
    nb = cKDTree(xy).query(xy, k=k + 1)[1]  # column 0 is the stop itself (or a stop at the same spot)
    cols = {1: np.arange(len(xy))[:, None]}
    for s in range(2, K + 1):
        pat = np.array(list(itertools.combinations(range(1, k + 1), s - 1)), int)
        if not len(pat):
            continue
        c = np.sort(np.concatenate([nb[:, :1].repeat(len(pat), 0), nb[:, pat].reshape(-1, s - 1)], 1), 1)
        cols[s] = np.unique(c[(np.diff(c, axis=1) != 0).all(1)], axis=0)
    return cols


def solve(xy, v, C, R, cols, extra=(), limit=None):
    """Set partitioning over the feasible clusters in cols plus extra. Returns (clusters or None, info)."""
    n = len(xy)
    by_size = {}
    for cl in extra:
        by_size.setdefault(len(cl), []).append(sorted(cl))
    groups = [keep(xy, v, C, R, idx) for idx in list(cols.values()) + [np.array(c) for c in by_size.values()]]
    off = np.cumsum([0] + [len(idx) for idx, _ in groups])
    rows = np.concatenate([idx.ravel() for idx, _ in groups])
    colj = np.concatenate([np.repeat(np.arange(off[g], off[g + 1]), idx.shape[1]) for g, (idx, _) in enumerate(groups)])
    m = off[-1]
    A = csc_array((np.ones(len(rows)), (rows, colj)), shape=(n, m))
    each_once = LinearConstraint(A, 1, 1)
    t = time.time()
    # one weighted objective (count + small radius term) spent >15 min proving the radius part; two solves instead
    res = milp(np.ones(m), integrality=np.ones(m), bounds=Bounds(0, 1), constraints=each_once,
               options={"time_limit": limit} if limit else {})
    info = dict(cols=int(m), t=round(time.time() - t, 2), status=int(res.status))
    if res.x is None:
        return None, info
    x, count = res.x, int(round(res.x.sum()))
    if res.mip_dual_bound is not None:  # lower bound on the count, valid for this column set only
        info["count_lb"] = math.ceil(res.mip_dual_bound - 1e-6)
    t = time.time()  # then the most compact solution with that count, best found in <= 60 s
    res2 = milp(np.concatenate([r for _, r in groups]), integrality=np.ones(m), bounds=Bounds(0, 1),
                constraints=[each_once, LinearConstraint(np.ones((1, m)), count, count)], options={"time_limit": 60})
    info["t_rad"] = round(time.time() - t, 2)
    if res2.x is not None:
        x = res2.x
    pick = np.flatnonzero(x > 0.5)
    g = np.searchsorted(off, pick, "right") - 1
    clusters = [groups[gi][0][j - off[gi]] for j, gi in zip(pick, g)]
    check(xy, v, C, R, clusters)
    return clusters, info


def mean_rad(xy, clusters):
    return round(float(np.mean([radius(xy, np.array([c]))[0] for c in clusters])), 4)


def run(task):
    row, xy, v, C = task
    cfg, n = CFG[row["mode"]], len(xy)
    R = 50.0 if row["m"] == "50km" else row["m"] * d4(xy)
    g = greedy(xy, v, C, R)
    check(xy, v, C, R, g)
    row.update(n=n, R=round(R, 4), floor=floor_(n, v, C), greedy=len(g), greedy_rad=mean_rad(xy, g))
    methods = [(f"knn{k}", lambda k=k: knn_columns(xy, k)) for k in cfg["ks"]]
    if row["mode"] == "small":
        methods.insert(0, ("exact", lambda: all_columns(n)))
    for name, cols in methods:
        if row["mode"] == "large" and len(g) == row["floor"]:  # greedy already at the floor: provably optimal
            row.update({name: len(g), name + "_rad": row["greedy_rad"], name + "_info": "floor"})
            continue
        cl, info = solve(xy, v, C, R, cols(), extra=() if name == "exact" else g, limit=cfg["limit"])
        if cl is None or len(cl) > len(g):  # time limit hit first (milp takes no warm start): the safety net is the answer
            cl, info["fallback"] = g, True
        row.update({name: len(cl), name + "_rad": mean_rad(xy, cl), name + "_info": info})
        assert row[name] <= row["greedy"], (name, row[name], row["greedy"])
    return row


def tasks(mode, days, per_cell=30, hood=40, n_large=20, seed=0):
    rng = np.random.default_rng(seed)
    if mode == "small":  # the 40 stops nearest a random stop, on 30 random days; same neighbourhoods in every cell
        picks = []
        for di in rng.choice(len(days), per_cell, replace=False):
            key, xy, v, C = days[di]
            picks.append((key, cKDTree(xy).query(xy[rng.integers(len(xy))], k=hood)[1], days[di]))
    else:  # whole days spread over the size range
        order = sorted(range(len(days)), key=lambda i: len(days[i][1]))
        at = np.unique(np.linspace(0, len(days) - 1, n_large).round().astype(int))
        picks = [(days[order[i]][0], slice(None), days[order[i]]) for i in at]
    for key, sel, (_, xy, v, C) in picks:
        for p in PRESS:
            vv = scale(v, C, p)[sel]
            for m in MULT:
                yield dict(mode=mode, day=key, p=p, m=m), xy[sel], vv, C


def summary():
    def med(rs, f):
        return f"{100 * np.median([f(r) for r in rs]):.1f}"

    for mode in ("small", "large"):
        f = ROOT / f"cluster/results/{mode}.jsonl"
        if not f.exists():
            continue
        rows = [json.loads(line) for line in f.open()]
        small = mode == "small"
        ks = [k for k in ("knn5", "knn10") if k in rows[0]]
        meth = ["greedy"] + (["exact"] if small else []) + ks
        extra = ["greedy over exact"] + [f"{k} = exact" for k in ks] + ["exact proven"] if small else \
            [f"{k} saves vs greedy" for k in ks]
        print(f"\n## {mode}: {len(rows)} rows. Median % over the floor, then comparisons (%)")
        print("| pressure | R | " + " | ".join(meth + extra + [f"{ks[-1]} radius vs greedy", "max solve s"]) + " |")
        for p in PRESS:
            for m in MULT:
                rs = [r for r in rows if r["p"] == p and r["m"] == m]
                if not rs:
                    continue
                cells = [med(rs, lambda r, a=a: r[a] / r["floor"] - 1) for a in meth]
                if small:
                    cells.append(med(rs, lambda r: r["greedy"] / r["exact"] - 1))
                    cells += [f"{100 * np.mean([r[k] == r['exact'] for r in rs]):.0f}" for k in ks]
                    cells.append(f"{100 * np.mean([r['exact_info']['status'] == 0 for r in rs]):.0f}")
                else:
                    cells += [f"{100 * np.mean([1 - r[k] / r['greedy'] for r in rs]):.1f}" for k in ks]
                cells.append(med(rs, lambda r: r[ks[-1] + "_rad"] / max(r["greedy_rad"], 1e-9) - 1))
                ts = [r[a + "_info"]["t"] for r in rs for a in meth[1:] if isinstance(r[a + "_info"], dict)]
                print(f"| {p} | {m} | " + " | ".join(cells) + f" | {max(ts, default=0):.0f} |")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "summary":
        summary()
        sys.exit()
    out = ROOT / f"cluster/results/{mode}.jsonl"
    out.parent.mkdir(exist_ok=True)
    done = {(r["day"], r["p"], r["m"]) for r in map(json.loads, out.open())} if out.exists() else set()
    todo = [t for t in tasks(mode, load_days()) if (t[0]["day"], t[0]["p"], t[0]["m"]) not in done]
    print(f"{mode}: {len(todo)} tasks to run, {len(done)} done", flush=True)
    with Pool(7) as pool, out.open("a") as f:  # 8 vCPUs, one left for the system
        for i, row in enumerate(pool.imap_unordered(run, todo), 1):
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(i, row["day"], row["p"], row["m"], "floor", row["floor"], "greedy", row["greedy"],
                  *(f"{a} {row[a]}" for a in ("exact", "knn5", "knn10") if a in row), flush=True)
