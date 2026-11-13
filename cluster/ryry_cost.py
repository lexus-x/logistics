"""Estimated truck-hire cost of each saved plan, from public broker list prices (output/reports/freight_rates_kr.md).
  python -I cluster/ryry_cost.py   # table -> cluster/results/ryry_cost.md
The prices are undated list prices, not the company's contract rates: good for comparing plans, not for budgeting."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
from ryry import C14, OUT, big_trucks, labels, load, matrices, route_cost, rows, with_big  # noqa: E402
from ryry_viz import real_truck  # noqa: E402

# won = base + per road km, a straight-line fit to each source's distance bands (50-500 km)
RATES = {"S1": {"1t": (46100, 402), "1.4t": (54400, 416), "2.5t": (62500, 536), "3.5t": (70700, 565), "5t": (90700, 565),
                "5t+": (103000, 605), "11t": (124000, 731)},
         "S2": {"1t": (36800, 403), "1.4t": (46800, 403), "2.5t": (60700, 524), "3.5t": (68000, 539), "5t": (82700, 565),
                "5t+": (96500, 595), "11t": (125000, 713)}}
TONS = [(1, "1t"), (1.4, "1.4t"), (2.5, "2.5t"), (3.5, "3.5t"), (5, "5t")]
NAMES = {"real": "Real dispatch", "rule": "Rule-based (Ryry's paper)", "kmeans": "k-means", "agg": "Agglomerative", "gnn": "GNN alone",
         "opt": "Optimizer", "knn8": "Optimizer, 8 nearest", "gnn_opt": "GNN + optimizer", "long": "GNN + optimizer, long run"}


def cost(rates, truck, km, stops):
    """One truck's hire: distance fare plus a fee for each address after the first."""
    if truck not in rates:  # "11t-9.7m", or a size read from the real dispatch's free-text label
        try:
            tons = float(truck.split("t")[0])
            truck = next((k for t, k in TONS if tons <= t), "11t")
        except ValueError:
            truck = "1t"  # shortcut: an unreadable label counts as a 1-ton, the most common truck
    base, per_km = rates[truck]
    # extra-address fee per the one public source that lists it; its unit is unlabelled (read as 10,000 won)
    fee = 10000 if truck in ("1t", "1.4t") else 30000 if truck == "11t" else 20000
    return base + per_km * km + fee * (stops - 1)


def trucks_of(j, m, clusters):
    """[(truck, cluster)] with one entry per truck driven."""
    if m == "real":
        return [(real_truck(j["truck"][c[0]]), c) for c in clusters]
    small = [c for c in clusters if j["v"][c].sum() <= C14 + 1e-9]
    lab = dict(zip(map(tuple, small), labels(small, j["v"])))
    return [(t, c) for c in clusters for t in ([lab[tuple(c)]] if tuple(c) in lab else big_trucks(j["v"][c[0]]))]


def main():
    jobs, Ms = load(), matrices()
    src = dict(rule=rows("base"), kmeans=rows("base"), agg=rows("agg"), gnn=rows("gnn"), opt=rows("base"), knn8=rows("knn8"),
               gnn_opt=rows("gnn"), long=rows("cg"))
    tot = {m: dict(trucks=0, km=0.0, S1=0.0, S2=0.0) for m in NAMES}
    for jid, j in jobs.items():
        D = Ms[jid][0]
        real = {}
        for i, r in enumerate(j["real"]):
            real.setdefault(r if r >= 0 else -1 - i, []).append(i)
        plans = {"real": list(real.values()), **{m: with_big(j, s[jid]["plans"][m]) for m, s in src.items() if jid in s}}
        for m, cl in plans.items():
            for truck, c in trucks_of(j, m, cl):
                km = route_cost(D, np.array([c]))[0][0]
                tot[m]["trucks"] += 1
                tot[m]["km"] += km
                for s in RATES:
                    tot[m][s] += cost(RATES[s], truck, km, len(c))
    stops = sum(len(j["v"]) for j in jobs.values())
    r = tot["real"]
    lines = ["Estimated hire cost from public list prices (two sources). Won, all 97 jobs.", "",
             "| method | trucks | road km | cost, source 1 | vs real | cost, source 2 | vs real | per stop (source 1) |", "|---|---|---|---|---|---|---|---|"]
    for m, t in tot.items():
        if t["trucks"]:
            lines.append(f"| {NAMES[m]} | {t['trucks']:,} | {t['km']:,.0f} | {t['S1'] / 1e6:,.1f} M | {100 * (t['S1'] / r['S1'] - 1):+.1f} % | "
                         f"{t['S2'] / 1e6:,.1f} M | {100 * (t['S2'] / r['S2'] - 1):+.1f} % | {t['S1'] / stops:,.0f} |")
    lines += ["", "List prices, undated, not contract rates. Fare = base + per km by truck size, plus 10,000-30,000 won per extra address. "
              "No waiting, loading-help, toll or night fees. The real dispatch's trucks are read from its free-text labels."]
    (OUT / "ryry_cost.md").write_text("\n".join(lines) + "\n")
    (OUT / "ryry_cost.json").write_text(json.dumps(dict(stops=stops, rate_1t=RATES["S1"]["1t"], methods={m: {k: round(x) for k, x in t.items()} for m, t in tot.items() if t["trucks"]})))  # for the results page
    print("\n".join(lines))


if __name__ == "__main__":
    main()
