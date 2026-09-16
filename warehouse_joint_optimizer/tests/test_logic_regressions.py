from dataclasses import replace

import pytest

from warehouse_opt.benchmark import benchmark
from warehouse_opt.evaluator import Evaluator
from warehouse_opt.generator import generate
from warehouse_opt.models import InputError, write_json
from warehouse_opt.solver import solve
from warehouse_opt.validator import validate_solution


@pytest.mark.parametrize("mode", ["nn", "2opt", "exact", "s_shape"])
def test_routing_accepts_one_shot_locations(mode):
    ctx = Evaluator(generate(3, 7, aisles=2, rows=2))
    locations = [p.location for p in ctx.instance.products]
    actual = ctx.router.route(iter(locations), mode)
    assert set(actual.stops) == set(locations) | {ctx.instance.depot}
    assert actual.distance > 0
    assert actual == ctx.router.route(locations, mode)


def test_batch_iterator_does_not_poison_cache():
    ctx = Evaluator(generate(3, 7, aisles=2, rows=2))
    ids = tuple(ctx.orders)
    actual = ctx.batch_info(iter(ids))
    expected = Evaluator(ctx.instance).batch_info(ids)
    assert actual == expected
    assert ctx.batch_info(ids) == expected


def test_partial_on_time_rate_counts_only_served_orders():
    instance = generate(3, 7)
    instance.orders = [replace(o, due=0) for o in instance.orders]
    ctx = Evaluator(instance)
    plan = (((instance.orders[0].id,),), (), ())
    assert ctx.evaluate(plan, partial=True)["on_time_rate"] == 0
    assert ctx.evaluate(((), (), ()), partial=True)["on_time_rate"] == 1


@pytest.mark.parametrize("field,value", [("schema_version", 2), ("schema_version", True),
                                         ("objective_config", []), ("objective_config", {})])
def test_validator_rejects_invalid_schema_and_objective(field, value):
    instance = generate(3, 7)
    result = solve(instance, "B0")
    result["metrics"].pop("objective")
    result["objective_config"] = None
    result[field] = value
    assert validate_solution(instance, result)


@pytest.mark.parametrize("uppercase", [False, True])
def test_benchmark_rejects_duplicate_names_before_writing_results(tmp_path, uppercase):
    first = generate(2, 7)
    second = generate(2, 8)
    second.name = first.name.upper() if uppercase else first.name
    paths = [tmp_path / "one.json", tmp_path / "two.json"]
    for path, instance in zip(paths, (first, second)):
        write_json(path, instance.to_dict())
    output = tmp_path / "results"
    with pytest.raises(InputError, match="unique"):
        benchmark({"instances": [str(p) for p in paths], "methods": ["B0"]}, output)
    assert not output.exists()
