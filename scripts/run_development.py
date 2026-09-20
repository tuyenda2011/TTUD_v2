"""Paired development experiments, separate from the final holdout."""
import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmark import benchmark
from src.models import InputError, write_json
from scripts.run_research import read, seal, source_hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists():
        raise InputError("Use a new experiment directory")
    variants = {
        "baseline": {},
        "incremental": {"incremental_validation": True},
        "deadline": {"destroy_operators": ["random", "related", "late", "batch", "delay_chain"]},
        "combined": {"incremental_validation": True, "destroy_operators": ["random", "related", "late", "batch", "delay_chain"]},
    }
    config = {"sizes": [10, 30, 100], "instance_seeds": [7203, 7204],
              "search_seeds": [31, 32, 33], "methods": ["B0", "ALNS"],
              "generator": {"pickers": 3, "capacity": 30, "aisles": 5, "rows": 6, "tightness": .15}}
    policy = {"variants": variants, "config": config, "source_sha256": source_hashes(),
              "selection": "Keep incremental only if fixed-iteration plans match and median runtime improves >=5%. Keep delay_chain only if mean paired F improves >=1% with no instance mean worsening >5% on equal-time development. Otherwise retain baseline operators. Holdout is not used."}
    seal(root / "development.lock.json", policy)
    results = {}
    for regime, search in (("iterations", {"seconds": 0, "iterations": 20, "segment": 5}),
                            ("time", {"seconds": 1, "iterations": 100000, "segment": 10})):
        for name, changes in variants.items():
            if regime == "iterations" and name not in ("baseline", "incremental"):
                continue
            cfg = {**config, "search": {**search, **changes}}
            rows = benchmark(cfg, root / regime / name)
            results[regime, name] = {(r["instance"], r["search_seed"]): r for r in rows if r["method"] == "ALNS"}
            print(regime, name, len(rows), flush=True)
    old, new = results["iterations", "baseline"], results["iterations", "incremental"]
    same = all(abs(old[k]["objective"] - new[k]["objective"]) < 1e-10 for k in old)
    same_plans = all(
        read(root / "iterations" / "baseline" / "raw" / f"{name}-ALNS-seed{seed}.json")["plan"]
        == read(root / "iterations" / "incremental" / "raw" / f"{name}-ALNS-seed{seed}.json")["plan"]
        for name, seed in old)
    speedup = statistics.median((old[k]["optimization_seconds"] - new[k]["optimization_seconds"]) / old[k]["optimization_seconds"] for k in old)
    keep_incremental = same and same_plans and speedup >= .05
    base_name = "incremental" if keep_incremental else "baseline"
    candidate_name = "combined" if keep_incremental else "deadline"
    ref, candidate = results["time", base_name], results["time", candidate_name]
    improvements = []
    for instance in sorted({key[0] for key in ref}):
        keys = [key for key in ref if key[0] == instance]
        a = statistics.mean(ref[k]["objective"] for k in keys)
        b = statistics.mean(candidate[k]["objective"] for k in keys)
        improvements.append((a - b) / a if a else 0.)
    keep_deadline = statistics.mean(improvements) >= .01 and min(improvements) >= -.05
    chosen = ("combined" if keep_deadline else "incremental") if keep_incremental else ("deadline" if keep_deadline else "baseline")
    seal(root / "decision.json", {"fixed_iteration_F_equal": same, "fixed_iteration_plans_equal": same_plans, "median_runtime_improvement": speedup,
         "deadline_mean_F_improvement": statistics.mean(improvements), "deadline_instance_improvements": improvements,
         "selected": chosen, "search_changes": variants[chosen], "policy": policy["selection"]})
    print("Selected", chosen, "runtime improvement", speedup, "deadline improvement", statistics.mean(improvements), flush=True)


if __name__ == "__main__":
    main()
