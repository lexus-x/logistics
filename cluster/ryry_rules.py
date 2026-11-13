"""What does each company rule cost? Re-plan Ryry's jobs with one rule loosened at a time.
  python -I cluster/ryry_rules.py run       # every variant in turn -> cluster/results/ryry_rule_<name>.jsonl (~35 min each)
  python -I cluster/ryry_rules.py summary   # table -> cluster/results/ryry_rules.md
Every variant only loosens a rule, so the base long-run plan (ryry_cg.py) stays valid and is the starting point: a
variant can match or beat it, never do worse. "control" changes nothing: it shows what a second search finds on its
own, and every saving is measured against it. The proven minimum is recomputed under each variant: exact where every load
can be listed and few enough remain (ryry_cg.prove), else the column-generation floor."""
import os
import subprocess
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
from exact import keep, knn_columns  # noqa: E402
from ryry import C14, OUT, R, big_trucks, finish, load, matrices, pool_run, rows, solve2, split  # noqa: E402
from ryry_cg import LONG, cg_bound, prove  # noqa: E402

VARIANTS = {"control": ({}, "No change (control)"),
            "radius75": ({"RULE_R": "75"}, "Radius 50 km → 75 km"),
            "stops6": ({"RULE_K": "6"}, "5 addresses per truck → 6"),
            "fill70": ({"RULE_FILL": "0.7"}, "Load limit 60 % → 70 %"),
            "no14limit": ({"RULE_MAX14": "100000"}, "No limit on 1.4-ton trucks (was 10 per job)")}


def run_rule(task):
    jid, j, M, base_plan = task
    s, xy, v, Ds, Ts = split(j, M)
    n_big = sum(len(big_trucks(x)) for x in j["v"][j["v"] > C14 + 1e-9])
    row = dict(job=jid)
    if len(s) < 2:
        row.update(bound=n_big + len(s), cg={})
        return finish(row, j, M, s, Ds, Ts, {"plan": [[i] for i in range(len(s))]})
    pos = {int(k): i for i, k in enumerate(s)}
    net = [[pos[k] for k in c] for c in base_plan]
    used = {i for c in net for i in c}
    net += [[i] for i in range(len(s)) if i not in used]  # stops that rode a bigger truck alone under the base load limit
    pool = knn_columns(xy, 15)
    t = time.time()
    # the true optimum under this variant's rules, where listable.
    # shortcut: the exact solve is skipped above 100,000 remaining loads: beyond that the solver overruns its time limit by hours
    # and has never finished (0 of 19 such jobs proven; the largest solved had 87,000); upgrade with a solver that honours its limit
    plan, floor_, proven, pinfo = prove(xy, v, Ds, net, max_left=100_000)
    if proven:
        cl, info = solve2(xy, v, Ds, pool, extra=net + plan, limit=LONG, k=len(plan))
        cl, info, b, cg = cl or plan, dict(info, exact=True, prove=pinfo), len(plan), dict(exact=True, converged=True)
    else:
        cl, info = solve2(xy, v, Ds, pool, extra=net + plan, limit=LONG)
        if cl is None or len(cl) > len(plan):
            cl, info["fallback"] = plan, True
        info["prove"] = pinfo
        b, cg = cg_bound(xy, v, {k: keep(xy, v, C14, R, a)[0] for k, a in pool.items()})
        b = max(b, floor_ or 0)
    row.update(info=info, s=round(time.time() - t, 1))
    row.update(bound=n_big + b, cg=cg)
    return finish(row, j, M, s, Ds, Ts, {"plan": [list(map(int, c)) for c in cl]})


def tasks():
    jobs, Ms, cg = load(), matrices(), rows("cg")
    return [(jid, j, Ms[jid], cg[jid]["plans"]["long"]) for jid, j in jobs.items()]


def drop(ctl, r):
    """How far the fewest possible trucks falls under a variant: (at least, at most). A job's true minimum lies between
    its floor and its plan, so the two differ only where a job is not proven on one side."""
    return (sum(max(0, ctl[j]["bound"] - r[j]["plan"]["trucks"]) for j in r),
            sum(ctl[j]["plan"]["trucks"] - r[j]["bound"] for j in r))


def summary():
    base = rows("cg")
    res = {name: rows(f"rule_{name}") for name in VARIANTS}
    res = {name: r for name, r in res.items() if len(r) == len(base)}
    if "control" not in res:
        return print("control run not finished")
    tot = lambda r, key: sum(x["plan"][key] for x in r.values())  # noqa: E731
    c_t, c_km = tot(res["control"], "trucks"), tot(res["control"], "km")
    lines = [f"Price of each rule, {len(base)} jobs. Base long run: {sum(x['long']['trucks'] for x in base.values())} trucks, "
             f"proven minimum {sum(x['bound'] for x in base.values())}. Each row loosens one rule; savings are against the control.", "",
             "| rule loosened | trucks | trucks saved | proven minimum | minimum drops by | jobs that improve | road km | km change |",
             "|---|---|---|---|---|---|---|---|"]
    for name, r in res.items():
        t, b, km = tot(r, "trucks"), sum(x["bound"] for x in r.values()), tot(r, "km")
        better = sum(r[j]["plan"]["trucks"] < res["control"][j]["plan"]["trucks"] for j in r)
        lo, hi = drop(res["control"], r)
        lines.append(f"| {VARIANTS[name][1]} | {t} | {c_t - t} ({100 * (c_t - t) / c_t:.1f} %) | {b} | {lo if lo == hi else f'{lo} to {hi}'} | {better} | "
                     f"{km:,.0f} | {100 * (km / c_km - 1):+.1f} % |")
    lines += ["", "Trucks saved = plans actually found. The proven minimum is the fewest trucks any plan could use under that variant's "
              "rules. Where every job is proven the drop is exact; a range means some jobs have too many possible loads to prove."]
    (OUT / "ryry_rules.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "run":
        for name, (env, _) in VARIANTS.items():  # one interpreter per variant: the rules are read at import
            subprocess.run([sys.executable, "-I", __file__, "one", name], env={**os.environ, **env}, check=True)
        summary()
    elif mode == "one":
        pool_run(run_rule, tasks(), f"rule_{sys.argv[2]}")
    elif mode == "summary":
        summary()
