"""Create a deterministic, independently audited offline presentation snapshot."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from warehouse_opt.demo_snapshot import validate_snapshot
from warehouse_opt.models import read_instance, write_json
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import solve


if __name__ == "__main__":
    instance = read_instance(ROOT / "data/processed/kris_small/instances_103_1.json")
    cfg = SearchConfig(seconds=0, iterations=100)
    results = {m: solve(instance, m, 42, cfg) for m in ("B0", "B3", "LNS", "ALNS", "VNS")}
    snapshot = {"instance": instance.to_dict(), "results": results, "seed": 42, "budget": 0,
                "saved_playback": True, "iterations": 100}
    validate_snapshot(snapshot)
    write_json(ROOT / "results/demo_vns/snapshot.json", snapshot)
    print({m: r["metrics"]["objective"] for m, r in results.items()})
