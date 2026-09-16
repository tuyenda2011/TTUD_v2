import copy
from dataclasses import replace
import json
import random
import subprocess
import sys

import pytest

from warehouse_opt.evaluator import Evaluator, Objective
from warehouse_opt.exact import solve_exact
from warehouse_opt.generator import generate
from warehouse_opt.heuristics import fcfs, freeze, list_schedule
from warehouse_opt.models import Edge, InputError, Instance, Node, Operations, Order, Product, read_instance, write_json
from warehouse_opt.search import SearchConfig, destroy, optimize, repair, schedule_neighbor
from warehouse_opt.solver import METHODS, solve
from warehouse_opt.validator import validate_solution


@pytest.fixture
def simple():
    return Instance("hand-check", "D", [Node("D", 0, 0), Node("A", 10, 0), Node("B", 20, 0)],
        [Edge("D", "A", 10), Edge("A", "B", 10)],
        [Product("X", "A", 1., .5), Product("Y", "B", 1., .5)],
        [Order("o1", {"X": 2}, 4., 0), Order("o2", {"X": 1}, 10., 1)],
        Operations(pickers=2, capacity=3, speed=10., location_minutes=1., batch_minutes=1.))


def context(instance):
    ctx = Evaluator(instance)
    ctx.set_reference(list_schedule(ctx, fcfs(ctx), "nn"))
    return ctx


def test_hand_calculation_shared_location(simple):
    ctx = context(simple)
    result = ctx.evaluate(((('o1', 'o2'),), ()), details=True)
    assert result["metrics"]["distance"] == 20
    assert result["metrics"]["makespan"] == 5.5  # 1 setup + 2 travel + 1 location + 1.5 items
    assert result["metrics"]["tardiness"] == 1.5
    assert result["metrics"]["late_orders"] == 1
    assert result["batches"][0]["load"] == 3
    assert result["picker_ends"] == [5.5, 0]
    assert validate_solution(simple, result) == []


def test_downstream_recomputed(simple):
    ctx = context(simple)
    first = ctx.evaluate(((('o1',), ('o2',)), ()), details=True)
    second = ctx.evaluate(((('o2',), ('o1',)), ()), details=True)
    assert first["batches"][1]["start"] == 5.
    assert second["batches"][1]["start"] == 4.5
    assert first["metrics"]["tardiness"] != second["metrics"]["tardiness"]


def test_graph_shortest_path_is_not_straight_line(simple):
    simple.nodes[2] = Node("B", 0, 1)  # Drawing coordinates do not change edge distance.
    ctx = context(simple)
    assert ctx.graph.distance("D", "B") == 20
    assert ctx.graph.path("D", "B") == ("D", "A", "B")


@pytest.mark.parametrize("mutation", [
    lambda x: setattr(x, "directed", True),
    lambda x: setattr(x, "orders", []),
    lambda x: x.orders.append(x.orders[0]),
    lambda x: x.edges.pop(),
    lambda x: x.edges.append(Edge("A", "D", 10)),
    lambda x: x.edges.__setitem__(0, Edge("D", "A", -1)),
    lambda x: x.products.__setitem__(0, Product("X", "missing")),
    lambda x: x.orders.__setitem__(0, Order("o1", {"X": 4}, 4, 0)),
    lambda x: x.orders.__setitem__(0, Order("o1", {"X": 1.5}, 4, 0)),
    lambda x: x.orders.__setitem__(0, Order("o1", {"X": True}, 4, 0)),
    lambda x: x.orders.__setitem__(0, Order("o1", {"X": 1}, float("nan"), 0)),
    lambda x: setattr(x, "operations", Operations(speed=0)),
    lambda x: setattr(x, "operations", Operations(pickers=True)),
])
def test_rejects_invalid_input(simple, mutation):
    mutation(simple)
    with pytest.raises(InputError):
        simple.validate()


@pytest.mark.parametrize("plan", [((('o1',),), ()), ((('o1', 'o1'),), (('o2',),)), (((),), (('o1', 'o2'),)), ((('unknown',),), ()), ((('o1', 'o2'),),)])
def test_invalid_plan(simple, plan):
    with pytest.raises(InputError):
        context(simple).evaluate(plan)


@pytest.mark.parametrize("field", ["load", "distance", "duration", "start", "end", "tardiness"])
def test_validator_detects_tampered_batch(simple, field):
    result = context(simple).evaluate(((('o1', 'o2'),), ()), details=True)
    result["batches"][0][field] += 1
    assert validate_solution(simple, result)


def test_validator_detects_illegal_walk_and_loss(simple):
    result = context(simple).evaluate(((('o1', 'o2'),), ()), details=True)
    result["batches"][0]["walk"] = ['D', 'B', 'D']
    assert validate_solution(simple, result)
    result = context(simple).evaluate(((('o1', 'o2'),), ()), details=True)
    result["orders"].pop()
    assert validate_solution(simple, result)


def test_zero_distance_and_depot_service(simple):
    simple.products[0] = Product("X", "D", 1, 0)
    simple.operations = replace(simple.operations, location_minutes=0, batch_minutes=0)
    result = solve(simple, "B0")
    assert result["metrics"]["objective"] == 0
    assert result["objective_config"]["distance_ref"] == 1
    assert result["batches"][0]["walk"] == ["D"]
    assert validate_solution(simple, result) == []


def test_quantity_sensitive_cache(simple):
    ctx = context(simple)
    _, a, p1 = ctx.batch_info(('o1',))
    _, b, p2 = ctx.batch_info(('o2',))
    assert a is b  # same route can be reused
    assert p1 - p2 == .5  # item handling cannot be reused blindly


def test_seeded_generation_roundtrip(tmp_path):
    first, second = generate(12, 17), generate(12, 17)
    assert first.to_dict() == second.to_dict()
    assert first.to_dict() != generate(12, 18).to_dict()
    path = tmp_path / "instance.json"
    write_json(path, first.to_dict())
    assert read_instance(path).to_dict() == first.to_dict()
    with pytest.raises(FileNotFoundError):
        read_instance(tmp_path / "missing.json")


def test_two_opt_preserves_coverage_and_improves():
    ctx = context(generate(20, 42))
    locations = set().union(*ctx.locations.values())
    before = ctx.router.route(locations, "nn")
    after = ctx.router.route(locations, "2opt")
    assert after.distance <= before.distance + 1e-9
    assert set(before.stops) == set(after.stops)
    assert after.distance == pytest.approx(ctx.graph.walk_distance(after.walk))


@pytest.mark.parametrize("method", METHODS)
def test_all_methods_return_feasible(method):
    instance = generate(10, 8, capacity=10, aisles=3, rows=3, tightness=.05)
    result = solve(instance, method, 9, SearchConfig(iterations=8, seconds=0, segment=2, candidate_limit=8, local_every=2))
    assert result["feasible"]
    assert validate_solution(instance, result) == []


@pytest.mark.parametrize("operator", ["random", "related", "late", "batch"])
@pytest.mark.parametrize("insertion", ["greedy", "regret2"])
def test_destroy_repair_never_loses_orders(operator, insertion):
    instance = generate(8, 3, capacity=8, aisles=2, rows=2)
    ctx = context(instance)
    plan = list_schedule(ctx, fcfs(ctx), "2opt")
    config = SearchConfig(seconds=0, candidate_limit=0)
    rng = random.Random(5)
    partial, removed = destroy(ctx, plan, operator, rng, config)
    candidate = repair(ctx, partial, removed, insertion, rng, config, "2opt", float("inf"))
    assert validate_solution(instance, ctx.evaluate(candidate, details=True)) == []


def test_alns_determinism_adaptation_and_best():
    instance = generate(10, 22, capacity=10, aisles=3, rows=2)
    cfg = SearchConfig(iterations=20, seconds=0, candidate_limit=8, segment=4, local_every=2)
    a, b = solve(instance, "ALNS", 7, cfg), solve(instance, "ALNS", 7, cfg)
    assert a["plan"] == b["plan"]
    assert a["metrics"] == b["metrics"]
    assert a["search"]["operator_weights"] == b["search"]["operator_weights"]
    assert any(w != 1 for w in a["search"]["operator_weights"].values())
    assert a["metrics"]["objective"] <= solve(instance, "B2")["metrics"]["objective"] + 1e-9
    lns = solve(instance, "LNS", 7, cfg)
    assert set(lns["search"]["operator_weights"].values()) == {1.}


def test_timeout_returns_complete_initial_solution(simple):
    ctx = context(simple)
    plan = list_schedule(ctx, fcfs(ctx), "2opt")
    best, metadata = optimize(ctx, plan, deadline=0.)
    assert best == plan
    assert metadata["stop_reason"] == "time_limit"
    assert validate_solution(simple, ctx.evaluate(best, details=True)) == []


def test_schedule_neighborhood_can_change_picker(simple):
    plan = ((('o1',), ('o2',)), ())
    candidates = [schedule_neighbor(plan, random.Random(seed)) for seed in range(30)]
    assert any(candidate[1] for candidate in candidates)
    assert any(candidate[0] and candidate[0][0] == ('o2',) for candidate in candidates)


def test_exact_joint_matches_hand_case(simple):
    result = solve_exact(simple)
    # batching both gives F=2/3 + 1.5/(3*11); splitting uses more distance.
    assert result["certified_optimal"]
    assert result["metrics"]["distance"] == 20
    assert result["metrics"]["objective"] == pytest.approx(2/3 + 1.5/33)
    assert result["states"] > 1
    bounded = solve_exact(simple, max_states=1)
    assert not bounded["certified_optimal"]


def test_heuristics_above_exact_tiny():
    instance = generate(4, 33, pickers=2, capacity=8, aisles=2, rows=2)
    exact = solve_exact(instance, seconds=10)
    assert exact["certified_optimal"]
    for method in ("B0", "B1", "B2", "B3", "ALNS"):
        result = solve(instance, method, config=SearchConfig(iterations=5, seconds=0))
        assert result["metrics"]["objective"] >= exact["metrics"]["objective"] - 1e-9


def test_s_shape_rejects_unverified_layout(simple):
    with pytest.raises(InputError):
        solve(simple, "B-S")


def test_cli_roundtrip(tmp_path):
    instance, result = tmp_path / "instance.json", tmp_path / "result.json"
    for arguments in [
        ["generate", "--orders", "5", "--output", str(instance)],
        ["solve", str(instance), "--method", "ALNS", "--iterations", "3", "--seconds", "0", "--output", str(result)],
        ["validate", str(instance), str(result)],
    ]:
        completed = subprocess.run([sys.executable, "-m", "warehouse_opt", *arguments], capture_output=True, text=True)
        assert completed.returncode == 0, completed.stderr


def test_invalid_search_config():
    for cfg in [SearchConfig(seconds=-1), SearchConfig(candidate_limit=-1), SearchConfig(cooling=1), SearchConfig(segment=0)]:
        with pytest.raises(InputError):
            cfg.validate()
    with pytest.raises(InputError):
        Objective(1, 1, 1, (0, .5, .5))
