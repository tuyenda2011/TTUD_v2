"""Stratified, preregistered check on existing Kris data; no new tuning."""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_research import digest, read, run_benchmark, seal, selection, verify_aggregates
from src.models import InputError, read_instance, write_json
from src.solver import fingerprint
from src.validator import validate_solution


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise InputError("Use a new external-check directory")
    strata = defaultdict(list)
    for row in sorted(read(ROOT / "data/processed/kris_small/catalog.json")["instances"], key=lambda r: r["file"]):
        strata[row["orders"]].append(row)
    entries = [r for size in sorted(strata) for r in strata[size][:2]]
    if not entries:
        raise InputError("No compatible Kris data")
    for row in entries:
        instance = read_instance(ROOT / row["file"])
        if instance.metadata["source_sha256"] != row["sha256"] or digest(ROOT / row["raw_file"]) != row["sha256"]:
            raise InputError(f"Source provenance mismatch: {row['file']}")
    config = {"instances": [str((ROOT / r["file"]).resolve()) for r in entries],
              "search_seeds": [21, 22, 23], "methods": ["B0", "B2", "B3", "LNS", "ALNS", "VNS"],
              "search": selection(args.study), "weights": read(args.study / "protocol.lock.json")["protocol"]["primary_weights"]}
    seal(args.output / "external.lock.json", {"rule": "First two filenames lexicographically per order-count stratum; three search seeds; no outcome-based selection.",
         "entries": entries, "config": config, "selection_sha256": digest(args.study / "selection.lock.json"),
         "limitation": "Project soft deadlines/objective in unchanged source units; not a reproduction of JOBPRSP-D or comparison to source best-known values. Licensing is not inferred from download availability."})
    target = args.output / "benchmark"
    run_benchmark(config, target)
    results = []
    for record in read(target / "manifest.json")["runs"]:
        result = read(target / record["file"])
        instance = read_instance(target / "instances" / f"{result['instance']}.json")
        assert fingerprint(instance) == result["instance_sha256"] == record["instance_sha256"]
        assert not validate_solution(instance, result)
        results.append(result)
    assert len(results) == len(entries) * 14
    verify_aggregates(target, results)
    write_json(args.output / "verification.json", {"solutions": len(results), "instances": len(entries), "source_hashes_verified": True})
    print(f"Verified {len(results)} external-data solutions", flush=True)


if __name__ == "__main__":
    main()
