"""Clustering + routing for Ryry's 97 dispatch jobs, with a GNN. Data: data/97_SPATIAL_EXPERIMENT_FROZEN.csv (personal data).
Rules (user 2026-11-10, Ryry's company constraints in reference paper/project-notes.docx): 1-5 addresses per truck; load
<= 60 % of the truck's box volume (safe packing, no stacking); every stop within 50 km of its cluster's centre; unlimited
third-party trucks. Several addresses ride a small truck: 1-ton, or 1.4-ton when 1-ton is too small (at most 10 per job).
A stop too big for a 1.4-ton rides alone on the smallest bigger truck that fits. Objective: fewest trucks, then least
road km. A route starts at the Changwon depot and doesn't return. The stop order is exact (every order of <= 5 stops is
tried) on real road km from a local OSRM server (cluster/osrm.sh), so no location leaves this machine.

  python -I cluster/ryry.py osrm      # road km / hours per job -> cluster/results/ryry_osrm.npz
  python -I cluster/ryry.py base      # real dispatch, rule-based (Ryry's paper), k-means, optimizer -> ryry_base.jsonl
  python -I cluster/ryry.py gnn       # GNN, 5-fold out-of-fold: GNN alone and GNN + optimizer -> ryry_gnn.jsonl, ryry_gnn.pt
  python -I cluster/ryry.py summary   # comparison table -> ryry_summary.md
  python -I cluster/ryry.py depot     # how much the km depend on the depot's exact position -> ryry_depot.md
  python -I cluster/ryry.py forward   # GNN trained on April-June only, planning July-August -> ryry_fwd.jsonl, ryry_forward.md
  python -I cluster/ryry.py plan [csv] [method]  # per-stop plan (IDs and numbers only) -> ryry_plan.csv
"""
import csv
import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy.cluster.vq import kmeans2
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_array
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
import exact  # noqa: E402
from exact import ROOT, check, keep, knn_columns, radius  # noqa: E402

# The company's rules. The RULE_* variables are only for the price-of-rules study (cluster/ryry_rules.py).
K = exact.K = int(os.environ.get("RULE_K", 5))  # addresses per truck; exact.py's helpers read exact.K
R = float(os.environ.get("RULE_R", 50))  # km from the cluster's centre
FILL = float(os.environ.get("RULE_FILL", 0.6))  # share of the box volume that may be loaded
MAX14 = int(os.environ.get("RULE_MAX14", 10))  # 1.4-ton trucks per job
DATA, OUT = ROOT / "data/97_SPATIAL_EXPERIMENT_FROZEN.csv", ROOT / "cluster/results"
LIMIT, OSRM = 60, "http://127.0.0.1:5055"
# The depot: 14-8 Myeongseo-dong, Uichang-gu, Changwon (from the user, 2026-11-11).
# shortcut: the district's centre point in the offline map; the lot itself is not in it (at most ~0.7 km away). Replace with the lot's lat, lng when known.
DEPOT = (35.24834, 128.64666)
# inner box W x L x H in cm, from data/riri/251227-truck-sizes [abw].xlsx
TRUCKS = {"1t": (160, 275, 160), "1.4t": (170, 290, 160), "2.5t": (180, 430, 180), "3.5t": (205, 460, 180),
          "5t": (220, 620, 200), "5t+": (230, 750, 220), "11t-8.3m": (235, 830, 220), "11t-9.7m": (240, 970, 240)}
CAP = {t: FILL * w * l * h / 1e6 for t, (w, l, h) in TRUCKS.items()}  # usable m3 at the load limit
C, C14 = CAP["1t"], CAP["1.4t"]
PERMS = {s: np.array(list(itertools.permutations(range(s)))) for s in range(1, K + 1)}


def load(path=DATA):
    """{job_id: stops} in date order. Drops the 9 typo-corrected stops Ryry leaves out (6,404 -> 6,395)."""
    jobs = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("unresolved_coordinate") == "True":
                continue
            j = jobs.setdefault(r["job_id"], dict(ids=[], ll=[], xy=[], v=[], real=[], truck=[], date=r["record_date"]))
            j["ids"].append(r["experiment_stop_id"])
            j["truck"].append(r.get("truck_type", ""))
            j["ll"].append((float(r["latitude_final"]), float(r["longitude_final"])))
            j["xy"].append((float(r["x_km"]), float(r["y_km"])))
            j["v"].append(float(r["total_volume_m3"]))
            j["real"].append(int(float(r["existing_cluster_id"])) if r.get("existing_cluster_id") else -1)
    for j in jobs.values():
        for k in ("ll", "xy", "v", "real"):
            j[k] = np.array(j[k])
    return dict(sorted(jobs.items(), key=lambda kv: (kv[1]["date"], kv[0])))


def hav(a, b):
    a, b = np.radians(a), np.radians(b)
    h = np.sin((b[..., 0] - a[..., 0]) / 2) ** 2 + np.cos(a[..., 0]) * np.cos(b[..., 0]) * np.sin((b[..., 1] - a[..., 1]) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(h))


def osrm_table(ll, depot=None):
    """Road km and hours between the depot (index 0) and every stop, from the local server. Returns (D, T, filled)."""
    pts = np.r_[[depot or DEPOT], ll]
    q = ";".join(f"{lng:.6f},{lat:.6f}" for lat, lng in pts)
    with urllib.request.urlopen(f"{OSRM}/table/v1/driving/{q}?annotations=distance,duration", timeout=600) as r:
        t = json.load(r)
    assert t["code"] == "Ok", t.get("message")
    D, T = np.array(t["distances"], dtype=float) / 1000, np.array(t["durations"], dtype=float) / 3600
    miss = np.isnan(D) | np.isnan(T)
    # shortcut: a pair with no road between them (an island) gets 1.3 x straight line at 60 km/h; rare, counted in the log
    H = hav(pts[:, None], pts[None]) * 1.3
    return np.where(miss, H, D), np.where(miss, H / 60, T), int(miss.sum())


def matrices():
    z = np.load(OUT / "ryry_osrm.npz")
    return {str(j): (z[f"D{i}"], z[f"T{i}"]) for i, j in enumerate(z["jobs"])}


def route_cost(D, idx):
    """Best one-way road km from the depot (row 0 of D) through each cluster in idx (clusters x size), and that order."""
    best, order = np.full(len(idx), np.inf), np.zeros(idx.shape, int)
    for p in PERMS[idx.shape[1]]:  # at most 120 orders
        c = idx[:, p] + 1
        km = D[0, c[:, 0]] + D[c[:, :-1], c[:, 1:]].sum(1)
        better = km < best
        best[better], order[better] = km[better], p
    return best, np.take_along_axis(idx, order, 1)


def legs(M, path):
    c = np.r_[0, np.asarray(path) + 1]
    return float(M[c[:-1], c[1:]].sum())


def big_trucks(v):
    """Trucks for a stop too big for a 1.4-ton: the smallest bigger truck that fits, else several of the largest."""
    for t, cap in CAP.items():
        if v <= cap + 1e-9:
            return [t]
    # shortcut: equal largest trucks; a smaller last truck would sometimes do, the count is the same
    return ["11t-9.7m"] * math.ceil(v / CAP["11t-9.7m"] - 1e-9)


def lb_ryry(v):
    return max(math.ceil(len(v) / K), math.ceil(v.sum() / C - 1e-9)) if len(v) else 0


def lb_valid(v):
    """No plan under these rules can use fewer trucks: big stops ride alone; a small truck carries at most C, except up
    to MAX14 1.4-ton clusters (C14 - C more each) and lone stops above C (their excess)."""
    big = v > C14 + 1e-9
    s = v[~big]
    n_big = sum(len(big_trucks(x)) for x in v[big])
    if not len(s):
        return n_big
    extra = MAX14 * (C14 - C) + np.clip(s - C, 0, None).sum()
    return n_big + max(math.ceil(len(s) / K), math.ceil(s.sum() / C14 - 1e-9), math.ceil((s.sum() - extra) / C - 1e-9))


def labels(clusters, v):
    """Truck per small cluster: 1-ton if it fits; several stops over that ride a 1.4-ton (<= MAX14 by construction);
    a lone stop over it takes a 1.4-ton while any are left, else a 2.5-ton."""
    multi = sum(len(c) > 1 and v[c].sum() > C + 1e-9 for c in clusters)
    assert multi <= MAX14, f"{multi} multi-stop 1.4-ton clusters"
    left, out = MAX14 - multi, []
    for c in clusters:
        if v[c].sum() <= C + 1e-9:
            out.append("1t")
        elif len(c) > 1 or left > 0:
            out.append("1.4t")
            left -= len(c) == 1
        else:
            out.append("2.5t")
    return out


def split(j, M):
    """Stops a small truck can take, their xy / volume, and the road matrices for depot + those stops."""
    s = np.flatnonzero(j["v"] <= C14 + 1e-9)
    sel = np.r_[0, s + 1]
    return s, j["xy"][s], j["v"][s], M[0][np.ix_(sel, sel)], M[1][np.ix_(sel, sel)]


def score(j, M, s, Ds, Ts, clusters):
    """Check the rules, then trucks, road km and driving hours, big stops included. Clusters index the small stops."""
    xy, v = j["xy"][s], j["v"][s]
    check(xy, v, C14, R, [np.asarray(c) for c in clusters])
    lab = labels([list(c) for c in clusters], v)
    km = hours = 0.0
    for c in clusters:
        k, o = route_cost(Ds, np.array([c]))
        km, hours = km + k[0], hours + legs(Ts, o[0])
    nb = 0
    for b in np.flatnonzero(j["v"] > C14 + 1e-9):
        n = len(big_trucks(j["v"][b]))
        nb, km, hours = nb + n, km + n * M[0][0, b + 1], hours + n * M[1][0, b + 1]
    return dict(trucks=len(clusters) + nb, t14=lab.count("1.4t"), km=round(km, 1), hours=round(hours, 2))


def score_real(j, M):
    """The dispatch that was driven, on the same road distances. Breaks = clusters outside the radius, size or load rules."""
    groups = {}
    for i, r in enumerate(j["real"]):
        groups.setdefault(r if r >= 0 else -1 - i, []).append(i)
    km = hours = 0.0
    breaks = 0
    for c in groups.values():
        k, o = route_cost(M[0], np.array([c]))
        km, hours = km + k[0], hours + legs(M[1], o[0])
        breaks += int(len(c) > K or radius(j["xy"], np.array([c]))[0] > R + 1e-9 or (len(c) > 1 and j["v"][c].sum() > C14 + 1e-9))
    return dict(trucks=len(groups), km=round(km, 1), hours=round(hours, 2), breaks=breaks)


def greedy2(xy, v, order=None, used=None, look=30):
    """Rule-based: seeds in order (default farthest from the centre), each adds its nearest free stops while the rules
    hold, on a 1.4-ton while any are left. used = [1.4-ton clusters so far], shared across calls."""
    used = [0] if used is None else used
    free, out = np.ones(len(xy), bool), []
    for s in np.argsort(-np.linalg.norm(xy - xy.mean(0), axis=1)) if order is None else order:
        if not free[s]:
            continue
        cl, free[s] = [s], False
        cap = C14 if used[0] < MAX14 else C
        cand = np.flatnonzero(free)
        for c in cand[np.argsort(np.linalg.norm(xy[cand] - xy[s], axis=1))[:look]]:
            if len(cl) == K:
                break
            if v[cl].sum() + v[c] <= cap + 1e-9 and radius(xy, np.array([cl + [c]]))[0] <= R + 1e-9:
                cl.append(c)
                free[c] = False
        used[0] += int(len(cl) > 1 and v[cl].sum() > C + 1e-9)
        out.append(cl)
    return out


def kmeans(xy, v, seed=0):
    """k-means with k = Ryry's lower bound, then each group is split by the rule-based greedy where it breaks a rule."""
    _, lab = kmeans2(xy, max(1, min(len(xy), lb_ryry(v))), minit="++", rng=np.random.default_rng(seed))
    out, used = [], [0]
    for c in np.unique(lab):
        m = np.flatnonzero(lab == c)
        out += [m[g].tolist() for g in greedy2(xy[m], v[m], order=np.argsort(-v[m]), used=used)]
    return out


def solve2(xy, v, Ds, cols, extra=(), limit=LIMIT, fit=None, k=None):
    """Set partitioning: fewest trucks, then least road km, with at most MAX14 multi-stop 1.4-ton clusters.
    fit(idx) -> (fits a small truck, needs the 1.4-ton) adds a physical check on multi-stop loads (ryry_v3.py).
    k = the truck count when it is already known: only the road km are then chosen.
    Returns (clusters or None, info)."""
    by_size = {}
    for cl in extra:
        by_size.setdefault(len(cl), []).append(sorted(cl))
    idx_l, km_l, t14_l = [], [], []
    for idx in list(cols.values()) + [np.array(c) for c in by_size.values()]:
        if len(idx):
            idx = keep(xy, v, C14, R, idx)[0]
        t14 = (v[idx].sum(1) > C + 1e-9) & (idx.shape[1] > 1) if len(idx) else None
        if fit is not None and len(idx) and idx.shape[1] > 1:
            ok, need14 = fit(idx)
            idx, t14 = idx[ok], (t14 | need14)[ok]
        if len(idx):
            idx_l.append(idx)
            km_l.append(route_cost(Ds, idx)[0])
            t14_l.append(t14)
    off = np.cumsum([0] + [len(i) for i in idx_l])
    m = off[-1]
    rows = np.concatenate([i.ravel() for i in idx_l])
    colj = np.concatenate([np.repeat(np.arange(off[g], off[g + 1]), i.shape[1]) for g, i in enumerate(idx_l)])
    cons = [LinearConstraint(csc_array((np.ones(len(rows)), (rows, colj)), shape=(len(xy), m)), 1, 1),
            LinearConstraint(np.concatenate(t14_l).astype(float)[None], 0, MAX14)]
    t, x0, info = time.time(), None, dict(cols=int(m), t=0.0, status=0)
    if k is None:
        res = milp(np.ones(m), integrality=np.ones(m), bounds=Bounds(0, 1), constraints=cons, options={"time_limit": limit})
        info = dict(cols=int(m), t=round(time.time() - t, 2), status=int(res.status))
        if res.x is None:
            return None, info
        k, x0 = int(round(res.x.sum())), res.x
    res2 = milp(np.concatenate(km_l), integrality=np.ones(m), bounds=Bounds(0, 1),
                constraints=cons + [LinearConstraint(np.ones((1, m)), k, k)], options={"time_limit": 60})
    x = res2.x if res2.x is not None else x0
    if x is None:
        return None, info
    pick = np.flatnonzero(x > 0.5)
    g = np.searchsorted(off, pick, "right") - 1
    return [idx_l[gi][jj - off[gi]].tolist() for jj, gi in zip(pick, g)], info


def optimize(xy, v, Ds, cols, nets):
    """The solver, or the best safety net if the solver runs out of time before beating it."""
    cl, info = solve2(xy, v, Ds, cols, extra=[c for n in nets for c in n])
    best = min(nets, key=len)
    if cl is None or len(cl) > len(best):
        cl, info["fallback"] = best, True
    return [list(map(int, c)) for c in cl], info


def with_big(j, cl):
    """A saved plan (small-stop clusters, job indices) plus each big stop riding alone, so every stop appears once."""
    return [list(c) for c in cl] + [[int(b)] for b in np.flatnonzero(j["v"] > C14 + 1e-9)]


def finish(row, j, M, s, Ds, Ts, plans):
    for name, cl in plans.items():
        row[name] = score(j, M, s, Ds, Ts, cl)
    row["plans"] = {name: [s[np.asarray(c, int)].tolist() for c in cl] for name, cl in plans.items()}
    return row


def run_base(task):
    jid, j, M = task
    s, xy, v, Ds, Ts = split(j, M)
    row = dict(job=jid, n=len(j["v"]), big=len(j["v"]) - len(s), lb_ryry=lb_ryry(j["v"]), lb_valid=lb_valid(j["v"]),
               real=score_real(j, M))
    if len(s) < 2:
        return finish(row, j, M, s, Ds, Ts, {m: [[i] for i in range(len(s))] for m in ("rule", "kmeans", "opt")})
    plans = {"rule": greedy2(xy, v, order=np.argsort(-v)), "kmeans": kmeans(xy, v)}  # rule = paper: biggest first
    t = time.time()
    plans["opt"], row["opt_info"] = optimize(xy, v, Ds, knn_columns(xy, 15), [plans["rule"], greedy2(xy, v)])
    row["opt_s"] = round(time.time() - t, 1)
    return finish(row, j, M, s, Ds, Ts, plans)


# ---------- GNN: scores how likely two stops share a truck; trained on the optimizer's plans ----------
def features(xy, v, Ds, k=12):
    """Node and edge features over each stop's k nearest stops (pairs > 100 km apart can never share a cluster)."""
    n, k = len(xy), min(k, len(xy) - 1)
    dist, nb = cKDTree(xy).query(xy, k=k + 1)
    src, dst = np.repeat(np.arange(n), k), nb[:, 1:].ravel()
    ok = (src != dst) & (np.linalg.norm(xy[src] - xy[dst], axis=1) <= 2 * R)
    pairs = np.unique(np.sort(np.c_[src[ok], dst[ok]], 1), axis=0).reshape(-1, 2)
    a, b = np.r_[pairs[:, 0], pairs[:, 1]], np.r_[pairs[:, 1], pairs[:, 0]]  # both directions
    dep = Ds[0, 1:]
    X = np.c_[v / C, (xy - xy.mean(0)) / 100, dep / 300, dist[:, 1] / 50, dist[:, min(4, k)] / 50,
              np.full(n, n / 100), np.full(n, v.sum() / C / max(n / K, 1))]
    E = np.c_[np.linalg.norm(xy[a] - xy[b], axis=1) / 50, np.minimum(Ds[a + 1, b + 1], 500) / 50, (v[a] + v[b]) / C,
              (dep[a] - dep[b]) / 100]
    return dict(X=X.astype(np.float32), E=E.astype(np.float32), a=a, b=b, pairs=pairs)


def gnn_class():
    import torch
    nn = torch.nn

    class GNN(nn.Module):
        """Edge-state message passing: 4 rounds, then one logit per directed edge."""

        def __init__(s, dx=8, de=4, h=64, L=4):
            super().__init__()
            mlp = lambda i, o: nn.Sequential(nn.Linear(i, h), nn.ReLU(), nn.Linear(h, o))  # noqa: E731
            s.nx, s.ne, s.head = mlp(dx, h), mlp(de, h), mlp(3 * h, 1)
            s.msg = nn.ModuleList(mlp(3 * h, h) for _ in range(L))
            s.upd = nn.ModuleList(mlp(2 * h, h) for _ in range(L))
            s.nrm = nn.ModuleList(nn.LayerNorm(h) for _ in range(L))

        def forward(s, X, E, a, b):
            h, e = s.nx(X), s.ne(E)
            deg = torch.bincount(b, minlength=len(X)).clamp(min=1).unsqueeze(1)
            for msg, upd, nrm in zip(s.msg, s.upd, s.nrm):
                m = msg(torch.cat([h[a], h[b], e], 1))
                e = e + m
                h = nrm(h + upd(torch.cat([h, torch.zeros_like(h).index_add_(0, b, m) / deg], 1)))
            return s.head(torch.cat([h[a], h[b], e], 1)).squeeze(1)

    return torch, GNN


def batch(graphs, torch, dev):
    X, E, a, b, y, off = [], [], [], [], [], 0
    for g in graphs:
        X.append(g["X"]), E.append(g["E"]), a.append(g["a"] + off), b.append(g["b"] + off)
        y.append(np.tile(g.get("y", np.zeros(len(g["pairs"]), np.float32)), 2))
        off += len(g["X"])
    t = lambda z, dt=torch.float32: torch.as_tensor(np.concatenate(z), dtype=dt, device=dev)  # noqa: E731
    return t(X), t(E), t(a, torch.long), t(b, torch.long), t(y)


def train(graphs, epochs=400, seed=0):
    torch, GNN = gnn_class()
    torch.manual_seed(seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    X, E, a, b, y = batch(graphs, torch, dev)
    model = GNN(X.shape[1], E.shape[1]).to(dev)
    opt = torch.optim.AdamW(model.parameters(), 1e-3, weight_decay=1e-4)
    for _ in range(epochs):
        loss = torch.nn.functional.binary_cross_entropy_with_logits(model(X, E, a, b), y)
        opt.zero_grad()
        loss.backward()
        opt.step()
    return model.cpu().eval(), loss.item()


def predict(model, g):
    torch, _ = gnn_class()
    with torch.no_grad():
        logit = model(*batch([g], torch, "cpu")[:4]).numpy()
    m = len(g["pairs"])
    return 1 / (1 + np.exp(-(logit[:m] + logit[m:]) / 2))  # one probability per undirected pair


def gnn_greedy(xy, v, pairs, p):
    """GNN alone: merge pairs from the most to the least likely while the merged cluster keeps every rule."""
    root, members, used = np.arange(len(xy)), {i: [i] for i in range(len(xy))}, 0
    t14 = lambda c: len(c) > 1 and v[c].sum() > C + 1e-9  # noqa: E731
    for q in np.argsort(-p):
        x, y = root[pairs[q, 0]], root[pairs[q, 1]]
        if x == y:
            continue
        m = members[x] + members[y]
        after = used - t14(members[x]) - t14(members[y]) + t14(m)
        if len(m) <= K and v[m].sum() <= C14 + 1e-9 and after <= MAX14 and radius(xy, np.array([m]))[0] <= R + 1e-9:
            members[x], used = m, after
            root[members.pop(y)] = x
    return list(members.values())


def agglomerative(xy, v, Ds):
    """Classic agglomerative clustering: merge the closest pair by road km first, while every rule holds (same loop as the GNN's)."""
    i, j = np.triu_indices(len(xy), 1)
    ok = np.linalg.norm(xy[i] - xy[j], axis=1) <= 2 * R  # farther pairs can never share a cluster
    pairs = np.c_[i[ok], j[ok]]
    return gnn_greedy(xy, v, pairs, -Ds[pairs[:, 0] + 1, pairs[:, 1] + 1])


def run_agg(task):
    jid, j, M = task
    s, xy, v, Ds, Ts = split(j, M)
    return finish(dict(job=jid), j, M, s, Ds, Ts, {"agg": agglomerative(xy, v, Ds) if len(s) >= 2 else [[i] for i in range(len(s))]})


def run_knn8(task):
    """Ablation: the optimizer over each stop's 8 nearest stops, no GNN (same short-list size as GNN + optimizer)."""
    jid, j, M = task
    s, xy, v, Ds, Ts = split(j, M)
    row = dict(job=jid)
    if len(s) < 2:
        return finish(row, j, M, s, Ds, Ts, {"knn8": [[i] for i in range(len(s))]})
    t = time.time()
    plan, row["knn8_info"] = optimize(xy, v, Ds, knn_columns(xy, 8), [agglomerative(xy, v, Ds), greedy2(xy, v, order=np.argsort(-v))])
    row["knn8_s"] = round(time.time() - t, 1)
    return finish(row, j, M, s, Ds, Ts, {"knn8": plan})


def gnn_columns(n, pairs, p, top=8):
    """Candidate clusters: each stop plus any <= 4 of the stops the GNN rates most likely to share its truck."""
    nbrs = [[] for _ in range(n)]
    for (x, y), q in zip(pairs, p):
        nbrs[x].append((q, y))
        nbrs[y].append((q, x))
    cols = {s: set() for s in range(1, K + 1)}
    for i in range(n):
        best = [y for _, y in sorted(nbrs[i], reverse=True)[:top]]
        for s in range(1, K + 1):
            cols[s].update(tuple(sorted((i,) + c)) for c in itertools.combinations(best, s - 1))
    return {s: np.array(sorted(c)) for s, c in cols.items() if c}


def run_gnn(task):
    jid, j, M, p = task
    s, xy, v, Ds, Ts = split(j, M)
    row = dict(job=jid)
    if len(s) < 2:
        return finish(row, j, M, s, Ds, Ts, {m: [[i] for i in range(len(s))] for m in ("gnn", "gnn_opt")})
    pairs = features(xy, v, Ds)["pairs"]
    plans = {"gnn": gnn_greedy(xy, v, pairs, p)}
    t = time.time()
    plans["gnn_opt"], row["gnn_opt_info"] = optimize(xy, v, Ds, gnn_columns(len(xy), pairs, p),
                                                     [plans["gnn"], greedy2(xy, v, order=np.argsort(-v))])
    row["gnn_opt_s"] = round(time.time() - t, 1)
    return finish(row, j, M, s, Ds, Ts, plans)


def graphs_for(jobs, Ms, base=None):
    """One graph per job with >= 2 small stops; labels (same truck in the optimizer's plan) when base rows are given."""
    out = {}
    for jid, j in jobs.items():
        s, xy, v, Ds, _ = split(j, Ms[jid])
        if len(s) < 2:
            continue
        g = features(xy, v, Ds)
        if base is not None:
            lab = np.full(len(j["v"]), -1)
            for c_i, c in enumerate(base[jid]["plans"]["opt"]):
                lab[c] = c_i
            pos = lab[s]
            g["y"] = (pos[g["pairs"][:, 0]] == pos[g["pairs"][:, 1]]).astype(np.float32)
        out[jid] = g
    return out


def rows(name):
    f = OUT / f"ryry_{name}.jsonl"
    return {r["job"]: r for r in map(json.loads, f.open())} if f.exists() else {}


def pool_run(fn, tasks, out):
    done = rows(out)
    todo = [t for t in tasks if t[0] not in done]
    print(f"{out}: {len(todo)} jobs to run, {len(done)} done", flush=True)
    with mp.get_context("spawn").Pool(7) as pool, (OUT / f"ryry_{out}.jsonl").open("a") as f:  # 8 vCPUs, one spare
        for i, row in enumerate(pool.imap_unordered(fn, todo), 1):
            f.write(json.dumps(row) + "\n")
            f.flush()
            print(i, row["job"], {k: v["trucks"] for k, v in row.items() if isinstance(v, dict) and "trucks" in v}, flush=True)


def depot_check(shift=10.0):
    """The depot's position is the district centre, not the exact lot. Re-route the saved plans from sites 10 km north, east, south and west of it: the trucks
    can't change (no rule involves the depot), so this shows how far the km and the km saving move."""
    jobs, base, cg = load(), rows("base"), rows("cg")
    sites = {"Depot (Myeongseo-dong)": (0, 0), "10 km north": (shift, 0), "10 km east": (0, shift), "10 km south": (-shift, 0),
             "10 km west": (0, -shift)}
    lines = ["| depot site | real dispatch km | rule-based km | best plan km | best vs real | best vs rule-based |", "|---|---|---|---|---|---|"]
    out = []
    for name, (dn, de) in sites.items():
        dep = (DEPOT[0] + dn / 111.0, DEPOT[1] + de / (111.0 * math.cos(math.radians(DEPOT[0]))))
        km = dict(real=0.0, rule=0.0, long=0.0)
        for jid, j in jobs.items():
            D = osrm_table(j["ll"], dep)[0]
            real = {}
            for i, r in enumerate(j["real"]):
                real.setdefault(r if r >= 0 else -1 - i, []).append(i)
            plans = dict(real=list(real.values()), rule=with_big(j, base[jid]["plans"]["rule"]), long=with_big(j, cg[jid]["plans"]["long"]))
            for m, cl in plans.items():
                for c in cl:  # a stop too big for one truck is driven to once per truck, as in score()
                    n = len(big_trucks(j["v"][c[0]])) if m != "real" and len(c) == 1 and j["v"][c[0]] > C14 + 1e-9 else 1
                    km[m] += n * route_cost(D, np.array([c]))[0][0]
        if not dn and not de:  # the depot itself must reproduce the saved totals
            saved = sum(r["long"]["km"] for r in cg.values())
            assert abs(km["long"] / saved - 1) < 1e-3, (km["long"], saved)
        lines.append(f"| {name} | {km['real']:,.0f} | {km['rule']:,.0f} | {km['long']:,.0f} | {100 * (km['long'] / km['real'] - 1):+.1f} % | "
                     f"{100 * (km['long'] / km['rule'] - 1):+.1f} % |")
        out.append(dict(site=name, **{m: round(x) for m, x in km.items()}))
        print(lines[-1], flush=True)
    (OUT / "ryry_depot.json").write_text(json.dumps(out))  # for the results page
    lines += ["", "Truck counts are the same for every site: no rule involves the depot. The plans are the saved ones, re-routed "
              "(best stop order) from each site; re-optimising for a site could only shorten its km further."]
    (OUT / "ryry_depot.md").write_text("\n".join(lines) + "\n")


def forward():
    """A forward-in-time test: the GNN learns from April-June only and plans July-August, days later than any it saw."""
    jobs, Ms, base = load(), matrices(), rows("base")
    G = graphs_for(jobs, Ms, base)
    train_ids = [j for j in G if jobs[j]["date"] < "2026-07-01"]
    test = [j for j in jobs if jobs[j]["date"] >= "2026-07-01"]
    model, loss = train([G[j] for j in train_ids])
    print(f"trained on {len(train_ids)} jobs before July (loss {loss:.3f}); planning {len(test)} jobs from July on", flush=True)
    P = {j: predict(model, G[j]) for j in test if j in G}
    pool_run(run_gnn, [(jid, jobs[jid], Ms[jid], P.get(jid, np.zeros(0))) for jid in test], "fwd")
    fwd, gnn, knn8, cg = rows("fwd"), rows("gnn"), rows("knn8"), rows("cg")
    tot = lambda src, m: sum(src[j][m]["trucks"] for j in test)  # noqa: E731
    lines = [f"Forward test: GNN trained on {len(train_ids)} jobs (April-June), planning the {len(test)} jobs from July on.", "",
             "| method on the July-August jobs | trucks |", "|---|---|",
             f"| Real dispatch | {sum(base[j]['real']['trucks'] for j in test)} |", f"| Rule-based | {tot(base, 'rule')} |",
             f"| Optimizer, 8 nearest (no GNN) | {tot(knn8, 'knn8')} |",
             f"| GNN + optimizer, forward (trained on earlier months only) | {tot(fwd, 'gnn_opt')} |",
             f"| GNN + optimizer, 5-fold (earlier result) | {tot(gnn, 'gnn_opt')} |",
             f"| Proven minimum | {sum(cg[j]['bound'] for j in test)} |"]
    (OUT / "ryry_forward.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def summary():
    base, gnn = rows("base"), rows("gnn")
    jobs = sorted(base)
    lbr, lbv = sum(base[j]["lb_ryry"] for j in jobs), sum(base[j]["lb_valid"] for j in jobs)
    real = sum(base[j]["real"]["trucks"] for j in jobs)
    lines = [f"Ryry's 97 jobs, {sum(base[j]['n'] for j in jobs)} stops ({sum(base[j]['big'] for j in jobs)} too big for a "
             f"1.4-ton ride alone on a bigger truck). Lower bound: Ryry's formula {lbr}; valid under these rules {lbv}.", "",
             "| method | trucks | vs valid bound | vs real dispatch | jobs at the bound | 1.4-ton used | road km | driving h | rule breaks | solve s (max) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    agg, knn8, cg = rows("agg"), rows("knn8"), rows("cg")
    for name, src in [("real", base), ("rule", base), ("kmeans", base), ("agg", agg), ("gnn", gnn), ("opt", base), ("knn8", knn8),
                      ("gnn_opt", gnn), ("long", cg)]:
        rs = [src[j] for j in jobs if j in src]
        if len(rs) < len(jobs):
            continue
        t = sum(r[name]["trucks"] for r in rs)
        at = sum(r[name]["trucks"] <= base[r["job"]]["lb_valid"] for r in rs)
        t14 = sum(r[name].get("t14", 0) for r in rs) if name != "real" else "-"
        brk = sum(r[name].get("breaks", 0) for r in rs)
        ts = [r.get(f"{name}_s", 0) for r in rs]
        lines.append(f"| {name} | {t} | +{100 * (t / lbv - 1):.1f}% | {100 * (t / real - 1):+.1f}% | {at} | {t14} | "
                     f"{sum(r[name]['km'] for r in rs):,.0f} | {sum(r[name]['hours'] for r in rs):,.0f} | {brk} | {max(ts):.0f} |")
    fb = {m: sum(bool(src[j].get(f"{m}_info", {}).get("fallback")) for j in jobs if j in src) for m, src in (("opt", base), ("gnn_opt", gnn))}
    lines += ["", f"Solver fell back to its safety net (time limit {LIMIT} s): opt {fb['opt']}, gnn_opt {fb['gnn_opt']} jobs. "
              "GNN rows are out-of-fold (5 folds by date): each job is planned by a model that never saw it. "
              "Real dispatch: its own clusters on the same road distances; rule breaks = clusters over 50 km, 5 stops or a 1.4-ton's 60 %."]
    (OUT / "ryry_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def plan(path=DATA, method=None):
    """Per-stop plan. With a new file (or method 'live'): road km, the final GNN and the optimizer run live."""
    jobs = load(path)
    out = []
    if Path(path) == DATA and method != "live":
        base, gnn = rows("base"), rows("gnn")
        src = lambda m: base if m in ("rule", "kmeans", "opt") else gnn  # noqa: E731
        method = method or min(("opt", "gnn_opt"), key=lambda m: (sum(src(m)[j][m]["trucks"] for j in base),
                                                                  sum(src(m)[j][m]["km"] for j in base)))
        Ms = matrices()
        plans = {j: with_big(jobs[j], src(method)[j]["plans"][method]) for j in jobs}
    else:
        import torch
        method = "gnn_opt (live)"
        _, GNN = gnn_class()
        ck = torch.load(OUT / "ryry_gnn.pt")
        model = GNN(ck["dx"], ck["de"])
        model.load_state_dict(ck["state"])
        model.eval()
        Ms, plans = {}, {}
        for jid, j in jobs.items():
            D, T, _ = osrm_table(j["ll"])
            Ms[jid] = (D, T)
            g = graphs_for({jid: j}, Ms).get(jid)
            plans[jid] = with_big(j, run_gnn((jid, j, Ms[jid], predict(model, g) if g else np.zeros(0)))["plans"]["gnn_opt"])
    for jid, j in jobs.items():
        D, T = Ms[jid]
        small = [c for c in plans[jid] if j["v"][c].sum() <= C14 + 1e-9]  # the rest are big stops riding alone
        lab = dict(zip(map(tuple, small), labels([list(c) for c in small], j["v"])))
        for c_no, c in enumerate(plans[jid], 1):
            truck = lab.get(tuple(c)) or "+".join(big_trucks(j["v"][c[0]]))
            km, o = route_cost(D, np.array([c]))
            for k, i in enumerate(o[0], 1):
                out.append([jid, j["ids"][i], c_no, truck, k, round(km[0], 1), round(legs(T, o[0]), 2)])
    with (OUT / "ryry_plan.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["job_id", "experiment_stop_id", "cluster", "truck", "stop_order", "route_km", "route_hours"])
        w.writerows(out)
    print(f"{len(out)} stops in {sum(len(p) for p in plans.values())} clusters, method {method} -> {OUT / 'ryry_plan.csv'}")


if __name__ == "__main__":
    mode = sys.argv[1]
    OUT.mkdir(exist_ok=True)
    if mode == "osrm":
        jobs, z, filled = load(), {}, 0
        for i, (jid, j) in enumerate(jobs.items()):
            z[f"D{i}"], z[f"T{i}"], f = osrm_table(j["ll"])
            filled += f
        np.savez_compressed(OUT / "ryry_osrm.npz", jobs=np.array(list(jobs)), depot=np.array(DEPOT), **z)
        print(f"{len(jobs)} jobs; {filled} pairs had no road and got 1.3 x straight line")
    elif mode == "base":
        jobs, Ms = load(), matrices()
        pool_run(run_base, [(jid, j, Ms[jid]) for jid, j in jobs.items()], "base")
    elif mode == "gnn":
        jobs, Ms, base = load(), matrices(), rows("base")
        G = graphs_for(jobs, Ms, base)
        ids = list(G)
        fold = {jid: i * 5 // len(ids) for i, jid in enumerate(ids)}  # 5 contiguous date blocks
        P = {}
        for k in range(5):
            model, loss = train([G[j] for j in ids if fold[j] != k])
            P.update({j: predict(model, G[j]) for j in ids if fold[j] == k})
            ap = np.mean([((P[j] > 0.5) == (G[j]["y"] > 0.5)).mean() for j in ids if fold[j] == k])
            print(f"fold {k}: train loss {loss:.3f}, held-out pair accuracy {ap:.3f}", flush=True)
        np.savez_compressed(OUT / "ryry_gnn_oof.npz", jobs=np.array(list(P)), **{f"p{i}": P[j] for i, j in enumerate(P)})
        model, loss = train([G[j] for j in ids])
        import torch
        torch.save(dict(state=model.state_dict(), dx=G[ids[0]]["X"].shape[1], de=G[ids[0]]["E"].shape[1]), OUT / "ryry_gnn.pt")
        pool_run(run_gnn, [(jid, j, Ms[jid], P.get(jid, np.zeros(0))) for jid, j in jobs.items()], "gnn")
    elif mode == "knn8":
        jobs, Ms = load(), matrices()
        pool_run(run_knn8, [(jid, j, Ms[jid]) for jid, j in jobs.items()], "knn8")
        print("knn8 + optimizer:", sum(r["knn8"]["trucks"] for r in rows("knn8").values()), "trucks")
    elif mode == "agg":
        jobs, Ms = load(), matrices()
        with (OUT / "ryry_agg.jsonl").open("w") as f:
            for jid, j in jobs.items():
                f.write(json.dumps(run_agg((jid, j, Ms[jid]))) + "\n")
        print("agglomerative:", sum(r["agg"]["trucks"] for r in rows("agg").values()), "trucks")
    elif mode == "depot":
        depot_check()
    elif mode == "forward":
        forward()
    elif mode == "summary":
        summary()
    elif mode == "plan":
        plan(Path(sys.argv[2]) if len(sys.argv) > 2 else DATA, sys.argv[3] if len(sys.argv) > 3 else None)
