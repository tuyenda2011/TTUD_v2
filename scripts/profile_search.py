"""Sequential fixed-iteration profile; tracemalloc overhead is explicitly included."""
import argparse
import cProfile
from pathlib import Path
import sys
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from warehouse_opt.generator import generate
from warehouse_opt.models import write_json
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import solve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=False)
    for n in (20, 50, 100, 200):
        instance = generate(n, seed=901)
        profiler = cProfile.Profile()
        tracemalloc.start()
        profiler.enable()
        result = solve(instance, "ALNS", 42, SearchConfig(seconds=0, iterations=10))
        profiler.disable()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result["profile"] = {"peak_traced_bytes": peak, "instrumented": True}
        write_json(root / f"n{n}.json", result)
        profiler.dump_stats(str(root / f"n{n}.prof"))
        print(n, result["metrics"]["objective"], peak, flush=True)


if __name__ == "__main__":
    main()
