"""Sequential budget sweep with a preselected stratified Kris sample."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from warehouse_opt.benchmark import benchmark
from warehouse_opt.models import write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--budgets", type=float, nargs="+", default=[1, 3, 5])
    parser.add_argument("--output", default="results/vns_suite")
    args = parser.parse_args()
    root = ROOT / args.output
    root.mkdir(parents=True, exist_ok=False)
    base = json.loads((ROOT / "configs/vns_comparison.json").read_text())
    catalog = json.loads((ROOT / "data/processed/kris_small/catalog.json").read_text())["instances"]
    selected = [r for n in (6, 12, 18) for r in sorted([r for r in catalog if r["orders"] == n], key=lambda r: r["file"])[:3]]
    write_json(root / "kris_selection.json", selected)
    for seconds in args.budgets:
        for dataset in ("synthetic", "kris"):
            config = {**base, "search": {**base["search"], "seconds": seconds}}
            if dataset == "kris":
                config["instances"] = [str(ROOT / r["file"]) for r in selected]
            dest = root / f"{dataset}-{seconds:g}s"
            print(f"START {dest}", flush=True)
            rows = benchmark(config, dest)
            print(f"DONE {dest}: {len(rows)} validated runs", flush=True)


if __name__ == "__main__":
    main()
