"""Re-audit saved benchmark JSON with its matching instance, independently of search."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.models import read_instance
from src.validator import validate_solution
from src.solver import fingerprint


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "results/smoke")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    instances, count = {}, 0
    for record in manifest["runs"]:
        result = json.loads((root / record["file"]).read_text(encoding="utf-8"))
        name = result["instance"]
        if name not in instances:
            instances[name] = read_instance(root / "instances" / f"{name}.json")
        errors = validate_solution(instances[name], result)
        actual_hash = fingerprint(instances[name])
        if result.get("instance_sha256") != actual_hash or record.get("instance_sha256") != actual_hash:
            errors.append("Instance SHA-256 mismatch")
        if errors:
            raise SystemExit(f"INVALID {record['file']}: {errors}")
        count += 1
    print(f"Revalidated {count} solutions across {len(instances)} instances")


if __name__ == "__main__":
    main()
