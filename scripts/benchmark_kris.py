"""Run the generic, auditable benchmark on the processed Kris catalog.

The old helper solved one instance per order-count stratum and wrote a custom
summary. This command uses :func:`src.benchmark` so it produces raw
runs, fingerprints, paired comparisons and a manifest that
``build_comparison_report.py`` can export.
"""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmark import benchmark
from src.models import write_json


def select_entries(catalog, orders=None, limit_per_size=0):
    entries = sorted(catalog, key=lambda row: (row["orders"], row["file"]))
    if orders:
        wanted = set(orders)
        entries = [row for row in entries if row["orders"] in wanted]
    if limit_per_size:
        by_size = defaultdict(list)
        for row in entries:
            by_size[row["orders"]].append(row)
        entries = [row for size in sorted(by_size) for row in by_size[size][:limit_per_size]]
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/processed/kris_small/catalog.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results/kris_benchmark")
    parser.add_argument("--report-output", type=Path, default=None,
                        help="Optionally export report-ready CSV/MD files after validation")
    parser.add_argument("--seconds", type=float, default=1.)
    parser.add_argument("--search-seeds", type=int, nargs="+", default=[21, 22, 23])
    parser.add_argument("--orders", type=int, nargs="+", default=None,
                        help="Restrict to selected order-count strata")
    parser.add_argument("--limit-per-size", type=int, default=0,
                        help="Keep only the first N files per order-count stratum; 0 means all")
    args = parser.parse_args(argv)
    if args.seconds <= 0 or args.limit_per_size < 0 or not args.search_seeds:
        parser.error("seconds must be positive; limit-per-size must be nonnegative; search-seeds nonempty")
    catalog_path = args.catalog.resolve()
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))["instances"]
    entries = select_entries(catalog, args.orders, args.limit_per_size)
    if not entries:
        raise SystemExit("No compatible Kris instances selected")
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"Use a new benchmark directory: {output}")
    config = {
        "instances": [str((ROOT / row["file"]).resolve()) for row in entries],
        "methods": ["B0", "B2", "B3", "LNS", "ALNS", "VNS"],
        "references": ["B0", "B2", "B3", "LNS", "VNS"],
        "search_seeds": args.search_seeds,
        "search": {"seconds": args.seconds, "iterations": 100000, "segment": 10},
        "weights": [1 / 3, 1 / 3, 1 / 3],
    }
    rows = benchmark(config, output, progress=lambda row: print(
        f"{row['instance']} {row['method']} seed={row['search_seed']} F={row['objective']:.6f}", flush=True))
    source_selection = {
        "catalog": str(catalog_path),
        "catalog_sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        "selection_rule": "All catalog files, sorted by (order count, filename), unless --orders or --limit-per-size is supplied.",
        "entries": entries,
        "config": config,
        "runs": len(rows),
    }
    write_json(output / "source_selection.json", source_selection)
    print(f"Saved {len(rows)} runs from {len(entries)} Kris instances to {output}")
    if args.report_output is not None:
        from scripts.build_comparison_report import build_report

        build_report(output, args.report_output.resolve())
        print(f"Report tables/charts: {args.report_output.resolve()}")


if __name__ == "__main__":
    main()
