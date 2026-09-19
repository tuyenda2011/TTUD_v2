import hashlib
import json
import platform
import random
import time
from dataclasses import asdict

from . import __version__
from .evaluator import Evaluator
from .heuristics import fcfs, greedy, list_schedule
from .models import InputError
from .search import BudgetExpired, SearchConfig, local_search, optimize
from .validator import validate_solution
from .vns import optimize_vns

METHODS = ("B0", "B1", "B2", "B3", "LNS", "ALNS", "VNS", "ALNS_NO_SCHEDULE", "ALNS_NO_2OPT", "B-S")


def fingerprint(instance):
    raw = json.dumps(instance.to_dict(), sort_keys=True, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def solve(instance, method="ALNS", seed=42, config=None, weights=(1/3, 1/3, 1/3)):
    if method not in METHODS:
        raise InputError(f"Unknown method {method}; choose {METHODS}")
    config = (config or SearchConfig()).validate()
    total_started = time.perf_counter()
    ctx = Evaluator(instance, config.cache_limit)
    baseline = list_schedule(ctx, fcfs(ctx), "nn")
    ctx.set_reference(baseline, weights)
    preprocessing = time.perf_counter() - total_started
    started = time.perf_counter()
    deadline = started + config.seconds if config.seconds else float("inf")
    metadata = {"seed": seed, "config": asdict(config)}
    initialization = 0.
    search_started = None
    if method == "B0":
        plan, mode = baseline, "nn"
    elif method == "B-S":
        mode = "s_shape"
        plan = list_schedule(ctx, fcfs(ctx), mode)
    else:
        mode = "nn" if method in ("B1", "ALNS_NO_2OPT") else "2opt"
        plan = list_schedule(ctx, greedy(ctx), mode)
        initial_objective = ctx.cost(plan, mode)
        initialization = time.perf_counter() - started
        search_started = time.perf_counter()
        if method == "B3":
            rng = random.Random(seed)
            iterations = 0
            for _ in range(config.iterations):
                try:
                    plan = local_search(ctx, plan, rng, 1, mode, deadline, schedule=True)
                    iterations += 1
                except BudgetExpired:
                    break
            metadata.update(iterations_completed=iterations, stop_reason="time_limit" if iterations < config.iterations else "iterations")
        elif method == "VNS":
            plan, metadata = optimize_vns(ctx, plan, seed, config, mode, deadline)
        elif method in ("LNS", "ALNS", "ALNS_NO_SCHEDULE", "ALNS_NO_2OPT"):
            plan, metadata = optimize(ctx, plan, seed, config, adaptive=method != "LNS", schedule=method != "ALNS_NO_SCHEDULE", mode=mode, deadline=deadline)
        metadata["initialization_seconds"] = initialization
        metadata["initial_objective"] = initial_objective
        for point in metadata.get("trace", []):
            point["seconds"] += initialization
    optimization = time.perf_counter() - started
    is_search = method in ("B3", "LNS", "ALNS", "VNS", "ALNS_NO_SCHEDULE", "ALNS_NO_2OPT")
    if not is_search:
        initialization = optimization
    search_seconds = time.perf_counter() - search_started if is_search and search_started is not None else 0.
    metadata.setdefault("iterations_completed", 0)
    metadata.setdefault("stop_reason", "heuristic_complete")
    metadata.setdefault("adaptation_updates", 0)
    metadata.setdefault("adapted_iterations", 0)
    metadata["initialization_seconds"] = initialization
    metadata["budget_scope"] = "initialization_and_search"
    metadata["search_executed"] = is_search and metadata["iterations_completed"] > 0
    metadata["cost_evaluations"] = ctx.cost_evaluations
    metadata["cache_entries"] = {"batch": len(ctx.info_cache), "route": len(ctx.router.cache), "prefix": len(ctx.prefix_cache)}
    result = ctx.evaluate(plan, mode, details=True)
    validation_started = time.perf_counter()
    errors = validate_solution(instance, result)
    validation_seconds = time.perf_counter() - validation_started
    if errors:
        raise RuntimeError("Internal solution validation failed: " + "; ".join(errors))
    result.update(method=method, feasible=True, search=metadata, instance_sha256=fingerprint(instance),
        timing={"preprocessing_seconds": preprocessing, "initialization_seconds": initialization,
                "search_seconds": search_seconds, "optimization_seconds": optimization,
                "validation_seconds": validation_seconds, "total_seconds": time.perf_counter() - total_started},
        environment={"python": platform.python_version(), "platform": platform.platform(), "cpu": platform.processor(), "package": __version__})
    return result
