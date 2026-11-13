"""Version 3: plans whose loads really fit the truck floor, and one small multi-task model that stands in for the three
slow parts of planning: which stops to group, whether a load fits, and how far the road is.
  python -I cluster/ryry_v3.py ref       # reference: company rules + physical fit, real packer and road km -> ryry_v3ref.jsonl
  python -I cluster/ryry_v3.py train     # the multi-task model, 5 folds by date -> ryry_mt_fold*.pt, ryry_mt.pt, ryry_mt_heads.json
  python -I cluster/ryry_v3.py e2e       # plan with the model only, and with simple rules only; both then checked against
                                         # the real packer and real roads -> ryry_v3model.jsonl, ryry_v3simple.jsonl
  python -I cluster/ryry_v3.py summary   # -> ryry_v3.json
  python -I cluster/ryry_v3.py train _tf | train _ptr   # rival AI encoders (Transformer, pointer network), same heads and tests
  python -I cluster/ryry_v3.py alone [tag]              # the model with no solver (greedy merge by its pair scores) -> ryry_v3alone{tag}.jsonl
  python -I cluster/ryry_v3.py extra     # saved plans made true and priced, per-job counts, one load's layout -> ryry_v3x.json
Physical fit: a multi-stop load needs a floor layout with GAP cm between boxes (cluster/pack.py); a load the packer
can't lay out counts as not fitting. A stop alone always gets a truck of its own. The model sees coordinates, volumes
and box sizes only: no road data and no packer."""
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
from exact import knn_columns, radius  # noqa: E402
from pack import fits  # noqa: E402
from ryry import (C, C14, DEPOT, K, MAX14, OUT, R, TRUCKS, big_trucks, features, gnn_columns, hav, lb_valid, legs, load,  # noqa: E402
                  matrices, pool_run, route_cost, rows, solve2, split)
from ryry_cg import merge, prove  # noqa: E402
from ryry_load import footprints  # noqa: E402

GAP, REF_LIMIT, FOLDS = 5.0, 120, 5
TAGS = ("", "_mid", "_big")  # model sizes trained: default 48 x 3, then larger ones
# Rival AI models: the same inputs, heads, losses, folds and tests; only the encoder differs (train _tf / train _ptr).
ARCH = {"_tf": "transformer", "_ptr": "pointer"}
FL = {t: TRUCKS[t][:2] for t in ("1t", "1.4t")}
AREA = {t: (w + GAP) * (l + GAP) for t, (w, l) in FL.items()}
TID = {"1t": 0, "1.4t": 1}


def area_of(fp):
    return sum((w + GAP) * (d + GAP) for w, d in fp)


class Packer:
    """The real check: is there a floor layout for these stops' boxes on this truck? Answers are remembered."""

    def __init__(s, fp):
        s.fp, s.memo = fp, {}

    def __call__(s, c, truck):
        k = (tuple(sorted(int(i) for i in c)), truck)
        if k not in s.memo:
            s.memo[k] = fits([b for i in k[0] for b in s.fp[i]], *FL[truck], GAP) is True
        return s.memo[k]

    def truck(s, c, vol):
        """The small truck this load needs: '1t', '1.4t', or None when it fits neither (volume limit or floor)."""
        if vol <= C + 1e-9 and s(c, "1t"):
            return "1t"
        return "1.4t" if vol <= C14 + 1e-9 and s(c, "1.4t") else None


def true_fit(P, s, v, area):
    """The physical check as solve2 wants it, on rows of small-stop indices."""
    def fit(idx):
        ok, need = np.zeros(len(idx), bool), np.zeros(len(idx), bool)
        for r in np.flatnonzero(area[idx].sum(1) <= AREA["1.4t"]):  # more footprint than floor can never fit
            t = P.truck(s[idx[r]], v[idx[r]].sum())
            ok[r], need[r] = t is not None, t == "1.4t"
        return ok, need
    return fit


def settle(P, s, xy, v, area, clusters):
    """Make a plan true. A multi-stop load with no layout sheds its largest-footprint stop until it has one; once
    MAX14 loads ride a 1.4-ton, further ones shed until they fit a 1-ton. Returns (clusters, truck per cluster, stops shed)."""
    out, shed, n14 = [], 0, 0
    for c in sorted((sorted(map(int, c)) for c in clusters), key=lambda c: (-len(c), c)):
        while len(c) > 1:
            t = P.truck(s[c], v[c].sum())
            if (t == "1t" or (t == "1.4t" and n14 < MAX14)) and radius(xy, np.array([c]))[0] <= R + 1e-9:
                n14 += t == "1.4t"
                break
            drop = max(c, key=lambda i: area[i])
            c.remove(drop)
            out.append([drop])
            shed += 1
        out.append(c)
    trucks = []
    for c in out:
        t = P.truck(s[c], v[c].sum())
        if len(c) == 1 and t != "1t":  # alone: a 1.4-ton while any are left, else the next size up
            t = "1.4t" if t == "1.4t" and n14 < MAX14 else "2.5t"
            n14 += t == "1.4t"
        trucks.append(t)
    return out, trucks, shed


def score3(j, M, s, clusters, trucks):
    """Check every rule and the physical fit labels, then trucks, real road km and hours (big stops included)."""
    D, T = M
    xy, v = j["xy"][s], j["v"][s]
    assert sorted(i for c in clusters for i in c) == list(range(len(s))), "every small stop exactly once"
    km = hours = 0.0
    for c, t in zip(clusters, trucks):
        assert len(c) <= K and (len(c) == 1 or (t in FL and v[c].sum() <= C14 + 1e-9 and radius(xy, np.array([c]))[0] <= R + 1e-9)), (c, t)
        k, o = route_cost(D, np.array([s[c]]))
        km, hours = km + k[0], hours + legs(T, o[0])
    assert sum(t == "1.4t" for t in trucks) <= MAX14
    nb = 0
    for b in np.flatnonzero(j["v"] > C14 + 1e-9):
        n = len(big_trucks(j["v"][b]))
        nb, km, hours = nb + n, km + n * D[0, b + 1], hours + n * T[0, b + 1]
    return dict(trucks=len(clusters) + nb, t14=sum(t == "1.4t" for t in trucks), km=round(float(km), 1), hours=round(float(hours), 2))


def small_setup(j, M, fp):
    s, xy, v, Ds, Ts = split(j, M)
    return s, xy, v, Ds, np.array([area_of(fp[i]) for i in s]), Packer(fp)


def run_ref(task):
    """Reference plan: every rule plus the physical fit, with the real packer and real road km in the loop."""
    jid, j, M, p, base_plan, fp = task
    s, xy, v, Ds, area, P = small_setup(j, M, fp)
    row = dict(job=jid)
    if len(s) < 2:
        cl, tr, _ = settle(P, s, xy, v, area, [[i] for i in range(len(s))])
        row.update(ref=score3(j, M, s, cl, tr), plan=[s[c].tolist() for c in cl], fit=[], base_shed=0, base_true=score3(j, M, s, cl, tr))
        return row
    pos = {int(k): i for i, k in enumerate(s)}
    base = [[pos[k] for k in c] for c in base_plan]
    net, tr, shed = settle(P, s, xy, v, area, base)  # the 60 % plan made physically true: also the safety net
    row.update(base_shed=shed, base_true=score3(j, M, s, net, tr))
    pool = merge(gnn_columns(len(xy), features(xy, v, Ds)["pairs"], p, top=12), knn_columns(xy, 15))
    t = time.time()
    cl, info = solve2(xy, v, Ds, pool, extra=net, limit=REF_LIMIT, fit=true_fit(P, s, v, area))
    if cl is None or len(cl) > len(net):
        cl, info["fallback"] = net, True
    cl, tr, shed = settle(P, s, xy, v, area, cl)
    # the exact step: every load is listed and priced; the physical check runs only on the loads that could still matter
    better, floor_, proven, pinfo = prove(xy, v, Ds, cl, fit=true_fit(P, s, v, area), limit=REF_LIMIT, max_left=40_000)
    if len(better) < len(cl):
        c2, t2, s2 = settle(P, s, xy, v, area, better)
        if len(c2) < len(cl):
            cl, tr, shed = c2, t2, shed + s2
    info.update(proven=bool(proven), floor=floor_, exact=pinfo)
    row.update(ref=score3(j, M, s, cl, tr), info=info, s=round(time.time() - t, 1), shed=shed, plan=[s[c].tolist() for c in cl])
    memo = list(P.memo.items())  # (stops, truck) -> fits: training data for the model's load-fit head
    rng = np.random.default_rng(0)
    row["fit"] = [[list(k[0]), k[1], bool(f)] for k, f in (memo if len(memo) <= 8000 else [memo[i] for i in rng.choice(len(memo), 8000, replace=False)])]
    return row


# ---------- the multi-task model ----------
def mt_graph(j, s, fp):
    """Inputs without any road data or packer: coordinates, volumes, box sizes."""
    xy, v, ll = j["xy"][s], j["v"][s], j["ll"][s]
    n, k = len(s), min(12, len(s) - 1)
    dist, nb = cKDTree(xy).query(xy, k=k + 1)
    src, dst = np.repeat(np.arange(n), k), nb[:, 1:].ravel()
    ok = (src != dst) & (np.linalg.norm(xy[src] - xy[dst], axis=1) <= 2 * R)
    pairs = np.unique(np.sort(np.c_[src[ok], dst[ok]], 1), axis=0).reshape(-1, 2)
    a, b = np.r_[pairs[:, 0], pairs[:, 1]], np.r_[pairs[:, 1], pairs[:, 0]]
    dep = hav(np.array(DEPOT), ll)  # straight-line km to the depot
    bx = np.array([[len(fp[i]), sum(w * d for w, d in fp[i]) / 1e4, max((max(q) for q in fp[i]), default=0), max((min(q) for q in fp[i]), default=0)] for i in s])
    X = np.c_[v / C, (xy - xy.mean(0)) / 100, dep / 300, dist[:, 1] / 50, dist[:, min(4, k)] / 50, np.full(n, n / 100),
              np.full(n, v.sum() / C / max(n / K, 1)), (ll[:, 0] - 36) / 2, (ll[:, 1] - 127.8) / 2, bx[:, 0] / 10, bx[:, 1] / 4.4,
              bx[:, 2] / 275, bx[:, 3] / 160]
    d = xy[a] - xy[b]
    E = np.c_[np.linalg.norm(d, axis=1) / 50, (v[a] + v[b]) / C, (dep[a] - dep[b]) / 100, d / 50]
    sweep = np.argsort(np.arctan2(ll[:, 0] - DEPOT[0], (ll[:, 1] - DEPOT[1]) * np.cos(np.radians(DEPOT[0]))))
    return dict(X=X.astype(np.float32), E=E.astype(np.float32), a=a, b=b, pairs=pairs, dep=dep.astype(np.float32), xy=xy.astype(np.float32), order=sweep)


def context(graphs, torch, dev="cpu"):
    """What the rival encoders need: every ordered pair of stops within a job (Transformer: who attends to whom), and
    each job's stops as a padded sequence in sweep order around the depot (pointer network)."""
    fa, fb, pad, off, longest = [], [], [], 0, max(len(g["X"]) for g in graphs)
    for g in graphs:
        n = len(g["X"])
        i = np.arange(n)
        fa.append(np.repeat(i, n) + off), fb.append(np.tile(i, n) + off)
        pad.append(np.r_[g["order"] + off, np.full(longest - n, -1)])
        off += n
    t = lambda z: torch.as_tensor(z, dtype=torch.long, device=dev)  # noqa: E731
    return dict(fa=t(np.concatenate(fa)), fb=t(np.concatenate(fb)), pad=t(np.stack(pad)))


def box_rows(fp, groups, trucks):
    """Flat box table for a list of groups (job stop indices): per-box features, group index, per-group extras."""
    bf, gi, ex = [], [], []
    for g, (c, t) in enumerate(zip(groups, trucks)):
        bs = [tuple(sorted(q)) for i in c for q in fp[i]]
        W, L = FL[t]
        bf += [(w / 100, d / 100, w * d / 1e4) for w, d in bs]
        gi += [g] * len(bs)
        ex.append((sum((w + GAP) * (d + GAP) for w, d in bs) / AREA[t], len(bs) / 10, max((d for _, d in bs), default=0) / L, TID[t]))
    return np.array(bf, np.float32).reshape(-1, 3), np.array(gi, np.int64), np.array(ex, np.float32).reshape(-1, 4)


def mt_class(h=48, L=3, arch="gnn"):
    import torch
    nn, F = torch.nn, torch.nn.functional
    HEADS = 4

    class MT(nn.Module):
        """One encoder, four heads: pairing (edges), road km (any pair, and from the depot), load fit (any group of boxes),
        truck share (per stop; its sum is the fleet size). arch picks the encoder: "gnn" = message passing over each
        stop's nearest stops (ours); "transformer" = the attention model's encoder (Kool et al. 2019), every stop attends
        to every stop of its job; "pointer" = the pointer network's encoder (Vinyals et al. 2015), an LSTM reads the
        stops as a sequence."""

        def __init__(s, dx=14, de=5):
            super().__init__()
            mlp = lambda i, o: nn.Sequential(nn.Linear(i, h), nn.ReLU(), nn.Linear(h, o))  # noqa: E731
            s.nx, s.ne = mlp(dx, h), mlp(de, h)
            if arch == "gnn":
                s.msg = nn.ModuleList(mlp(3 * h, h) for _ in range(L))
                s.upd = nn.ModuleList(mlp(2 * h, h) for _ in range(L))
            elif arch == "transformer":
                s.qkv = nn.ModuleList(nn.Linear(h, 3 * h) for _ in range(L))
                s.att = nn.ModuleList(nn.Linear(h, h) for _ in range(L))
                s.ff = nn.ModuleList(mlp(h, h) for _ in range(L))
                s.nrm2 = nn.ModuleList(nn.LayerNorm(h) for _ in range(L))
            else:
                s.rnn = nn.LSTM(h, h // 2, num_layers=L, bidirectional=True, batch_first=True)
            s.nrm = nn.ModuleList(nn.LayerNorm(h) for _ in range(1 if arch == "pointer" else L))
            s.pair, s.road, s.dep = mlp(3 * h, 1), mlp(2 * h + 3, 1), mlp(h, 1)
            s.box, s.fit = mlp(3, h), mlp(2 * h + 4, 1)
            s.share = mlp(h, 1)  # the share of a truck each stop uses: summed over a job, the number of trucks

        def encode(s, X, E, a, b, ctx=None):
            x, e = s.nx(X), s.ne(E)
            n = len(X)
            if arch == "gnn":
                deg = torch.bincount(b, minlength=n).clamp(min=1).unsqueeze(1)
                for msg, upd, nrm in zip(s.msg, s.upd, s.nrm):
                    m = msg(torch.cat([x[a], x[b], e], 1))
                    e = e + m
                    x = nrm(x + upd(torch.cat([x, torch.zeros_like(x).index_add_(0, b, m) / deg], 1)))
            elif arch == "transformer":  # multi-head self-attention within each job, written over the list of pairs
                ia, ib, d = ctx["fa"], ctx["fb"], h // HEADS
                for qkv, att, ff, n1, n2 in zip(s.qkv, s.att, s.ff, s.nrm, s.nrm2):
                    q, k, v = qkv(x).view(n, 3, HEADS, d).unbind(1)
                    w = (q[ia] * k[ib]).sum(-1) / d ** 0.5
                    top = torch.zeros(n, HEADS, device=x.device).index_reduce_(0, ia, w.detach(), "amax", include_self=False)
                    w = (w - top[ia]).exp()
                    w = w / torch.zeros(n, HEADS, device=x.device).index_add_(0, ia, w)[ia]
                    m = torch.zeros(n, HEADS, d, device=x.device).index_add_(0, ia, w.unsqueeze(-1) * v[ib])
                    x = n1(x + att(m.reshape(n, h)))
                    x = n2(x + ff(x))
            else:  # the stops of each job as one sequence, read in both directions
                pad = ctx["pad"]
                ok = pad >= 0
                seq = nn.utils.rnn.pack_padded_sequence(x[pad.clamp(min=0)], ok.sum(1).cpu(), batch_first=True, enforce_sorted=False)
                out = nn.utils.rnn.pad_packed_sequence(s.rnn(seq)[0], batch_first=True, total_length=pad.shape[1])[0]
                y = torch.zeros_like(x)
                y[pad[ok]] = out[ok]
                x = s.nrm[0](x + y)
            return x, e

        def pair_logit(s, x, e, a, b):
            return s.pair(torch.cat([x[a], x[b], e], 1)).squeeze(1)

        def road_km(s, x, xy, ia, ib):
            """Road km between any two stops: the straight line stretched by a learned detour (never shorter)."""
            d = xy[ia] - xy[ib]
            sl = d.norm(dim=1)
            g = torch.cat([x[ia] + x[ib], (x[ia] - x[ib]).abs(), (sl / 50).unsqueeze(1), d.abs() / 50], 1)
            return sl * (1 + F.softplus(s.road(g).squeeze(1)))

        def dep_km(s, x, straight):
            return straight * (1 + F.softplus(s.dep(x).squeeze(1)))

        def truck_share(s, x):
            return torch.sigmoid(s.share(x).squeeze(1))

        def fit_logit(s, bf, gi, ex):
            z = s.box(bf)
            n = len(ex)
            tot = torch.zeros(n, z.shape[1], device=z.device).index_add_(0, gi, z)
            top = torch.zeros(n, z.shape[1], device=z.device).index_reduce_(0, gi, z, "amax", include_self=False)
            return s.fit(torch.cat([tot, top, ex], 1)).squeeze(1)

    return torch, F, MT


def road_sample(g, Ds, cap=3000, seed=0):
    """Pairs of stops up to 100 km apart with their real road km (training targets only)."""
    n = len(g["X"])
    i, k = np.triu_indices(n, 1)
    ok = np.linalg.norm(g["xy"][i] - g["xy"][k], axis=1) <= 2 * R
    i, k = i[ok], k[ok]
    if len(i) > cap:
        pick = np.random.default_rng(seed).choice(len(i), cap, replace=False)
        i, k = i[pick], k[pick]
    return i, k, Ds[i + 1, k + 1].astype(np.float32)


def build(jobs, Ms, items, ref):
    """Per job: graph, pair labels (same truck in the reference plan), road targets, load-fit samples."""
    out = {}
    for jid, j in jobs.items():
        fp = footprints(items, j)
        s, xy, v, Ds, _ = split(j, Ms[jid])
        if len(s) < 2:
            continue
        g = mt_graph(j, s, fp)
        lab = np.full(len(j["v"]), -1)
        for ci, c in enumerate(ref[jid]["plan"]):
            lab[c] = ci
        pos = lab[s]
        g["y"] = (pos[g["pairs"][:, 0]] == pos[g["pairs"][:, 1]]).astype(np.float32)
        g["sh"] = (1 / np.bincount(pos, minlength=pos.max() + 1)[pos]).astype(np.float32)  # sums to the job's small trucks
        g["big"] = sum(len(big_trucks(x)) for x in j["v"][j["v"] > C14 + 1e-9])
        g["lb"] = lb_valid(j["v"])
        g["ri"], g["rk"], g["rkm"] = road_sample(g, Ds)
        g["dkm"] = Ds[0, 1:].astype(np.float32)
        fs = ref[jid]["fit"]
        g["fit"] = box_rows(fp, [f[0] for f in fs], [f[1] for f in fs]) + (np.array([f[2] for f in fs], np.float32),)
        out[jid] = g
    return out


def tensors(graphs, torch, dev):
    off, X, E, a, b, y, ri, rk, rkm, dep, dkm, xy, sh = 0, [], [], [], [], [], [], [], [], [], [], [], []
    bf, gi, ex, fy, goff = [], [], [], [], 0
    for g in graphs:
        X.append(g["X"]), E.append(g["E"]), a.append(g["a"] + off), b.append(g["b"] + off), y.append(np.tile(g["y"], 2))
        ri.append(g["ri"] + off), rk.append(g["rk"] + off), rkm.append(g["rkm"]), dep.append(g["dep"]), dkm.append(g["dkm"]), xy.append(g["xy"])
        sh.append(g["sh"])
        f = g["fit"]
        bf.append(f[0]), gi.append(f[1] + goff), ex.append(f[2]), fy.append(f[3])
        off, goff = off + len(g["X"]), goff + len(f[2])
    t = lambda z, dt=torch.float32: torch.as_tensor(np.concatenate(z), dtype=dt, device=dev)  # noqa: E731
    return dict(X=t(X), E=t(E), a=t(a, torch.long), b=t(b, torch.long), y=t(y), ri=t(ri, torch.long), rk=t(rk, torch.long), rkm=t(rkm),
                dep=t(dep), dkm=t(dkm), xy=t(xy), bf=t(bf), gi=t(gi, torch.long), ex=t(ex), fy=t(fy), sh=t(sh), ctx=context(graphs, torch, dev))


def train(graphs, epochs=400, seed=0, h=48, L=3, arch="gnn"):
    torch, F, MT = mt_class(h, L, arch)
    torch.manual_seed(seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    d = tensors(graphs, torch, dev)
    model = MT().to(dev)
    opt = torch.optim.AdamW(model.parameters(), 2e-3 if h <= 64 else 1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    # shortcut: above width 96 the load-fit loss sees a random 150k loads per step (the full batch needs more than the
    # GPU's 23 GB); train the full batch again on a larger GPU
    n_fit, cap = len(d["fy"]), 150_000 if h > 96 else 0
    for _ in range(epochs):
        x, e = model.encode(d["X"], d["E"], d["a"], d["b"], d["ctx"])
        bf, gi, ex, fy = d["bf"], d["gi"], d["ex"], d["fy"]
        if cap and n_fit > cap:
            keep = torch.zeros(n_fit, dtype=torch.bool, device=dev)
            keep[torch.randperm(n_fit, device=dev)[:cap]] = True
            box = keep[gi]
            bf, gi, ex, fy = bf[box], (keep.cumsum(0) - 1)[gi[box]], ex[keep], fy[keep]
        loss = (F.binary_cross_entropy_with_logits(model.pair_logit(x, e, d["a"], d["b"]), d["y"])
                + F.binary_cross_entropy_with_logits(model.fit_logit(bf, gi, ex), fy)
                + 5 * ((model.road_km(x, d["xy"], d["ri"], d["rk"]) - d["rkm"]).abs() / (d["rkm"] + 5)).mean()
                + 5 * ((model.dep_km(x, d["dep"]) - d["dkm"]).abs() / (d["dkm"] + 5)).mean()
                + 5 * F.mse_loss(model.truck_share(x), d["sh"]))
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
    return model.cpu().eval(), loss.item()


def auc(score, y):
    r = np.argsort(np.argsort(score)) + 1
    p = y > 0.5
    return float((r[p].sum() - p.sum() * (p.sum() + 1) / 2) / max(p.sum() * (~p).sum(), 1))


def infer(model, g):
    """Everything the model says about one job: pair probabilities, a full predicted road matrix (depot = 0)."""
    torch, _, _ = mt_class()
    with torch.no_grad():
        T = lambda z, dt=torch.float32: torch.as_tensor(z, dtype=dt)  # noqa: E731
        x, e = model.encode(T(g["X"]), T(g["E"]), T(g["a"], torch.long), T(g["b"], torch.long), context([g], torch))
        lg = model.pair_logit(x, e, T(g["a"], torch.long), T(g["b"], torch.long)).numpy()
        m = len(g["pairs"])
        p = 1 / (1 + np.exp(-(lg[:m] + lg[m:]) / 2))
        n = len(g["X"])
        i, k = np.triu_indices(n, 1)
        D = np.zeros((n + 1, n + 1), np.float32)
        km = model.road_km(x, T(g["xy"]), T(i, torch.long), T(k, torch.long)).numpy()
        D[i + 1, k + 1] = D[k + 1, i + 1] = km
        D[0, 1:] = D[1:, 0] = model.dep_km(x, T(g["dep"])).numpy()
        g["fleet"] = float(model.truck_share(x).sum())  # trucks for the small stops, with no solving
    return p, D


def model_fit(model, fp, s, thr=0.5):
    """The load-fit head as solve2 wants it."""
    torch, _, _ = mt_class()

    def fit(idx):
        groups = [s[r].tolist() for r in idx]
        with torch.no_grad():
            pr = [torch.sigmoid(model.fit_logit(*map(torch.as_tensor, box_rows(fp, groups, [t] * len(groups))))).numpy() for t in ("1t", "1.4t")]
        return (pr[0] >= thr) | (pr[1] >= thr), pr[0] < thr
    return fit


_models = {}


def get_model(k, tag=""):
    if (k, tag) not in _models:
        import torch
        torch.set_num_threads(1)
        ck = torch.load(OUT / f"ryry_mt_fold{k}{tag}.pt")
        m = mt_class(ck.get("h", 48), ck.get("L", 3), ck.get("arch", "gnn"))[2]()
        m.load_state_dict(ck["state"])
        _models[k, tag] = (m.eval(), ck)
    return _models[k, tag]


def run_e2e(task):
    """Plan one job twice without the packer or road data in the loop (the model; simple rules), then make each plan true
    with the real packer and score it on real roads."""
    jid, j, M, fp, fold, which, tag, *exact = task
    s, xy, v, Ds, area, P = small_setup(j, M, fp)
    row = dict(job=jid)
    if len(s) < 2:
        cl, tr, _ = settle(P, s, xy, v, area, [[i] for i in range(len(s))])
        row[which] = score3(j, M, s, cl, tr)
        row.update(shed=0, t_prep=0.0, t_solve=0.0)
        return row
    model, ck = get_model(fold, tag)
    t0 = time.time()
    if which == "model":
        g = mt_graph(j, s, fp)
        p, D = infer(model, g)
        cols, fit = gnn_columns(len(s), g["pairs"], p, top=8), model_fit(model, fp, s)
    else:  # no learning: nearest neighbours, a floor-coverage threshold, straight line x a fixed factor
        ll = np.r_[[DEPOT], j["ll"][s]]
        D = hav(ll[:, None], ll[None]) * ck["road_factor"]
        cols = knn_columns(xy, 8)
        cov = lambda idx, t: area[idx].sum(1) / AREA[t]  # noqa: E731
        fit = lambda idx: ((cov(idx, "1t") <= ck["theta"]) | (cov(idx, "1.4t") <= ck["theta"]), cov(idx, "1t") > ck["theta"])  # noqa: E731
    t1 = time.time()
    cl, info = solve2(xy, v, D, cols, limit=60, fit=fit)
    if cl is None:
        cl = [[i] for i in range(len(s))]
    if exact:  # the exact method on this planner's own fit and road estimates: every load listed, still no packer and no map server
        # skipped when over 40,000 loads remain, as in run_ref: beyond that the solver overruns its time limit
        better, _, row["proven"], _ = prove(xy, v, D, cl, fit=fit, limit=60, max_left=40_000)
        cl = better if len(better) < len(cl) else cl
    t2 = time.time()
    cl, tr, shed = settle(P, s, xy, v, area, cl)
    row[which] = score3(j, M, s, cl, tr)
    row.update(shed=shed, t_prep=round(t1 - t0, 3), t_solve=round(t2 - t1, 2), cols=info.get("cols"))
    return row


def run_alone(task):
    """The model with no solver: stops are merged from the most to the least likely pair while the company rules hold
    (the same loop as "GNN alone" in version 1), then the plan is made true with the real packer and scored on real roads."""
    from ryry import gnn_greedy
    jid, j, M, fp, fold, tag = task
    s, xy, v, Ds, area, P = small_setup(j, M, fp)
    cl = [[i] for i in range(len(s))]
    if len(s) >= 2:
        g = mt_graph(j, s, fp)
        cl = gnn_greedy(xy, v, g["pairs"], infer(get_model(fold, tag)[0], g)[0])
    cl, tr, shed = settle(P, s, xy, v, area, cl)
    return dict(job=jid, alone=score3(j, M, s, cl, tr), shed=shed)


def fold_of(jobs):
    ids = list(jobs)
    return {jid: i * FOLDS // len(ids) for i, jid in enumerate(ids)}


def main_train(tag="", h=48, L=3, epochs=400):
    jobs, Ms, ref = load(), matrices(), rows("v3ref")
    items = json.loads((OUT / "ryry_items.json").read_text())
    G = build(jobs, Ms, items, ref)
    fold, arch = fold_of(jobs), ARCH.get(tag, "gnn")
    torch, _, _ = mt_class()
    acc = dict(pair=[], pair_base=[], fit=[], fit_base=[], road=[], road_base=[], dep=[], dep_base=[], fleet=[], fleet_base=[], fleet_true=[])
    yy = dict(pair_s=[], pair_d=[], pair_y=[], fit_s=[], fit_c=[], fit_y=[])
    for k in range(FOLDS):
        tr, te = [G[j] for j in G if fold[j] != k], [j for j in G if fold[j] == k]
        model, loss = train(tr, epochs=epochs, h=h, L=L, arch=arch)
        # the simple rules, fitted on the same training jobs
        lbf = float(sum(g["lb"] * (g["sh"].sum() + g["big"]) for g in tr) / sum(g["lb"] ** 2 for g in tr))  # trucks ~ factor x lower bound
        cov, fy = np.concatenate([g["fit"][2][:, 0] for g in tr]), np.concatenate([g["fit"][3] for g in tr])
        thetas = np.linspace(0.5, 1.0, 51)
        theta = float(thetas[np.argmax([((cov <= t) == (fy > 0.5)).mean() for t in thetas])])
        sl = np.concatenate([np.linalg.norm(g["xy"][g["ri"]] - g["xy"][g["rk"]], axis=1) for g in tr])
        rkm = np.concatenate([g["rkm"] for g in tr])
        factor = float((sl * rkm).sum() / (sl * sl).sum())
        dfac = float(sum((g["dep"] * g["dkm"]).sum() for g in tr) / sum((g["dep"] ** 2).sum() for g in tr))
        torch.save(dict(state=model.state_dict(), theta=theta, road_factor=factor, dep_factor=dfac, h=h, L=L, arch=arch), OUT / f"ryry_mt_fold{k}{tag}.pt")
        for jid in te:
            g = G[jid]
            p, D = infer(model, g)
            true = g["sh"].sum() + g["big"]
            acc["fleet"].append(abs(g["fleet"] + g["big"] - true)), acc["fleet_base"].append(abs(lbf * g["lb"] - true)), acc["fleet_true"].append(true)
            yy["pair_s"].append(p), yy["pair_d"].append(-g["E"][:len(g["pairs"]), 0]), yy["pair_y"].append(g["y"])
            with torch.no_grad():
                fs = torch.sigmoid(model.fit_logit(*map(torch.as_tensor, g["fit"][:3]))).numpy()
            yy["fit_s"].append(fs), yy["fit_c"].append(g["fit"][2][:, 0]), yy["fit_y"].append(g["fit"][3])
            acc["fit"].append(((fs >= 0.5) == (g["fit"][3] > 0.5))), acc["fit_base"].append(((g["fit"][2][:, 0] <= theta) == (g["fit"][3] > 0.5)))
            s_l = np.linalg.norm(g["xy"][g["ri"]] - g["xy"][g["rk"]], axis=1)
            far = g["rkm"] >= 1
            acc["road"].append(np.abs(D[g["ri"] + 1, g["rk"] + 1] - g["rkm"])[far] / g["rkm"][far])
            acc["road_base"].append(np.abs(s_l * factor - g["rkm"])[far] / g["rkm"][far])
            acc["dep"].append(np.abs(D[0, 1:] - g["dkm"]) / np.maximum(g["dkm"], 1))
            acc["dep_base"].append(np.abs(g["dep"] * dfac - g["dkm"]) / np.maximum(g["dkm"], 1))
        print(f"fold {k}: loss {loss:.3f}, coverage threshold {theta:.2f}, road factor {factor:.3f}, depot factor {dfac:.3f}", flush=True)
    cat = lambda z: np.concatenate(z)  # noqa: E731
    params = sum(p.numel() for p in model.parameters())
    ft = np.array(acc["fleet_true"])
    heads = dict(
        params=params, kb=round(params * 4 / 1024), h=h, L=L, arch=arch,
        fleet=dict(mae=float(np.mean(acc["fleet"])), base_mae=float(np.mean(acc["fleet_base"])), err=float(np.median(np.array(acc["fleet"]) / ft)),
                   base_err=float(np.median(np.array(acc["fleet_base"]) / ft)), n=len(ft)),
        pair=dict(auc=auc(cat(yy["pair_s"]), cat(yy["pair_y"])), base_auc=auc(cat(yy["pair_d"]), cat(yy["pair_y"])), n=int(len(cat(yy["pair_y"])))),
        fit=dict(acc=float(cat(acc["fit"]).mean()), base_acc=float(cat(acc["fit_base"]).mean()), auc=auc(cat(yy["fit_s"]), cat(yy["fit_y"])),
                 base_auc=auc(-cat(yy["fit_c"]), cat(yy["fit_y"])), n=int(len(cat(yy["fit_y"]))), share_fit=float(cat(yy["fit_y"]).mean())),
        road=dict(err=float(np.median(cat(acc["road"]))), base_err=float(np.median(cat(acc["road_base"]))), mean=float(cat(acc["road"]).mean()),
                  base_mean=float(cat(acc["road_base"]).mean()), n=int(len(cat(acc["road"])))),
        dep=dict(err=float(np.median(cat(acc["dep"]))), base_err=float(np.median(cat(acc["dep_base"]))), mean=float(cat(acc["dep"]).mean()),
                 base_mean=float(cat(acc["dep_base"]).mean()), n=int(len(cat(acc["dep"])))))
    (OUT / f"ryry_mt_heads{tag}.json").write_text(json.dumps(heads))
    model, _ = train(list(G.values()), epochs=epochs, h=h, L=L, arch=arch)  # the model to ship: trained on every job
    torch.save(dict(state=model.state_dict(), h=h, L=L, arch=arch), OUT / f"ryry_mt{tag}.pt")
    print(json.dumps(heads, indent=1))


def summary():
    jobs = load()
    ref, mod, sim, cg = rows("v3ref"), rows("v3model"), rows("v3simple"), rows("cg")
    tot = lambda r, key, f: sum(x[key][f] for x in r.values())  # noqa: E731
    out = dict(jobs=len(ref), base=dict(trucks=sum(x["long"]["trucks"] for x in cg.values()), km=round(sum(x["long"]["km"] for x in cg.values()))),
               base_true=dict(trucks=tot(ref, "base_true", "trucks"), km=round(tot(ref, "base_true", "km")), shed=sum(x["base_shed"] for x in ref.values())),
               ref=dict(trucks=tot(ref, "ref", "trucks"), km=round(tot(ref, "ref", "km")), s=float(np.median([x.get("s", 0) for x in ref.values()]))))
    for name, r, key in [("model", mod, "model"), ("simple", sim, "simple"), ("model_x", rows("v3model_x"), "model"), ("simple_x", rows("v3simple_x"), "simple")] + \
            [(f"model{t}", rows(f"v3model{t}"), "model") for t in TAGS[1:]]:
        if len(r) == len(jobs):
            out[name] = dict(trucks=tot(r, key, "trucks"), km=round(tot(r, key, "km")), hours=round(tot(r, key, "hours")), shed=sum(x["shed"] for x in r.values()),
                             s=float(np.median([x["t_prep"] + x["t_solve"] for x in r.values()])), prep=float(np.median([x["t_prep"] for x in r.values()])))
    for t in TAGS + tuple(ARCH):
        if (OUT / f"ryry_mt_heads{t}.json").exists():
            out[f"heads{t}"] = json.loads((OUT / f"ryry_mt_heads{t}.json").read_text())
    # the encoders side by side at one size: ours ("" = the small GNN) and each rival
    out["rivals"] = {}
    for t in ("",) + tuple(ARCH):
        m, al = rows(f"v3model{t}"), rows(f"v3alone{t}")
        if f"heads{t}" in out and len(m) == len(jobs) and len(al) == len(jobs):
            gm, ga = rows("v3model"), rows("v3alone")
            cmp = lambda a, b, k: dict(fewer=sum(a[j][k]["trucks"] < b[j][k]["trucks"] for j in a), more=sum(a[j][k]["trucks"] > b[j][k]["trucks"] for j in a))  # noqa: E731
            out["rivals"][t or "_gnn"] = dict(
                arch=out[f"heads{t}"].get("arch", "gnn"), params=out[f"heads{t}"]["params"], solver=tot(m, "model", "trucks"), solver_km=round(tot(m, "model", "km")),
                solver_shed=sum(x["shed"] for x in m.values()), alone=tot(al, "alone", "trucks"), alone_km=round(tot(al, "alone", "km")),
                alone_shed=sum(x["shed"] for x in al.values()), vs_gnn_solver=cmp(gm, m, "model") if t else None, vs_gnn_alone=cmp(ga, al, "alone") if t else None,
                **{k: out[f"heads{t}"][k] for k in ("pair", "road", "dep", "fleet")})
    (OUT / "ryry_v3.json").write_text(json.dumps(out))
    print(json.dumps(out, indent=1))


def run_extra():
    """What the results page shows beyond the runs themselves -> ryry_v3x.json: the saved plans (rule-based, the 60 % plan,
    the reference plan) made physically true and priced; the reference plan's trucks for the job explorer; per-job
    truck counts; one real load's floor layout."""
    from pack import layout
    from ryry import CAP, FILL
    from ryry_cost import RATES, cost
    jobs, Ms, ref, base, cg, sim = load(), matrices(), rows("v3ref"), rows("base"), rows("cg"), rows("v3simple")
    items = json.loads((OUT / "ryry_items.json").read_text())
    sizes = {t: r for t in TAGS if len(r := rows(f"v3model{t}")) == len(jobs)}
    tag = min(sizes, key=lambda t: sum(x["model"]["trucks"] for x in sizes[t].values()))  # the size that plans best
    tot = {k: dict(trucks=0, km=0.0, hours=0.0, t14=0, shed=0, S1=0.0, S2=0.0) for k in ("rule_true", "base_true", "ref")}
    plans, per, ex = {}, [], None
    for n, (jid, j) in enumerate(jobs.items()):
        D = Ms[jid][0]
        fp = footprints(items, j)
        s, xy, v, Ds, area, P = small_setup(j, Ms[jid], fp)
        pos = {int(k): i for i, k in enumerate(s)}
        bigs = [(int(b), big_trucks(j["v"][b])) for b in np.flatnonzero(j["v"] > C14 + 1e-9)]
        row = dict(i=n, date=j["date"], n=len(j["v"]), real=base[jid]["real"]["trucks"], rule=base[jid]["rule"]["trucks"],
                   long=cg[jid]["long"]["trucks"], bound=cg[jid]["bound"], model=sizes[tag][jid]["model"]["trucks"], simple=sim[jid]["simple"]["trucks"])
        for name, plan in (("rule_true", base[jid]["plans"]["rule"]), ("base_true", cg[jid]["plans"]["long"]), ("ref", ref[jid]["plan"])):
            cl, tr, shed = settle(P, s, xy, v, area, [[pos[k] for k in c] for c in plan])
            sc = score3(j, Ms[jid], s, cl, tr)
            if name != "rule_true":  # recomputed today, these must equal what the runs saved
                assert sc["trucks"] == ref[jid][name]["trucks"] and abs(sc["km"] - ref[jid][name]["km"]) < 0.2, (jid, name, sc, ref[jid][name])
            row[name] = sc["trucks"]
            a = tot[name]
            a["shed"] += shed
            for k in ("trucks", "km", "hours", "t14"):
                a[k] += sc[k]
            trucks = [(t, s[c].tolist()) for c, t in zip(cl, tr)] + [(t, [b]) for b, ts in bigs for t in ts]
            for t, c in trucks:
                km = route_cost(D, np.array([c]))[0][0]
                for src in RATES:
                    a[src] += cost(RATES[src], t, km, len(c))
            if name == "ref":
                plans[jid] = dict(clusters=[s[c].tolist() for c in cl] + [[b] for b, _ in bigs], trucks=list(tr) + ["+".join(ts) for _, ts in bigs])
                for c, t in zip(cl, tr):  # a typical full load to draw: 1-ton, several addresses, every box size known
                    boxes = [q for i in s[c] for q in fp[i]]
                    cov = sum(w * d for w, d in boxes) / (FL["1t"][0] * FL["1t"][1])
                    known = all(items[j["ids"][i]]["frozen"] - items[j["ids"][i]]["vol"] <= 0.01 * items[j["ids"][i]]["frozen"] for i in s[c])
                    if t == "1t" and len(c) >= 3 and 6 <= len(boxes) <= 12 and 0.70 <= cov <= 0.84 and known:
                        rank = (-len(c), abs(cov - 0.77))
                        if ex is None or rank < ex[0]:
                            ex = (rank, n, j["date"], s[c], cov, float(v[c].sum()), route_cost(D, np.array([s[c]]))[1][0].tolist(), fp)
        per.append(row)
    _, n, date, c, cov, vol, order, fp = ex
    boxes = [q for i in c for q in fp[i]]
    owner = {}
    for i in c:  # boxes of one size are interchangeable, so a placed box is given to any stop that has that size
        for q in fp[i]:
            owner.setdefault(tuple(sorted(round(z, 3) for z in q)), []).append(order.index(int(i)))
    lay = layout(boxes, *FL["1t"], GAP)
    example = dict(job=n, date=date, W=FL["1t"][0], L=FL["1t"][1], gap=GAP, stops=len(c), cover=round(cov, 3), fill=round(vol / (CAP["1t"] / FILL), 3),
                   boxes=[[round(x, 1), round(y, 1), round(w, 1), round(d, 1), owner[tuple(sorted((round(w, 3), round(d, 3))))].pop()] for x, y, w, d in lay])
    wins = lambda a, b: dict(fewer=sum(x[a] < x[b] for x in per), more=sum(x[a] > x[b] for x in per), same=sum(x[a] == x[b] for x in per))  # noqa: E731
    out = dict(model_tag=tag, model_vs_simple=wins("model", "simple"), ref_vs_rule_true=wins("ref", "rule_true"), totals={k: {f: round(x, 1) if f in ("km", "hours") else round(x) for f, x in a.items()} for k, a in tot.items()},
               jobs=per, example=example, plans=plans)
    (OUT / "ryry_v3x.json").write_text(json.dumps(out))
    print(json.dumps(dict(model_tag=tag, totals=out["totals"], example={k: x for k, x in example.items() if k != "boxes"}, boxes=len(example["boxes"])), indent=1))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "extra":
        run_extra()
    elif mode == "ref":
        jobs, Ms, cg = load(), matrices(), rows("cg")
        items = json.loads((OUT / "ryry_items.json").read_text())
        z = np.load(OUT / "ryry_gnn_oof.npz")
        P0 = {str(j): z[f"p{i}"] for i, j in enumerate(z["jobs"])}
        pool_run(run_ref, [(jid, j, Ms[jid], P0.get(jid, np.zeros(0)), cg[jid]["plans"]["long"], footprints(items, j)) for jid, j in jobs.items()], "v3ref")
    elif mode == "train":  # train            -> the small model;   train _big 192 6 -> a larger one, saved with that tag
        a = sys.argv[2:]
        main_train(*(a[:1] + [int(x) for x in a[1:]]))
    elif mode == "alone":  # alone [tag] -> ryry_v3alone{tag}.jsonl
        jobs, Ms = load(), matrices()
        items = json.loads((OUT / "ryry_items.json").read_text())
        fold, tag = fold_of(jobs), sys.argv[2] if len(sys.argv) > 2 else ""
        pool_run(run_alone, [(jid, j, Ms[jid], footprints(items, j), fold[jid], tag) for jid, j in jobs.items()], f"v3alone{tag}")
    elif mode in ("e2e", "e2ex"):  # e2ex: the same test with the exact method added -> ryry_v3model_x.jsonl, ryry_v3simple_x.jsonl
        jobs, Ms = load(), matrices()
        items = json.loads((OUT / "ryry_items.json").read_text())
        fold, tag, x = fold_of(jobs), sys.argv[2] if len(sys.argv) > 2 else "", ("_x",) * (mode == "e2ex")
        for which in ("model", "simple") if x or not tag else ("model",):
            pool_run(run_e2e, [(jid, j, Ms[jid], footprints(items, j), fold[jid], which, tag, *x) for jid, j in jobs.items()], f"v3{which}{tag}{''.join(x)}")
    if mode in ("summary", "e2e", "e2ex", "alone"):
        summary()
