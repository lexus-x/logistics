"""Build the local results page for Ryry's jobs: python -I cluster/ryry_viz.py, then
python3 -m http.server 8777 --bind 127.0.0.1 --directory output/ryry_viz   # port 8765 is taken by another local site
The page holds stop coordinates (personal data): local only, never deploy it. Road shapes come from the local OSRM server."""
import csv
import json
import re
import shutil
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
from ryry import (C14, CAP, DATA, DEPOT, FILL, OSRM, OUT, ROOT, big_trucks, features, graphs_for, labels, load, matrices,  # noqa: E402
                  radius, route_cost, rows, split, with_big)

DST = ROOT / "output/ryry_viz"
METHODS = ["real", "rule", "kmeans", "gnn", "opt", "gnn_opt"]
KOREA = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"


def real_truck(label):
    """The driven truck's size from its free-text label (e.g. '1톤 카고(리프트X)' -> 1t)."""
    m = re.match(r"\s*([\d.]+)\s*톤", label or "")
    return {"1": "1t", "1.4": "1.4t"}.get(m.group(1), m.group(1) + "t") if m else "?"


def place(r):
    """Province + city only (e.g. 경기 화성시), never the street: postcodes dropped, the second word kept only if it is a city, county or district."""
    for src in (r.get("kakao_address_name", ""), r.get("address_normalized", "")):
        t = [x for x in src.split() if not re.match(r"^\(?\d", x)]
        if t:
            return " ".join(t[:1] + [x for x in t[1:2] if x[-1] in "시군구"])
    return ""


def geom(pts):
    """Road shape through pts (lat, lng) as an encoded polyline (precision 5), from the local server."""
    q = ";".join(f"{lng:.6f},{lat:.6f}" for lat, lng in pts)
    with urllib.request.urlopen(f"{OSRM}/route/v1/driving/{q}?overview=simplified&geometries=polyline", timeout=120) as r:
        t = json.load(r)
    return t["routes"][0]["geometry"] if t["code"] == "Ok" else ""


def v2(jobs, base, gnn, cg):
    """Results added after the first release: cost, the depot check, the price of each rule, the forward test.
    Each part is None (or done=False) until its run has finished, and the page says so."""
    from ryry_rules import VARIANTS, drop
    out = {name: json.loads(f.read_text()) if (f := OUT / f"ryry_{name}.json").exists() else None for name in ("cost", "depot")}
    ctl, out["rules"] = rows("rule_control"), []
    if len(ctl) == len(jobs):
        tot = lambda r, k: sum(x["plan"][k] for x in r.values())  # noqa: E731
        bound = lambda r: sum(x["bound"] for x in r.values())  # noqa: E731
        for name, (_, label) in VARIANTS.items():
            r = rows(f"rule_{name}")
            row = dict(name=name, label=label, done=len(r) == len(jobs))
            if row["done"]:
                row.update(trucks=tot(r, "trucks"), km=round(tot(r, "km")), bound=bound(r), saved=tot(ctl, "trucks") - tot(r, "trucks"),
                           bound_drop=drop(ctl, r), improved=sum(r[j]["plan"]["trucks"] < ctl[j]["plan"]["trucks"] for j in r))
            out["rules"].append(row)
    test = [j for j in jobs if jobs[j]["date"] >= "2026-07-01"]
    fwd, knn8 = rows("fwd"), rows("knn8")
    out["forward"] = None
    if test and all(j in fwd for j in test) and all(j in knn8 for j in test):
        t = lambda src, m: sum(src[j][m]["trucks"] for j in test)  # noqa: E731
        out["forward"] = dict(train=len(jobs) - len(test), test=len(test), real=sum(base[j]["real"]["trucks"] for j in test),
                              rule=t(base, "rule"), knn8=t(knn8, "knn8"), fwd=t(fwd, "gnn_opt"), cv=t(gnn, "gnn_opt"),
                              bound=sum(cg[j]["bound"] for j in test))
    return out


def gnn_stats(jobs, Ms, base, gnn, oof):
    """What the stage-1 GNN adds, for the page: its held-out pair scores, and the short list and solve time with and without it."""
    from ryry_v3 import auc
    G = graphs_for(jobs, Ms, base)
    y, p = (np.concatenate([a[j] for j in G if j in oof]) for a in ({j: g["y"] for j, g in G.items()}, oof))
    med = lambda r, k: float(np.median([x[k] if "_s" in k else x[k]["cols"] for x in r.values()]))  # noqa: E731
    return dict(pairs=len(y), acc=float(((p > 0.5) == (y > 0.5)).mean()), base_acc=float(1 - y.mean()), auc=float(auc(p, y)),
                cols=[med(base, "opt_info"), med(gnn, "gnn_opt_info")], s=[med(base, "opt_s"), med(gnn, "gnn_opt_s")],
                limit=[sum(x[k]["status"] == 1 for x in r.values()) for r, k in ((base, "opt_info"), (gnn, "gnn_opt_info"))])


def main():
    jobs, Ms, base, gnn, cg = load(), matrices(), rows("base"), rows("gnn"), rows("cg")
    with open(DATA, encoding="utf-8-sig", newline="") as f:
        city = {r["experiment_stop_id"]: place(r) for r in csv.DictReader(f)}
    v3x = json.loads(f.read_text()) if (f := OUT / "ryry_v3x.json").exists() else None  # ryry_v3.py extra
    v3ref = rows("v3ref") if v3x else {}
    extra = {"agg": rows("agg"), "knn8": rows("knn8"), "long": cg,  # optional runs, shown once complete
             "v3": {j: dict(v3=r["ref"]) for j, r in v3ref.items()}}
    methods = ["real", "rule", "kmeans", "agg", "gnn", "opt", "knn8", "gnn_opt", "long", "v3"]
    methods = [m for m in methods if m in METHODS or len(extra[m]) == len(jobs)]
    lbp = {j: cg[j]["bound"] if j in cg else base[j]["lb_valid"] for j in jobs}
    z = np.load(OUT / "ryry_gnn_oof.npz")
    oof = {str(j): z[f"p{i}"] for i, j in enumerate(z["jobs"])}
    (DST / "jobs").mkdir(parents=True, exist_ok=True)
    DST.chmod(0o700)
    if not (DST / "korea.json").exists():  # public province outlines (KOSTAT 2013); a download, nothing is sent
        urllib.request.urlretrieve(KOREA, DST / "korea.json")
    shutil.copy(Path(__file__).with_name("ryry_viz.html"), DST / "index.html")
    shutil.copytree(ROOT / "riri-form/public/fonts", DST / "fonts", dirs_exist_ok=True)  # Barlow (OFL), same type as Ryry's form
    src = {m: extra.get(m) or (gnn if m.startswith("gnn") else base) for m in methods}
    summary = dict(depot=DEPOT, methods={}, jobs=[])
    for m in methods:
        rs = [src[m][j][m] for j in jobs]
        summary["methods"][m] = dict(trucks=sum(r["trucks"] for r in rs), km=round(sum(r["km"] for r in rs)),
                                     hours=round(sum(r["hours"] for r in rs)), t14=sum(r.get("t14", 0) for r in rs),
                                     breaks=sum(r.get("breaks", 0) for r in rs),
                                     at_bound=sum(src[m][j][m]["trucks"] <= lbp[j] for j in jobs),
                                     solve_max=max((src[m][j].get(f"{m}_s", 0) for j in jobs), default=0))
    summary.update(lb_valid=sum(base[j]["lb_valid"] for j in jobs), lb_ryry=sum(base[j]["lb_ryry"] for j in jobs),
                   lb_proven=sum(lbp.values()), proven=len(cg) == len(jobs), exact_jobs=sum(bool(r["cg"].get("exact")) for r in cg.values()),
                   stops=sum(len(j["v"]) for j in jobs.values()), gnn=gnn_stats(jobs, Ms, base, gnn, oof))
    pool = ThreadPoolExecutor(16)
    for i, (jid, j) in enumerate(jobs.items()):
        D, T = Ms[jid]
        ll = j["ll"]
        out = dict(date=j["date"], n=len(ll), lb=lbp[jid], lbr=base[jid]["lb_ryry"],
                   cols=dict(opt=base[jid].get("opt_info", {}).get("cols"), gnn=gnn[jid].get("gnn_opt_info", {}).get("cols")),
                   stops=[[round(a, 4), round(b, 4), round(float(v), 3), city.get(sid, "")] for (a, b), v, sid in zip(ll, j["v"], j["ids"])],
                   methods={})
        pairs = set()
        for m in methods:
            if m == "real":
                g = {}
                for k, r in enumerate(j["real"]):
                    g.setdefault(r if r >= 0 else -1 - k, []).append(k)
                cl = list(g.values())
                tr = [real_truck(j["truck"][c[0]]) for c in cl]
            elif m == "v3":  # the plan with the physical fit check: its trucks come from the real packer, not from volume
                cl, tr = v3x["plans"][jid]["clusters"], v3x["plans"][jid]["trucks"]
            else:
                cl = with_big(j, src[m][jid]["plans"][m])
                small = [c for c in cl if j["v"][c].sum() <= C14 + 1e-9]
                lab = dict(zip(map(tuple, small), labels(small, j["v"])))
                tr = [lab.get(tuple(c)) or "+".join(big_trucks(j["v"][c[0]])) for c in cl]
            cs = []
            for c, t in zip(cl, tr):
                km, o = route_cost(D, np.array([c]))
                o = o[0].tolist()
                path = np.r_[0, np.array(o) + 1]
                box = sum(CAP[x] / FILL for x in t.split("+")) if all(x in CAP for x in t.split("+")) else None
                cs.append(dict(s=o, t=t, km=round(float(km[0]), 1), h=round(float(T[path[:-1], path[1:]].sum()), 2),
                               lk=[round(float(x), 1) for x in D[path[:-1], path[1:]]],  # km of each leg, depot first
                               v=round(float(j["v"][c].sum()), 2), fill=round(float(j["v"][c].sum() / box), 3) if box else None,
                               r=round(float(radius(j["xy"], np.array([c]))[0]), 1)))
                pairs.update(zip(o[:-1], o[1:]))
            cs.sort(key=lambda c: c["lk"][0])  # truck 1 = the nearest first stop, so the list reads outward from the depot
            out["methods"][m] = dict(trucks=src[m][jid][m]["trucks"], km=src[m][jid][m]["km"], clusters=cs)
        firsts = sorted({c["s"][0] for mm in out["methods"].values() for c in mm["clusters"]})
        legs = sorted(pairs)
        gf = pool.map(lambda k: geom([DEPOT, ll[k]]), firsts)
        gl = pool.map(lambda ab: geom([ll[ab[0]], ll[ab[1]]]), legs)
        out["first"] = dict(zip(map(str, firsts), gf))
        out["legs"] = {f"{a}-{b}": g for (a, b), g in zip(legs, gl)}
        s, xy, v, Ds, _ = split(j, Ms[jid])
        if jid in oof and len(s) >= 2:
            pr = features(xy, v, Ds)["pairs"]
            out["edges"] = [[int(s[a]), int(s[b]), round(float(p), 2)] for (a, b), p in zip(pr, oof[jid]) if p >= 0.05]
        (DST / f"jobs/{i}.json").write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
        summary["jobs"].append(dict(i=i, date=j["date"], n=len(ll), lb=out["lb"],
                                    trucks={m: out["methods"][m]["trucks"] for m in methods},
                                    km={m: out["methods"][m]["km"] for m in methods}))
        print(i, jid, len(firsts), len(legs), flush=True)
    summary["v2"] = v2(jobs, base, gnn, cg)
    v3f, ldf = OUT / "ryry_v3.json", OUT / "ryry_load.json"  # version 3: real loading and the multi-task model (ryry_v3.py)
    summary["v3"] = dict(json.loads(v3f.read_text()), load=json.loads(ldf.read_text())) if v3f.exists() and ldf.exists() else None
    if summary["v3"] and v3x:
        summary["v3"]["x"] = {k: v for k, v in v3x.items() if k != "plans"}
        # fewest possible with the floor check: shown by the exact step, or equal to the minimum without that check
        summary["v3"]["proven"] = sum(bool(r["info"].get("proven")) or r["ref"]["trucks"] <= lbp[j] for j, r in v3ref.items())
    (DST / "summary.json").write_text(json.dumps(summary, separators=(",", ":")))
    for f in DST.rglob("*.json"):
        f.chmod(0o600)
    print("built", DST)


if __name__ == "__main__":
    main()
