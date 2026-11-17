"""Aggregates for the slide figures (no locations): method totals and each job's date and trucks saved.
  .venv/bin/python -I competition/webfigs/data.py  -> competition/webfigs/data.json  (reads the results page's summary.json)"""
import json
from pathlib import Path

HERE = Path(__file__).parent
S = json.loads((HERE.parent.parent / "output/ryry_viz/summary.json").read_text())
M = S["methods"]
keys = ["real", "kmeans", "agg", "opt", "knn8", "gnn_opt"]
methods = {k: dict(trucks=M[k]["trucks"], km=round(M[k]["km"])) for k in keys}
jobs = [dict(date=j["date"], saved=j["trucks"]["real"] - j["trucks"]["gnn_opt"]) for j in S["jobs"]]
assert methods["gnn_opt"]["trucks"] == 1933 and methods["real"]["trucks"] == 2517 and len(jobs) == 97
assert sum(j["saved"] > 0 for j in jobs) == 93
(HERE / "data.json").write_text(json.dumps(dict(methods=methods, jobs=jobs), indent=1))
print("ok", methods["knn8"], max(j["saved"] for j in jobs), min(j["saved"] for j in jobs))
