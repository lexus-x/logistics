"""Figures and numbers for the LogisticSolver 2026 report (Version 1 results, real depot).
  .venv/bin/python -I competition/make_figs.py   -> competition/figs/*.svg|png, competition/numbers.json
Reads only saved results and the stop table. The national map shows stops as unlabeled dots (the user allowed it);
nothing else in the output holds a stop location. The example job is synthetic."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "cluster"))
from exact import knn_columns  # noqa: E402
from ryry import C, C14, DEPOT, OUT, R, load, route_cost, rows, solve2  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

for f in (HERE / "fonts").glob("Barlow-*.ttf"):
    font_manager.fontManager.addfont(str(f))
FIG = HERE / "figs"
FIG.mkdir(exist_ok=True)

# palette: validated (dataviz validator, light surface): ours blue, existing practice orange; grey = other baselines
BLUE, ORANGE, GREY, NAVY, INK, MUTED, GRID, SKY = "#2f6fdb", "#cf7f2e", "#a3acb8", "#1d3f86", "#1c2430", "#5b6676", "#e3e8ef", "#eef4fb"
plt.rcParams.update({"font.family": "Barlow", "font.size": 9.5, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "semibold", "axes.titlesize": 10.5, "axes.titlecolor": INK, "axes.titlelocation": "left",
                     "svg.fonttype": "path", "figure.dpi": 100, "savefig.bbox": "tight", "savefig.pad_inches": 0.04})


def save(fig, name):
    fig.savefig(FIG / f"{name}.svg")
    fig.savefig(FIG / f"{name}.png", dpi=220)
    plt.close(fig)


S = json.loads((ROOT / "output/ryry_viz/summary.json").read_text())
M = S["methods"]
N = {}  # every number the report quotes

# ---- data ----
jobs = load()
sizes = np.array([len(j["v"]) for j in jobs.values()])
vols = np.concatenate([j["v"] for j in jobs.values()])
dates = sorted(j["date"] for j in jobs.values())
N["data"] = dict(jobs=len(jobs), stops=int(sizes.sum()), days=len(set(dates)), first=dates[0], last=dates[-1],
                 per_job_min=int(sizes.min()), per_job_med=int(np.median(sizes)), per_job_max=int(sizes.max()),
                 big=int((vols > C14 + 1e-9).sum()), over_1t=int((vols > C + 1e-9).sum()), vol_med=round(float(np.median(vols)), 2),
                 vol_total=round(float(vols.sum())), cap_1t=round(C, 2), cap_14t=round(C14, 2))

# ---- results (V1) ----
names = {"real": "Real dispatch", "kmeans": "k-means", "agg": "Agglomerative", "rule": "Rule-based (our earlier method)",
         "opt": "Optimizer, 15-nearest list", "gnn_opt": "GNN + optimizer", "long": "GNN + optimizer, long run (ours)"}
lb = S["lb_proven"]
N["bench"] = json.loads((HERE / "benchmark/results.json").read_text())  # competition/benchmark.py
N["methods"] = {m: dict(name=names[m], trucks=M[m]["trucks"], km=M[m]["km"], hours=M[m]["hours"], t14=M[m]["t14"],
                        breaks=M[m]["breaks"], at_bound=M[m]["at_bound"], gap=round(100 * (M[m]["trucks"] / lb - 1), 1),
                        vs_real=round(100 * (M[m]["trucks"] / M["real"]["trucks"] - 1), 1)) for m in names}
N["lb"], N["lb_simple"] = lb, S["lb_valid"]
cg = rows("cg")
gap = [r["long"]["trucks"] - r["bound"] for r in cg.values()]
N["proof"] = dict(optimal=sum(g == 0 for g in gap), plus1=sum(g == 1 for g in gap), plus2=sum(g == 2 for g in gap),
                  exact=sum(bool(r["cg"].get("exact")) for r in cg.values()),
                  long_s_med=round(float(np.median([r["long_s"] for r in cg.values()])), 1),
                  long_s_max=round(max(r["long_s"] for r in cg.values())),
                  prove_s_med=round(float(np.median([r["long_info"]["prove"].get("s", r["long_info"]["prove"]["lp_s"]) for r in cg.values() if r["long_info"].get("prove")])), 1),
                  loads_med=int(np.median([r["long_info"]["prove"]["loads"] for r in cg.values() if r["long_info"].get("prove")])))
N["gnn"] = S["gnn"]
N["gnn"]["params"] = 137857
base, gnn = rows("base"), rows("gnn")
N["speed"] = dict(opt_max=round(max(r["opt_s"] for r in base.values())), gnn_max=round(max(r["gnn_opt_s"] for r in gnn.values())),
                  opt_fallback=sum(bool(r["opt_info"].get("fallback")) for r in base.values()),
                  gnn_fallback=sum(bool(r["gnn_opt_info"].get("fallback")) for r in gnn.values()))
V = S["v2"]
N["forward"], N["depot"] = V["forward"], V["depot"]
cost = V["cost"]["methods"]
N["cost"] = {m: dict(S1=cost[m]["S1"], S2=cost[m]["S2"]) for m in names}
# CO2: 1-ton diesel truck, 8.8 km/L (Asia Economy 2025); IPCC 2006 diesel default 74.1 t CO2/TJ, NCV 43.0 TJ/Gg, density 0.84 kg/L
KG_L = 74.1e-3 * 43.0 * 0.84  # kg CO2 per litre = t/TJ * TJ/Gg * kg/L
KG_KM = KG_L / 8.8
N["co2"] = dict(kg_per_l=round(KG_L, 2), kg_per_km=round(KG_KM, 3),
                **{m: round(M[m]["km"] * KG_KM / 1000, 1) for m in names})
YEAR = 365 / ((np.datetime64(dates[-1]) - np.datetime64(dates[0])).astype(int) + 1)  # scale the observed period to a year
N["year_factor"] = round(float(YEAR), 2)
best = "gnn_opt"  # the final Version 1 planner
N["save"] = {ref: dict(trucks=M[ref]["trucks"] - M[best]["trucks"], km=M[ref]["km"] - M[best]["km"], hours=M[ref]["hours"] - M[best]["hours"],
                       won=cost[ref]["S1"] - cost[best]["S1"], co2_t=round((M[ref]["km"] - M[best]["km"]) * KG_KM / 1000, 1))
             for ref in ("real",)}
for ref in ("real",):
    N["save"][ref]["year"] = {k: round(v * YEAR) if k != "co2_t" else round(v * YEAR, 1) for k, v in N["save"][ref].items()}
pct = lambda a, b: round(100 * (a / b - 1), 1)  # noqa: E731
N["pct"] = {ref: dict(trucks=pct(M[best]["trucks"], M[ref]["trucks"]), km=pct(M[best]["km"], M[ref]["km"]),
                      hours=pct(M[best]["hours"], M[ref]["hours"]), cost=pct(cost[best]["S1"], cost[ref]["S1"]),
                      co2=pct(M[best]["km"], M[ref]["km"])) for ref in ("real",)}
(HERE / "numbers.json").write_text(json.dumps(N, indent=1))

# ---- Fig: national map (unlabeled dots) ----
geo = json.loads((ROOT / "output/ryry_viz/korea.json").read_text())
ll = np.concatenate([j["ll"] for j in jobs.values()])
fig, ax = plt.subplots(figsize=(3.3, 4.4))
for ft in geo["features"]:
    g = ft["geometry"]
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = np.array(poly[0])
        ax.fill(ring[:, 0], ring[:, 1], color=SKY, ec="#c9d4e3", lw=0.5)
ax.scatter(ll[:, 1], ll[:, 0], s=1.2, color=BLUE, alpha=0.35, lw=0)
ax.scatter([DEPOT[1]], [DEPOT[0]], marker="*", s=130, color=ORANGE, ec="white", lw=0.8, zorder=5)
ax.annotate("Depot (Changwon)", (DEPOT[1], DEPOT[0]), xytext=(DEPOT[1] - 2.3, DEPOT[0] - 0.75), color=INK, fontsize=8.5,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
ax.set_xlim(125.9, 129.7)
ax.set_ylim(33.0, 38.7)
ax.set_aspect(1 / np.cos(np.radians(36)))
ax.axis("off")
save(fig, "map")

# ---- Fig: synthetic example job, solved with the real code ----
rng = np.random.default_rng(7)
centres = np.array([[40, 30], [95, 60], [60, 105], [130, 115]])
pts = np.concatenate([c + rng.normal(0, 11, (n, 2)) for c, n in zip(centres, (8, 7, 6, 5))])
v = np.clip(rng.lognormal(np.log(0.9), 0.55, len(pts)), 0.2, 3.0)
depot = np.array([0.0, 0.0])
D = np.zeros((len(pts) + 1, len(pts) + 1))
D[1:, 1:] = 1.3 * np.linalg.norm(pts[:, None] - pts[None], axis=2)
D[0, 1:] = D[1:, 0] = 1.3 * np.linalg.norm(pts - depot, axis=1)
cols = knn_columns(pts, 8)
plan, info = solve2(pts, v, D, cols)
km, ordered = zip(*[(k, o) for k, o in (tuple(x[0] for x in route_cost(D, np.array([c]))) for c in plan)])
N["example"] = dict(stops=len(pts), candidates=info["cols"], trucks=len(plan), km=round(float(sum(km))), volume=round(float(v.sum()), 1))
sample = [dict(stop=f"S{i + 1:02d}", x_km=round(float(x), 1), y_km=round(float(y), 1), volume_m3=round(float(q), 2)) for i, ((x, y), q) in enumerate(zip(pts, v))]
(HERE / "synthetic_job.json").write_text(json.dumps(dict(depot=[0, 0], stops=sample, plan=[[f"S{i + 1:02d}" for i in o] for o in ordered]), indent=1))

fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.7))
nb = [np.argsort(np.linalg.norm(pts - p, axis=1))[1:5] for p in pts]
for k, ax in enumerate(axs):
    ax.set_xlim(-12, 160)
    ax.set_ylim(-12, 140)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(GRID)
    if k == 1:
        for i, js in enumerate(nb):
            for j in js:
                ax.plot(*zip(pts[i], pts[j]), color=BLUE, alpha=0.35, lw=0.8, zorder=1)
    if k == 2:
        for o in ordered:
            path = np.r_[[depot], pts[list(o)]]
            ax.plot(path[:1 + 1, 0], path[:2, 1], color=GREY, lw=0.8, ls=(0, (2, 2)), zorder=1)
            ax.plot(path[1:, 0], path[1:, 1], color=BLUE, lw=1.6, zorder=2, solid_capstyle="round")
    ax.scatter(pts[:, 0], pts[:, 1], s=14 + 22 * v, color=BLUE if k else "#7fa6e8", ec="white", lw=0.8, zorder=3)
    ax.scatter(*depot, marker="*", s=120, color=ORANGE, ec="white", lw=0.6, zorder=4)
axs[0].set_title("(a) Stops and depot")
axs[1].set_title("(b) Short list of partners")
axs[2].set_title(f"(c) Optimal plan: {len(plan)} trucks")
axs[0].text(0, 128, "dot size = volume", fontsize=8, color=MUTED)
axs[2].text(0, 128, "dashed = drive from depot", fontsize=8, color=MUTED)
fig.tight_layout(w_pad=0.6)
save(fig, "example")

# ---- Fig: trucks and total road km per method (two panels, one scale each) ----
order = ["kmeans", "real", "agg", "opt", "gnn_opt"]
col = {"real": ORANGE, "kmeans": GREY, "agg": GREY, "opt": "#9dbbef", "gnn_opt": BLUE}
short = {"real": "Real dispatch", "kmeans": "k-means", "agg": "Agglomerative", "opt": "Optimizer, 15-nearest", "gnn_opt": "GNN + optimizer (ours)"}
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.3))
y = np.arange(len(order))[::-1]
for ax, key, title, f_, mx_ in ((axs[0], "trucks", "Trucks for all 97 jobs", "{:,.0f}", 3300), (axs[1], "km", "Total road km for all 97 jobs", "{:,.0f}", 820000)):
    vals = [M[m][key] for m in order]
    ax.barh(y, vals, height=0.56, color=[col[m] for m in order], zorder=2)
    for yy, vv, m in zip(y, vals, order):
        ax.text(vv + mx_ * 0.012, yy, f_.format(vv), va="center", color=INK, fontsize=8.5, fontweight="semibold" if m == "gnn_opt" else "normal")
    ax.set_xlim(0, mx_)
    ax.set_title(title)
    ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
axs[0].set_yticks(y, [short[m] for m in order])
axs[1].set_yticks(y, [""] * len(order))
axs[0].set_xticks([0, 1000, 2000, 3000], ["0", "1,000", "2,000", "3,000"])
axs[1].set_xticks([0, 200000, 400000, 600000, 800000], ["0", "200K", "400K", "600K", "800K"])
fig.tight_layout(w_pad=1.2)
save(fig, "trucks")

# ---- Fig: how close to the best possible, per job ----
fig, ax = plt.subplots(figsize=(3.4, 2.4))
labs = ["Proven optimal", "1 truck above\nlower bound", "2 trucks above\nlower bound"]
cnt = [N["proof"]["optimal"], N["proof"]["plus1"], N["proof"]["plus2"]]
ax.bar(range(3), cnt, width=0.5, color=[BLUE, "#9dbbef", "#c9d8f3"], zorder=2)
for i, c_ in enumerate(cnt):
    ax.text(i, c_ + 1.5, f"{c_} jobs", ha="center", color=INK, fontsize=9)
ax.set_xticks(range(3), labs)
ax.set_ylim(0, 92)
ax.set_yticks([0, 20, 40, 60, 80])
ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
ax.tick_params(axis="x", length=0)
ax.set_ylabel("Jobs (of 97)")
save(fig, "proof")

# ---- Fig: speed (two panels, no dual axis) ----
g = N["gnn"]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 1.9))
for ax, (vals_, title, fmt) in zip(axs, [(g["cols"], "Candidate loads per job (median)", "{:,.0f}"), (g["s"], "Solve time per job, seconds (median)", "{:.1f} s")]):
    ax.barh([1, 0], vals_, height=0.5, color=[GREY, BLUE], zorder=2)
    for yy, vv in zip([1, 0], vals_):
        ax.text(vv * 1.02 + max(vals_) * 0.01, yy, fmt.format(vv), va="center", color=INK, fontsize=9)
    ax.set_yticks([1, 0], ["15-nearest list", "GNN short list"])
    ax.set_xlim(0, max(vals_) * 1.28)
    ax.set_title(title)
    ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
axs[0].set_xticks([0, 5000, 10000, 15000, 20000], ["0", "5K", "10K", "15K", "20K"])
fig.tight_layout(w_pad=2)
save(fig, "speed")

# ---- Fig: KPI change against the real dispatch and the earlier method ----
kpis = [("trucks", "Trucks"), ("km", "Road km"), ("hours", "Driving hours")]
fig, ax = plt.subplots(figsize=(7.2, 1.7))
yk = np.arange(len(kpis))[::-1]
for off_, ref, c_, lab in ((0, "real", BLUE, "vs real dispatch"),):
    vv = [N["pct"][ref][k] for k, _ in kpis]
    ax.barh(yk + off_, vv, height=0.5, color=c_, zorder=2, label=lab)
    for yy, x in zip(yk + off_, vv):
        ax.text(x - 0.4, yy, f"{x:+.1f} %".replace("-", "−"), va="center", ha="right", color=INK, fontsize=8.5)
ax.set_yticks(yk, [l_ for _, l_ in kpis])
ax.set_xlim(-30, 0)
ax.set_xticks([-30, -20, -10, 0], ["−30 %", "−20 %", "−10 %", "0"])
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
ax.axvline(0, color=MUTED, lw=0.8)
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
save(fig, "kpi")

# ---- Fig: pipeline ----
fig, ax = plt.subplots(figsize=(7.2, 1.95))
ax.set_xlim(0, 100)
ax.set_ylim(0, 27)
ax.axis("off")
steps = [("1  Road km", "private map server\n(OSRM, Korea)"), ("2  Short list", "GNN: each stop's\n8 likeliest partners"),
         ("3  Candidates", "rule-safe groups\nof 1-5 stops"), ("4  Selection", "exact MILP: fewest\ntrucks, then km"),
         ("5  Check", "every truck checked\nagainst every rule")]
w, gap_ = 17.6, 2.9
for i, (t, d) in enumerate(steps):
    x0 = i * (w + gap_)
    ax.add_patch(matplotlib.patches.FancyBboxPatch((x0, 4), w, 19, boxstyle="round,pad=0,rounding_size=1.6",
                                                   fc=SKY if i != 3 else "#dce8fb", ec=NAVY if i == 3 else "#b9c8de", lw=1.1))
    ax.text(x0 + 1.4, 19.2, t, fontsize=8.8, fontweight="semibold", color=NAVY, va="center")
    ax.text(x0 + 1.4, 11.2, d, fontsize=7.9, color=INK, va="center", linespacing=1.35)
    if i < len(steps) - 1:
        ax.annotate("", (x0 + w + gap_ - 0.3, 13.5), (x0 + w + 0.3, 13.5), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.1))
ax.text(0, 1.2, "Input: one job's stops (location, volume)", fontsize=7.9, color=MUTED)
ax.text(100, 1.2, "Output: per truck, its stops, type, order, km, hours", fontsize=7.9, color=MUTED, ha="right")
save(fig, "pipeline")

print(json.dumps({k: N[k] for k in ("data", "proof", "example", "co2", "save", "pct", "year_factor")}, indent=1))

# ---- added figures: rules, earlier method vs optimizer, GNN, proof funnel, per job ----
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle  # noqa: E402
from ryry import greedy2  # noqa: E402

# rules, drawn
fig, axs = plt.subplots(1, 3, figsize=(7.2, 1.9))
for ax in axs:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect("equal")
    ax.axis("off")
ax = axs[0]
for i in range(5):
    ax.add_patch(Circle((1.2 + i * 1.9, 3.2), 0.55, color=BLUE))
ax.text(5, 0.5, "1 to 5 addresses per truck", ha="center", fontsize=9, color=INK)
ax = axs[1]
ax.add_patch(Rectangle((1.2, 2.0), 7.6, 2.6, fc="white", ec=NAVY, lw=1.2))
ax.add_patch(Rectangle((1.2, 2.0), 7.6 * 0.6, 2.6, fc="#c9daf7", ec="none"))
ax.plot([1.2 + 7.6 * 0.6] * 2, [2.0, 4.6], color=NAVY, lw=1.2, ls=(0, (2, 2)))
ax.text(1.2 + 7.6 * 0.3, 3.3, "60 %", ha="center", va="center", fontsize=10, color=NAVY, fontweight="semibold")
ax.text(5, 0.5, "load at most 60 % of the box", ha="center", fontsize=9, color=INK)
ax = axs[2]
ax.add_patch(Circle((5, 3.7), 1.95, fc=SKY, ec=NAVY, lw=1.1, ls=(0, (3, 2))))
for dx, dy in ((-1.2, 0.6), (0.9, 1.1), (0.3, -1.2), (-0.6, -0.5), (1.5, -0.2)):
    ax.add_patch(Circle((5 + 0.85 * dx, 3.7 + 0.85 * dy), 0.28, color=BLUE))
ax.plot([5, 5 + 1.95 * 0.8], [3.7, 3.7 - 1.95 * 0.6], color=MUTED, lw=0.8)
ax.text(7.0, 2.0, "50 km", ha="left", fontsize=8, color=MUTED)
ax.text(5, 0.5, "every stop within 50 km of the centre", ha="center", fontsize=9, color=INK)
save(fig, "rules")

# the earlier rule-based method against the optimizer, same synthetic job
g_plan = greedy2(pts, v, order=np.argsort(-v))
g_ord = [route_cost(D, np.array([c]))[1][0] for c in g_plan]
g_km = sum(route_cost(D, np.array([c]))[0][0] for c in g_plan)
N["example"].update(greedy_trucks=len(g_plan), greedy_km=round(float(g_km)))
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
for ax, plan_, title in ((axs[0], g_ord, f"Earlier rule-based method: {len(g_plan)} trucks, {g_km:,.0f} km"),
                         (axs[1], ordered, f"Exact optimizer: {len(plan)} trucks, {sum(km):,.0f} km")):
    ax.set_xlim(-12, 160)
    ax.set_ylim(-12, 152)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(GRID)
    for o in plan_:
        path = np.r_[[depot], pts[list(o)]]
        ax.plot(path[:2, 0], path[:2, 1], color=GREY, lw=0.8, ls=(0, (2, 2)), zorder=1)
        ax.plot(path[1:, 0], path[1:, 1], color=BLUE if plan_ is ordered else ORANGE, lw=1.6, zorder=2)
        if len(o) == 1:
            ax.add_patch(Circle(pts[o[0]], 6, fc="none", ec=ORANGE, lw=1.2, zorder=4))
    ax.scatter(pts[:, 0], pts[:, 1], s=14 + 22 * v, color=BLUE, ec="white", lw=0.8, zorder=3)
    ax.scatter(*depot, marker="*", s=120, color=ORANGE, ec="white", lw=0.6, zorder=4)
    ax.set_title(title)
axs[0].text(155, -6, "circled: a stop alone in its own truck", fontsize=8, color=MUTED, ha="right")
fig.tight_layout(w_pad=1)
save(fig, "greedy_vs_opt")

# the GNN, as a flow
fig, ax = plt.subplots(figsize=(7.2, 1.55))
ax.set_xlim(0, 100)
ax.set_ylim(0, 20)
ax.axis("off")
boxes = [("Job graph", "stops as nodes,\n12 nearest linked"), ("Features", "8 per stop,\n4 per pair"),
         ("4 rounds of\nmessage passing", None), ("Pair score", "chance two stops\nshare a truck"), ("Short list", "each stop's\n8 best partners")]
w, gap_ = 17.6, 2.9
for i, (t_, d_) in enumerate(boxes):
    x0 = i * (w + gap_)
    ax.add_patch(FancyBboxPatch((x0, 1.5), w, 17, boxstyle="round,pad=0,rounding_size=1.6", fc="#dce8fb" if i == 2 else SKY,
                                ec=NAVY if i == 2 else "#b9c8de", lw=1.1))
    if d_ is None:
        ax.text(x0 + w / 2, 10, t_, fontsize=8.8, fontweight="semibold", color=NAVY, ha="center", va="center", linespacing=1.3)
    else:
        ax.text(x0 + 1.4, 14.6, t_, fontsize=8.8, fontweight="semibold", color=NAVY, va="center")
        ax.text(x0 + 1.4, 7.4, d_, fontsize=7.8, color=INK, va="center", linespacing=1.35)
    if i < len(boxes) - 1:
        ax.annotate("", (x0 + w + gap_ - 0.3, 10), (x0 + w + 0.3, 10), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.1))
save(fig, "gnn")

# the proof, as a funnel for a typical job
lefts = [r["long_info"]["prove"]["left"] for r in cg.values() if r["long_info"].get("prove") and "left" in r["long_info"]["prove"]]
N["proof"]["left_med"] = int(np.median(lefts))
stages = [("Possible groups of up to 5 stops", "7.7 million", 1.0), ("Valid loads under the company rules", f"{N['proof']['loads_med']:,}", 0.72),
          ("Loads that could still improve the plan", f"{N['proof']['left_med']:,}", 0.46), ("Exact solve: optimal plan, with proof", "optimal", 0.26)]
fig, ax = plt.subplots(figsize=(7.2, 2.0))
ax.set_xlim(-1, 1)
ax.set_ylim(-0.5, len(stages) - 0.4)
ax.axis("off")
shades = ["#c9daf7", "#a8c3f2", "#7fa6e8", BLUE]
for k, (lab, val, wd) in enumerate(stages):
    yy = len(stages) - 1 - k
    ax.add_patch(FancyBboxPatch((-wd / 2 - 0.45, yy - 0.36), wd, 0.72, boxstyle="round,pad=0,rounding_size=0.06", fc=shades[k], ec="none", mutation_aspect=0.5))
    ax.text(-0.45, yy, val, ha="center", va="center", fontsize=10, fontweight="semibold", color="white" if k == 3 else NAVY)
    ax.text(0.12, yy, lab, ha="left", va="center", fontsize=9, color=INK)
save(fig, "funnel")

# per job: real dispatch against our plan
jobs_s = S["jobs"]
xr = np.array([j["trucks"]["real"] for j in jobs_s])
yl = np.array([j["trucks"]["gnn_opt"] for j in jobs_s])
N["perjob"] = dict(fewer=int((yl < xr).sum()), more=int((yl > xr).sum()), same=int((yl == xr).sum()))
fig, ax = plt.subplots(figsize=(3.4, 3.0))
mx = max(xr.max(), yl.max()) + 3
ax.plot([0, mx], [0, mx], color=MUTED, lw=0.8, ls=(0, (3, 2)))
ax.scatter(xr, yl, s=22, color=BLUE, ec="white", lw=0.7, zorder=3)
ax.text(mx * 0.6, mx * 0.66, "same number", rotation=38, fontsize=8, color=MUTED, ha="center", va="bottom", rotation_mode="anchor")
ax.set_xlim(0, mx)
ax.set_ylim(0, mx)
ax.set_aspect("equal")
ax.text(mx * 0.04, mx * 0.96, f"{int((yl < xr).sum())} of {len(xr)} jobs below the line:\nfewer trucks than the real dispatch", fontsize=8, color=INK, ha="left", va="top")
ax.set_xlabel("Trucks per job, real dispatch")
ax.set_ylabel("Trucks per job, our plan")
ax.grid(True, color=GRID, lw=0.7)
ax.set_axisbelow(True)
save(fig, "perjob")

(HERE / "numbers.json").write_text(json.dumps(N, indent=1))
print("extra", N["example"], N["proof"]["left_med"], N["perjob"])

# cover art: the synthetic job's optimal routes, no axes
fig, ax = plt.subplots(figsize=(5.2, 3.0))
ax.set_xlim(-8, 150)
ax.set_ylim(-8, 142)
ax.set_aspect("equal")
ax.axis("off")
for o in ordered:
    path = np.r_[[depot], pts[list(o)]]
    ax.plot(path[:2, 0], path[:2, 1], color="#9fb3d6", lw=0.9, ls=(0, (2, 2)), zorder=1)
    ax.plot(path[1:, 0], path[1:, 1], color=BLUE, lw=2.0, zorder=2, solid_capstyle="round")
ax.scatter(pts[:, 0], pts[:, 1], s=20 + 30 * v, color=NAVY, ec="white", lw=1.0, zorder=3)
ax.scatter(*depot, marker="*", s=260, color=ORANGE, ec="white", lw=0.8, zorder=4)
fig.savefig(FIG / "cover.svg", transparent=True)
fig.savefig(FIG / "cover.png", dpi=220, transparent=True)
plt.close(fig)

# ---- page-filling V1 material: GNN per fold, savings by job size, solve time by job size, workflow, example plan ----
from ryry import graphs_for, matrices  # noqa: E402
from ryry_v3 import auc  # noqa: E402

G = graphs_for(jobs, matrices(), base)
z = np.load(OUT / "ryry_gnn_oof.npz")
oof = {str(j): z[f"p{i}"] for i, j in enumerate(z["jobs"])}
ids = list(G)
folds = []
for k in range(5):
    fj = [j for i, j in enumerate(ids) if i * 5 // len(ids) == k]
    y_ = np.concatenate([G[j]["y"] for j in fj])
    p_ = np.concatenate([oof[j] for j in fj])
    folds.append(dict(k=k + 1, jobs=len(fj), first=jobs[fj[0]]["date"], last=jobs[fj[-1]]["date"], pairs=int(len(y_)),
                      acc=round(100 * float(((p_ > 0.5) == (y_ > 0.5)).mean()), 1), base=round(100 * float(1 - y_.mean()), 1),
                      auc=round(float(auc(p_, y_)), 2)))
N["folds"] = folds

# savings by job size
n_ = np.array([j["n"] for j in jobs_s])
saved = xr - yl
fig, ax = plt.subplots(figsize=(7.2, 2.4))
ax.axhline(0, color=MUTED, lw=0.8)
ax.scatter(n_, saved, s=18, color=BLUE, ec="white", lw=0.6, zorder=3)
ax.set_xlabel("Stops in the job")
ax.set_ylabel("Trucks saved")
ax.set_title("Trucks saved on each job against the real dispatch")
ax.grid(True, color=GRID, lw=0.7)
ax.set_axisbelow(True)
ax.set_xlim(0, 150)
save(fig, "bysize")
small_, big_ = n_ < np.median(n_), n_ >= np.median(n_)
N["bysize"] = dict(med_stops=int(np.median(n_)), small_saved=round(float(saved[small_].mean()), 1), big_saved=round(float(saved[big_].mean()), 1),
                   small_pct=round(100 * float(saved[small_].sum() / xr[small_].sum()), 1), big_pct=round(100 * float(saved[big_].sum() / xr[big_].sum()), 1),
                   corr=round(float(np.corrcoef(n_, saved)[0, 1]), 2))

# solve time by job size
ord_ = list(jobs)
nn = np.array([len(jobs[j]["v"]) for j in ord_])
t_opt = np.array([base[j]["opt_s"] for j in ord_])
t_gnn = np.array([gnn[j]["gnn_opt_s"] for j in ord_])
fig, ax = plt.subplots(figsize=(7.2, 2.5))
ax.scatter(nn, np.maximum(t_opt, 0.1), s=16, color=GREY, ec="white", lw=0.5, label="Optimizer, 15-nearest list", zorder=2)
ax.scatter(nn, np.maximum(t_gnn, 0.1), s=16, color=BLUE, ec="white", lw=0.5, label="GNN + optimizer", zorder=3)
ax.set_yscale("log")
ax.set_yticks([0.1, 1, 10, 100], ["0.1 s", "1 s", "10 s", "100 s"])
ax.set_xlabel("Stops in the job")
ax.set_ylabel("Solve time per job")
ax.grid(True, color=GRID, lw=0.7, which="major")
ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
save(fig, "timesize")
big = nn >= 100
N["timesize"] = dict(big_jobs=int(big.sum()), opt_big_med=round(float(np.median(t_opt[big])), 1), gnn_big_med=round(float(np.median(t_gnn[big])), 1),
                     opt_small_med=round(float(np.median(t_opt[nn < 50])), 1), gnn_small_med=round(float(np.median(t_gnn[nn < 50])), 1))

# how a dispatcher uses it
fig, ax = plt.subplots(figsize=(7.2, 1.45))
ax.set_xlim(0, 100)
ax.set_ylim(0, 20)
ax.axis("off")
flow = [("Order export", "today's spreadsheet,\nno new data entry"), ("Planner", "on the company PC,\nseconds per job"),
        ("Plan sheet + map", "per truck: stops in\norder, size, km, hours"), ("Dispatcher", "reviews, edits if\nneeded, books trucks")]
w, gap_ = 22.6, 3.2
for i, (t_, d_) in enumerate(flow):
    x0 = i * (w + gap_)
    ax.add_patch(FancyBboxPatch((x0, 1.5), w, 17, boxstyle="round,pad=0,rounding_size=1.6", fc="#dce8fb" if i == 1 else SKY,
                                ec=NAVY if i == 1 else "#b9c8de", lw=1.1))
    ax.text(x0 + 1.6, 14.4, t_, fontsize=8.8, fontweight="semibold", color=NAVY, va="center")
    ax.text(x0 + 1.6, 7.4, d_, fontsize=7.8, color=INK, va="center", linespacing=1.35)
    if i < len(flow) - 1:
        ax.annotate("", (x0 + w + gap_ - 0.3, 10), (x0 + w + 0.3, 10), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.1))
save(fig, "workflow")

# the planner's output for the synthetic job, as a table
rows_ = []
for t_i, (o, k_) in enumerate(sorted(zip(ordered, km), key=lambda x: D[0, x[0][0] + 1]), 1):
    vol = float(v[list(o)].sum())
    truck = "1-ton" if vol <= C + 1e-9 else "1.4-ton"
    rows_.append(f"| {t_i} | {' → '.join(f'S{i + 1:02d}' for i in o)} | {vol:.2f} | {truck} | {100 * vol / (C if truck == '1-ton' else C14):.0f} % | {k_:,.0f} |")
(HERE / "example_plan.md").write_text("| Truck | Stops in visiting order | Volume (m³) | Truck size | Share of usable volume | km (synthetic) |\n|--:|---|--:|---|--:|--:|\n" + "\n".join(rows_) + "\n")
(HERE / "numbers.json").write_text(json.dumps(N, indent=1))
print("fill", N["folds"], N["bysize"], N["timesize"])

# ---- cover background: full A4 page; gradient with 50 km rings around the depot, the map, one real job's trucks ----
# One real job at national scale with unlabeled stops (the user chose a real job, like the map figure).
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Ellipse  # noqa: E402

KM_LAT = 111.0
km_lon = KM_LAT * np.cos(np.radians(DEPOT[0]))
spread = {jid: float(np.ptp(j["ll"][:, 0]) + np.ptp(j["ll"][:, 1])) for jid, j in jobs.items() if 55 <= len(j["v"]) <= 75 and jid in gnn}
jid = max(spread, key=spread.get)  # a typical-size job that reaches far across the country
j = jobs[jid]
s_ = np.flatnonzero(j["v"] <= C14 + 1e-9)
clus = [[int(i) for i in c] for c in gnn[jid]["plans"]["gnn_opt"]]  # indices into the job's stops
N["cover"] = dict(stops=len(j["v"]), trucks=gnn[jid]["gnn_opt"]["trucks"], real=int(len(set(j["real"]))) if "real" in j else None)

def cover_art(name, size, box):
    """The cover picture: gradient, 50 km rings round the depot, the map, the chosen job's trucks."""
    fig = plt.figure(figsize=size)
    bg = fig.add_axes([0, 0, 1, 1])
    gx, gy = np.meshgrid(np.linspace(0, 1, 400), np.linspace(0, 1, 560))
    bg.imshow(0.65 * gy + 0.35 * gx, cmap=LinearSegmentedColormap.from_list("cv", [BLUE, "#2554b8", NAVY]), extent=(0, 1, 0, 1), aspect="auto", origin="lower")
    bg.axis("off")
    ax = fig.add_axes(box)
    ax.set_xlim(125.9, 129.7)
    ax.set_ylim(33.0, 38.7)
    ax.set_aspect(1 / np.cos(np.radians(36)))
    ax.axis("off")
    for r_km in range(50, 901, 50):  # the pattern: distance rings every 50 km from the depot
        ax.add_patch(Ellipse((DEPOT[1], DEPOT[0]), 2 * r_km / km_lon, 2 * r_km / KM_LAT, fc="none", ec="white", lw=0.6, alpha=0.07, clip_on=False))
    for ft in geo["features"]:
        g_ = ft["geometry"]
        for poly in (g_["coordinates"] if g_["type"] == "MultiPolygon" else [g_["coordinates"]]):
            ring = np.array(poly[0])
            ax.fill(ring[:, 0], ring[:, 1], color="white", alpha=0.10, lw=0)
            ax.plot(ring[:, 0], ring[:, 1], color="white", alpha=0.30, lw=0.45)
    ax.scatter(ll[:, 1], ll[:, 0], s=0.7, color="white", alpha=0.22, lw=0)
    big3 = sorted((c for c in clus if len(c) >= 3), key=lambda c: -np.hypot(*(j["ll"][c].mean(0) - DEPOT)))[:3]
    for c in clus:
        p = j["ll"][c]
        ax.plot([DEPOT[1], p[0, 1]], [DEPOT[0], p[0, 0]], color="white", lw=0.6, alpha=0.35, ls=(0, (2, 2)))
        ax.plot(p[:, 1], p[:, 0], color="#ffd9a8", lw=1.8, solid_capstyle="round", zorder=4)
    for c in big3:
        cy, cx = j["ll"][c].mean(0)
        ax.add_patch(Ellipse((cx, cy), 2 * 50 / km_lon, 2 * 50 / KM_LAT, fc=(1, 1, 1, 0.07), ec="white", lw=1.0, ls=(0, (3, 2)), zorder=3))
    ax.scatter(j["ll"][:, 1], j["ll"][:, 0], s=16, color="white", ec=NAVY, lw=0.5, zorder=5)
    ax.scatter([DEPOT[1]], [DEPOT[0]], marker="*", s=420, color=ORANGE, ec="white", lw=1.0, zorder=6)
    lab = dict(color="white", fontsize=11, fontweight="medium", zorder=7)
    ax.annotate("Depot (Changwon)", (DEPOT[1], DEPOT[0]), xytext=(DEPOT[1] - 2.2, DEPOT[0] - 0.95), arrowprops=dict(arrowstyle="-", color="white", lw=0.7), **lab)
    cy, cx = j["ll"][big3[0]].mean(0)
    ax.annotate("50 km radius:\nevery stop of a truck\nwithin 50 km of its centre", (cx + 50 / km_lon * 0.7, cy + 50 / KM_LAT * 0.7), xytext=(cx + 0.55, cy + 0.75), arrowprops=dict(arrowstyle="-", color="white", lw=0.7), **lab)
    ax.text(127.75, 33.25, f"One real dispatch job: {len(j['v'])} stops,\n{gnn[jid]['gnn_opt']['trucks']} trucks in our plan.\nEach orange line is one truck:\nup to 5 stops, at most 60 % load.", **lab)
    with plt.rc_context({"savefig.bbox": "standard", "savefig.pad_inches": 0}):  # exactly the page size
        fig.savefig(FIG / name, dpi=220)
    plt.close(fig)


cover_art("cover_bg.png", (8.27, 11.69), [0.34, 0.035, 0.64, 0.665])  # report cover, A4
cover_art("slide_bg.png", (13.333, 7.5), [0.555, 0.03, 0.43, 0.94])  # title slide, 16:9
(HERE / "numbers.json").write_text(json.dumps(N, indent=1))
print("cover", jid[:8], N["cover"])
