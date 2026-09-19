"""Paired descriptive comparison across instances, never treating seeds as datasets."""
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from warehouse_opt.models import write_json


def main():
    root = Path(sys.argv[1])
    summaries = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    by = {(r["instance"], r["method"]): r for r in summaries}
    names = sorted({r["instance"] for r in summaries})
    rows = []
    for method in sorted({r["method"] for r in summaries}):
        pairs = [(by[n, method], by[n, "ALNS"]) for n in names if (n, method) in by and (n, "ALNS") in by]
        differences = [a["objective"]["mean"] - b["objective"]["mean"] for a, b in pairs]
        rows.append({"method": method, "instances": len(pairs),
                     "mean_improvement_pct_B0": statistics.mean(a["objective"]["improvement_pct_vs_B0"] for a, _ in pairs),
                     "wins_vs_ALNS": sum(d < -1e-9 for d in differences),
                     "ties_vs_ALNS": sum(abs(d) <= 1e-9 for d in differences),
                     "losses_vs_ALNS": sum(d > 1e-9 for d in differences)})
    write_json(root / "paired.json", rows)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
