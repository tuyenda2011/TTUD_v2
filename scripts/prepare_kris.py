"""Convert verified compatible author instances, retaining source fields and provenance."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.author_data import read_kris
from src.models import InputError, write_json


def main():
    raw = ROOT / "data" / "raw" / "KrisSmallDataCorrected"
    target = ROOT / "data" / "processed" / "kris_small"
    records, rejected = [], []
    for path in sorted(raw.rglob("*.txt")):
        try:
            instance = read_kris(path)
            dest = target / f"{path.stem}.json"
            write_json(dest, instance.to_dict())
            records.append({"file": dest.relative_to(ROOT).as_posix(), "raw_file": path.relative_to(ROOT).as_posix(),
                "orders": len(instance.orders), "products": len(instance.products), "nodes": len(instance.nodes),
                "pickers": instance.operations.pickers, "capacity": instance.operations.capacity,
                "sha256": instance.metadata["source_sha256"], "due_dates_regenerated": False})
        except InputError as exc:
            rejected.append({"file": path.relative_to(ROOT).as_posix(), "reason": str(exc)})
    if not records and not rejected:
        raise SystemExit("No raw Kris files found; extract the author archive first")
    write_json(target / "catalog.json", {"instances": records, "rejected": rejected})
    print(f"Converted {len(records)} original Kris instances, rejected {len(rejected)}")
    if records:
        print("First:", records[0])
    if rejected:
        print("First rejection:", rejected[0])


if __name__ == "__main__":
    main()
