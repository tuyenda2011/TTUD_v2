import argparse
import json
from pathlib import Path

from .benchmark import benchmark
from .exact import solve_exact
from .generator import MAP_SCENARIOS, generate, generate_scenario
from .models import InputError, read_instance, write_json
from .search import SearchConfig
from .solver import METHODS, solve
from .validator import validate_solution


def main(argv=None):
    parser = argparse.ArgumentParser(description="Warehouse batching + routing + picker scheduling")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="Generate a reproducible synthetic instance")
    gen.add_argument("--scenario", choices=list(MAP_SCENARIOS.keys()), default=None,
                     help="Predefined warehouse scenario (single_block, double_block, mega_hub, rush_hour, abc_zonal)")
    gen.add_argument("--orders", type=int, default=None)
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--pickers", type=int, default=None)
    gen.add_argument("--capacity", type=float, default=None)
    gen.add_argument("--aisles", type=int, default=None)
    gen.add_argument("--rows", type=int, default=None)
    gen.add_argument("--tightness", type=float, default=None)
    gen.add_argument("--output", required=True)
    run = sub.add_parser("solve", help="Optimize a schema-v1 JSON instance")
    run.add_argument("instance")
    run.add_argument("--method", choices=METHODS, default="ALNS")
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--seconds", type=float, default=3.)
    run.add_argument("--iterations", type=int, default=200)
    run.add_argument("--candidate-limit", type=int, default=24)
    run.add_argument("--weights", type=float, nargs=3, default=[1/3, 1/3, 1/3], metavar=("DISTANCE", "MAKESPAN", "TARDINESS"))
    run.add_argument("--output", required=True)
    validate = sub.add_parser("validate", help="Independently validate exported solution")
    validate.add_argument("instance")
    validate.add_argument("solution")
    exact = sub.add_parser("exact", help="Full enumeration for tiny instances")
    exact.add_argument("instance")
    exact.add_argument("--seconds", type=float, default=30.)
    exact.add_argument("--max-states", type=int, default=200000)
    exact.add_argument("--output", required=True)
    bench = sub.add_parser("benchmark", help="Run config JSON, save raw and aggregate results")
    bench.add_argument("--config", default="configs/smoke.json")
    bench.add_argument("--output", default="results/smoke")
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            if args.scenario:
                overrides = {}
                if args.orders is not None:
                    overrides["n"] = args.orders
                if args.pickers is not None:
                    overrides["pickers"] = args.pickers
                if args.capacity is not None:
                    overrides["capacity"] = args.capacity
                if args.aisles is not None:
                    overrides["aisles"] = args.aisles
                if args.rows is not None:
                    overrides["rows"] = args.rows
                if args.tightness is not None:
                    overrides["tightness"] = args.tightness
                instance = generate_scenario(args.scenario, seed=args.seed, **overrides)
            else:
                orders = 30 if args.orders is None else args.orders
                pickers = 3 if args.pickers is None else args.pickers
                capacity = 30. if args.capacity is None else args.capacity
                aisles = 5 if args.aisles is None else args.aisles
                rows = 6 if args.rows is None else args.rows
                tightness = .25 if args.tightness is None else args.tightness
                instance = generate(orders, args.seed, pickers, capacity, aisles, rows, tightness)
            write_json(args.output, instance.to_dict())
            print(f"Generated {instance.name}: {len(instance.orders)} orders -> {args.output}")
        elif args.command == "solve":
            config = SearchConfig(seconds=args.seconds, iterations=args.iterations, candidate_limit=args.candidate_limit)
            result = solve(read_instance(args.instance), args.method, args.seed, config, args.weights)
            write_json(args.output, result)
            print(json.dumps(result["metrics"], indent=2))
            print(f"Validated solution -> {args.output}")
        elif args.command == "validate":
            result = json.loads(Path(args.solution).read_text(encoding="utf-8"))
            errors = validate_solution(read_instance(args.instance), result)
            if errors:
                raise InputError("; ".join(errors))
            print("VALID: orders, capacity, physical paths, timing and metrics")
        elif args.command == "exact":
            result = solve_exact(read_instance(args.instance), args.seconds, args.max_states)
            write_json(args.output, result)
            print(f"Certified optimal: {result['certified_optimal']}; evaluated states: {result['states']}")
        else:
            config = json.loads(Path(args.config).read_text(encoding="utf-8"))
            rows = benchmark(config, args.output, progress=lambda row: print(f"{row['instance']} {row['method']} seed={row['search_seed']} F={row['objective']:.5f}", flush=True))
            print(f"Saved {len(rows)} runs to {args.output}")
    except (InputError, OSError, json.JSONDecodeError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
