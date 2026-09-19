"""Sequential acceptance benchmark for the demo upgrade; run in Conda TTUD."""
import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from warehouse_opt.generator import generate
from warehouse_opt.models import read_instance, write_json
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import solve
from warehouse_opt.validator import validate_solution


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/demo_upgrade_benchmark")
    args = parser.parse_args()
    output = ROOT / args.output
    catalog = json.loads((ROOT / "data/processed/kris_small/catalog.json").read_text(encoding="utf-8"))
    author_files = [min(r["file"] for r in catalog["instances"] if r["orders"] == n) for n in (6, 12, 18)]
    instances = [generate(n, 42, capacity=20) for n in (10, 30, 100)]
    instances += [read_instance(ROOT / path) for path in author_files]
    config = {"methods": ["B0", "B2", "ALNS", "VNS"], "search_seeds": [7, 42, 101],
              "seconds": [1, 3], "iterations": 2000, "synthetic_seed": 42,
              "synthetic_capacity": 20, "author_files": author_files}
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ("warehouse_opt", "demo") for p in sorted((ROOT / folder).glob("*.py"))}
    write_json(output / "config.json", config)
    rows, files = [], []
    started = time.perf_counter()
    for instance in instances:
        write_json(output / "instances" / f"{instance.name}.json", instance.to_dict())
        for budget in config["seconds"]:
            for method in config["methods"]:
                seeds = config["search_seeds"] if method in ("ALNS", "VNS") else [42]
                for seed in seeds:
                    result = solve(instance, method, seed, SearchConfig(seconds=budget, iterations=2000))
                    assert not validate_solution(instance, result)
                    initial = result["search"].get("initial_objective")
                    assert initial is None or result["metrics"]["objective"] <= initial + 1e-9
                    filename = f"raw/{instance.name}-{budget}s-{method}-{seed}.json"
                    write_json(output / filename, result)
                    files.append({"file": filename, "instance_sha256": result["instance_sha256"]})
                    row = {"instance": instance.name, "budget": budget, "method": method, "seed": seed,
                           "objective": result["metrics"]["objective"], **result["timing"],
                           "initialization_seconds": result["search"].get("initialization_seconds", 0),
                           "search_seconds": max(0, result["timing"]["optimization_seconds"] - result["search"].get("initialization_seconds", 0))}
                    rows.append(row)
                    print(f"{len(rows)}/96 {instance.name} {budget}s {method} seed={seed}", flush=True)
    summaries = []
    for instance in instances:
        for budget in config["seconds"]:
            for method in config["methods"]:
                group = [r for r in rows if (r["instance"], r["budget"], r["method"]) == (instance.name, budget, method)]
                summary = {"instance": instance.name, "budget": budget, "method": method, "runs": len(group)}
                for metric in ("objective", "preprocessing_seconds", "initialization_seconds", "search_seconds", "total_seconds"):
                    values = [r[metric] for r in group]
                    summary[metric] = {"median": statistics.median(values), "min": min(values), "max": max(values)}
                summaries.append(summary)
    write_json(output / "summary.json", summaries)
    write_json(output / "manifest.json", {"python": sys.version, "executable": sys.executable,
               "git_revision": revision, "working_tree_dirty": dirty, "source_sha256": hashes,
               "elapsed_seconds": time.perf_counter() - started, "runs": files})
    lines = ["# Demo upgrade benchmark", "", f"Python: `{sys.executable}`; sequential runs; 96 validated solutions.",
             "", "F and times: median [min, max], seeds 7/42/101 for search; deterministic methods once per budget.",
             "No claim that one search method always wins. Sources and revision are recorded in manifest.json.",
             "", "| Instance | Budget | Method | F | Init (s) | Search (s) | Total (s) |",
             "|---|---:|---|---|---|---|---|"]
    for row in summaries:
        values = [row[m] for m in ("objective", "initialization_seconds", "search_seconds", "total_seconds")]
        cells = [f"{v['median']:.4f} [{v['min']:.4f}, {v['max']:.4f}]" for v in values]
        lines.append(f"| {row['instance']} | {row['budget']} | {row['method']} | " + " | ".join(cells) + " |")
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
