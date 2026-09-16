"""Create a self-contained example and real diagnostic figures inside this project."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from warehouse_opt.exact import solve_exact
from warehouse_opt.generator import generate
from warehouse_opt.models import write_json
from warehouse_opt.plots import convergence_figure, gantt_figure, warehouse_figure
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import solve


def main():
    output = ROOT / "results" / "demo"
    output.mkdir(parents=True, exist_ok=True)
    instance = generate(30, seed=42, pickers=3, capacity=20, tightness=.1)
    write_json(ROOT / "data" / "synthetic" / "demo_30.json", instance.to_dict())
    for method in ("B0", "B1", "B2", "B3", "LNS", "ALNS"):
        result = solve(instance, method, 42, SearchConfig(iterations=150, seconds=0, candidate_limit=16, max_removed=4, segment=10))
        write_json(output / f"{method}.json", result)
        print(f"{method}: {result['metrics']}", flush=True)
        if method == "ALNS":
            for name, fig in (("warehouse.png", warehouse_figure(instance, result, batch_id=result["batches"][0]["id"])), ("schedule.png", gantt_figure(instance, result)), ("convergence.png", convergence_figure(result))):
                fig.savefig(output / name, dpi=150)
                plt.close(fig)
    tiny = generate(4, seed=33, pickers=2, capacity=8, aisles=2, rows=2)
    write_json(ROOT / "data" / "synthetic" / "tiny_4.json", tiny.to_dict())
    exact = solve_exact(tiny)
    write_json(output / "tiny_exact.json", exact)
    print(f"Tiny exact: certified={exact['certified_optimal']}, states={exact['states']}")


if __name__ == "__main__":
    main()
