"""Each stop's boxes, for the loading check: order lines (data/riri, personal data) x box sizes -> cluster/results/ryry_items.json
  UV_CACHE_DIR=.uv-cache .bin/uv run --no-project --with pandas --with openpyxl python -I cluster/ryry_items.py
The output holds only stop IDs and box sizes: {experiment_stop_id: {"boxes": [[w, d, h, qty], ...] in cm, "vol": m3 from
these boxes, "frozen": m3 in the frozen set, "lines": order lines, "sized": lines with a known box}}.
Addresses are used in memory as the join key (job + address) and are never printed or written."""
import csv
import glob
import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cluster/results/ryry_items.json"


def code(name):
    """Model code = the product name up to the first space or bracket (WPC-2000C (white) -> WPC-2000C)."""
    return re.split(r"[\s(\[]", str(name).strip(), maxsplit=1)[0].upper()


def main():
    sizes = pd.read_excel(glob.glob(str(ROOT / "data/riri/*product*.xlsx"))[0], sheet_name="Inventory Status", header=1)
    box = {code(r["Product Name"]): (r["horizontal"] / 10, r["vertical"] / 10, r["height"] / 10) for _, r in sizes.iterrows()
           if pd.notna(r["Product Name"])}
    raw = pd.read_excel(glob.glob(str(ROOT / "data/riri/*delivery*.xlsx"))[0])
    lines = defaultdict(list)
    for job, addr, item, qty in zip(raw["job_id"], raw["배송주소"], raw["품목명(규격)"], raw["수량"]):
        q = abs(float(qty)) if pd.notna(qty) else 0.0  # returns are entered as negative quantities
        lines[job, " ".join(str(addr).split())].append((code(item), q))
    out, miss = {}, 0
    with open(ROOT / "data/97_SPATIAL_EXPERIMENT_FROZEN.csv", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            ls = lines.get((r["job_id"], " ".join(r["address_original"].split())), [])
            miss += not ls
            boxes = defaultdict(float)
            for c, q in ls:
                if c in box and q > 0:
                    boxes[box[c]] += q
            out[r["experiment_stop_id"]] = dict(
                boxes=[[w, d, h, q] for (w, d, h), q in boxes.items()], lines=len(ls), sized=sum(c in box for c, _ in ls),
                vol=round(sum(w * d * h * q for (w, d, h), q in boxes.items()) / 1e6, 4), frozen=float(r["total_volume_m3"]))
    OUT.write_text(json.dumps(out))
    OUT.chmod(0o600)
    ratio = pd.Series([v["vol"] / v["frozen"] for v in out.values() if v["frozen"] > 0])
    print(f"{len(box)} box sizes; {len(out)} stops, {miss} with no order line found; lines sized {sum(v['sized'] for v in out.values())} of "
          f"{sum(v['lines'] for v in out.values())}")
    print(f"volume from boxes / frozen volume: within 1 % for {100 * ((ratio - 1).abs() < 0.01).mean():.1f} % of stops; "
          f"lower {100 * (ratio < 0.99).mean():.1f} %, higher {100 * (ratio > 1.01).mean():.1f} %; median {ratio.median():.3f}")
    tall = pd.Series([h for v in out.values() for _, _, h, q in v["boxes"] for _ in range(int(q))])
    print(f"boxes {len(tall)}; height cm p50 {tall.median():.0f}, p90 {tall.quantile(.9):.0f}, max {tall.max():.0f}; "
          f"taller than a 1-ton's 160 cm: {100 * (tall > 160).mean():.1f} %")


if __name__ == "__main__":
    main()
