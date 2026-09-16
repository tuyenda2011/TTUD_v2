import random

import pytest

from warehouse_opt.evaluator import Evaluator
from warehouse_opt.exact import solve_exact
from warehouse_opt.generator import generate
from warehouse_opt.heuristics import fcfs, list_schedule
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import solve
from warehouse_opt.validator import validate_solution
from warehouse_opt.vns import batch_neighbor, optimize_vns
from warehouse_opt.search import order_neighbor, schedule_neighbor


def test_vns_reproducible_and_common_initial():
    instance = generate(10, 22, capacity=10, aisles=3, rows=2)
    cfg = SearchConfig(seconds=0, iterations=30)
    first = solve(instance, "VNS", 7, cfg)
    second = solve(instance, "VNS", 7, cfg)
    assert first["plan"] == second["plan"]
    assert first["metrics"] == second["metrics"]
    assert first["search"]["initial_objective"] == solve(instance, "ALNS", 7, cfg)["search"]["initial_objective"]
    assert first["metrics"]["objective"] <= first["search"]["initial_objective"] + 1e-9
    assert validate_solution(instance, first) == []


def test_batch_moves_and_timeout():
    instance = generate(10, 4, capacity=30, aisles=2, rows=2)
    ctx = Evaluator(instance)
    plan = list_schedule(ctx, fcfs(ctx), "nn")
    ctx.set_reference(plan)
    counts = {sum(map(len, plan))}
    rng = random.Random(10)
    for _ in range(200):
        plan = batch_neighbor(ctx, plan, rng)
        ctx.check_plan(plan)
        counts.add(sum(map(len, plan)))
    assert len(counts) > 1
    best, meta = optimize_vns(ctx, plan, 42, SearchConfig(), deadline=0)
    assert best == plan
    assert meta["stop_reason"] == "time_limit"


def test_vns_above_exact():
    instance = generate(4, 33, pickers=2, capacity=8, aisles=2, rows=2)
    exact = solve_exact(instance)
    assert exact["certified_optimal"]
    result = solve(instance, "VNS", config=SearchConfig(seconds=0, iterations=50))
    assert result["metrics"]["objective"] >= exact["metrics"]["objective"] - 1e-9


@pytest.mark.parametrize("limit", [2, 10000])
def test_cached_cost_matches_full_after_moves(limit):
    instance = generate(20, 12, capacity=20)
    ctx = Evaluator(instance, cache_limit=limit)
    plan = list_schedule(ctx, fcfs(ctx), "nn")
    ctx.set_reference(plan)
    rng = random.Random(42)
    for _ in range(100):
        plan = order_neighbor(ctx, plan, rng)
        plan = schedule_neighbor(plan, rng)
        plan = batch_neighbor(ctx, plan, rng)
        assert ctx.cost(plan) == pytest.approx(ctx.evaluate(plan)["objective"], abs=1e-10)
        assert len(ctx.prefix_cache) <= limit
        assert len(ctx.info_cache) <= limit
        assert len(ctx.router.cache) <= limit
