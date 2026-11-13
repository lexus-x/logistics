"""Audit of the load rule: do the loads physically fit on the truck floor with no stacking?
  python -I cluster/ryry_load.py                              # real dispatch and the 60 % plan
  RULE_FILL=0.7 python -I cluster/ryry_load.py rule_fill70    # a plan made under another load limit
Results -> cluster/results/ryry_load.json (one entry per plan), table printed. Boxes per stop come from ryry_items.py.
A box stands upright and may turn 90 degrees; height is not checked (0.3 % of boxes are taller than a 1-ton's 160 cm).
Where a stop's boxes cover less volume than the frozen set says (a product with no known box), a filler box of the
missing volume, 122 cm tall (the median box), is added. gap = clearance kept between neighbouring boxes, in cm."""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
from pack import fits, key  # noqa: E402
from ryry import FILL, OUT, TRUCKS, load, rows, with_big  # noqa: E402
from ryry_cost import TONS, trucks_of  # noqa: E402

GAPS = (0, 5, 10)


def floor(truck):
    """(width, length, height) in cm of the truck's box; sizes read from the real dispatch's labels map to the next size up."""
    if truck not in TRUCKS:
        try:
            tons = float(truck.split("t")[0])
            truck = next((k for t, k in TONS if tons <= t), "11t-9.7m")
        except ValueError:
            return None
    return TRUCKS[truck]


def footprints(items, j):
    """Per stop of the job: [(w, d)] in cm, one per box."""
    out = []
    for sid in j["ids"]:
        it = items[sid]
        fp = [(w, d) for w, d, _, q in it["boxes"] for _ in range(math.ceil(q))]
        missing = it["frozen"] - it["vol"]
        if missing > 0.01 * it["frozen"]:  # a product with no known box size
            side = 100 * math.sqrt(missing / 1.22)
            fp.append((side, side))
        out.append(fp)
    return out


def audit(name):
    jobs, items = load(), json.loads((OUT / "ryry_items.json").read_text())
    src = None if name == "real" else rows(name if name.startswith("rule_") else {"long": "cg"}.get(name, name))
    which = "plan" if name.startswith("rule_") else name
    res = {g: dict(fit=0, no=0, undecided=0) for g in GAPS}
    cache = json.loads(c.read_text()) if (c := OUT / "pack_cache.json").exists() else {}  # exact answers from pack_exact.py
    todo = json.loads(t.read_text()) if (t := OUT / "pack_todo.json").exists() else {}
    cover, fill, several, by_truck = [], [], 0, {}
    for jid, j in jobs.items():
        fp = footprints(items, j)
        if name == "real":
            g = {}
            for i, r in enumerate(j["real"]):
                g.setdefault(r if r >= 0 else -1 - i, []).append(i)
            clusters = list(g.values())
        else:
            clusters = with_big(j, src[jid]["plans"][which])
        seen = {}
        for truck, c in trucks_of(j, name, clusters):
            seen[tuple(c)] = seen.get(tuple(c), 0) + 1
        for truck, c in trucks_of(j, name, clusters):
            box = floor(truck)
            if seen[tuple(c)] > 1 or box is None:  # a stop spread over several trucks, or an unreadable label
                several += 1
                continue
            W, L, H = box
            boxes = [b for i in c for b in fp[i]]
            cov = sum(w * d for w, d in boxes) / (W * L)
            cover.append(cov)
            fill.append(j["v"][c].sum() / (W * L * H / 1e6))
            t = by_truck.setdefault("1-ton" if (W, L) == TRUCKS["1t"][:2] else "1.4-ton" if (W, L) == TRUCKS["1.4t"][:2] else "bigger",
                                    {g: [0, 0] for g in GAPS})
            for g in GAPS:
                f = fits(boxes, W, L, g)
                if f is None:
                    k = key(boxes, W, L, g)
                    f = cache.get(k)
                    if f is None:
                        todo[k] = [W, L, g, boxes]
                res[g]["fit" if f else "no" if f is False else "undecided"] += 1
                t[g][0] += f is True
                t[g][1] += 1
    n = len(cover)
    out = dict(plan=name, load_limit=FILL, loads=n, skipped=several, cover_p50=round(float(np.median(cover)), 3),
               cover_p90=round(float(np.quantile(cover, .9)), 3), fill_p50=round(float(np.median(fill)), 3),
               fill_p90=round(float(np.quantile(fill, .9)), 3), over_floor=round(float(np.mean(np.array(cover) > 1)), 4),
               gaps={str(g): res[g] for g in GAPS}, by_truck={t: {str(g): v for g, v in d.items()} for t, d in by_truck.items()})
    (OUT / "pack_todo.json").write_text(json.dumps(todo))
    f = OUT / "ryry_load.json"
    allr = json.loads(f.read_text()) if f.exists() else {}
    allr[name] = out
    f.write_text(json.dumps(allr))
    print(f"{name} (load limit {FILL:.0%}): {n} loads checked, {several} skipped. Floor covered: median {out['cover_p50']:.0%}, "
          f"p90 {out['cover_p90']:.0%}; footprints bigger than the floor: {out['over_floor']:.1%}. Volume filled: median {out['fill_p50']:.0%}, p90 {out['fill_p90']:.0%}")
    for g in GAPS:
        r = res[g]
        print(f"  clearance {g:2d} cm: fit {100 * r['fit'] / n:5.1f} %, proved not to fit {100 * r['no'] / n:5.1f} %, undecided {100 * r['undecided'] / n:5.1f} %   "
              + "  ".join(f"{t}: {100 * d[g][0] / d[g][1]:.0f} % of {d[g][1]}" for t, d in sorted(by_truck.items())))


if __name__ == "__main__":
    for plan in sys.argv[1:] or ["real", "long"]:
        audit(plan)
