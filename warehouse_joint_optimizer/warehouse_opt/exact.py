"""Full enumeration oracle for tiny instances, including partition AND picker schedules."""
from itertools import permutations, product
import time

from .evaluator import Evaluator
from .heuristics import fcfs, freeze, list_schedule
from .models import InputError
from .search import BudgetExpired, deadline_check
from .validator import validate_solution


def partitions(order_ids, loads, capacity):
    blocks = []
    def visit(index):
        if index == len(order_ids):
            yield tuple(tuple(b) for b in blocks)
            return
        oid = order_ids[index]
        for batch in blocks:
            if sum(loads[o] for o in batch) + loads[oid] <= capacity + 1e-9:
                batch.append(oid)
                yield from visit(index + 1)
                batch.pop()
        blocks.append([oid])
        yield from visit(index + 1)
        blocks.pop()
    yield from visit(0)


def solve_exact(instance, seconds=30., max_states=200000):
    if len(instance.orders) > 6 or len({p.location for p in instance.products} - {instance.depot}) > 8:
        raise InputError("Exact joint enumeration is restricted to <=6 orders and <=8 non-depot SKU locations")
    from .models import number
    number(seconds, "exact seconds", strict=True)
    if type(max_states) is not int or max_states < 1:
        raise InputError("max_states must be positive")
    started = time.perf_counter()
    deadline = started + seconds
    ctx = Evaluator(instance)
    baseline = list_schedule(ctx, fcfs(ctx), "nn")
    ctx.set_reference(baseline)
    best = list_schedule(ctx, fcfs(ctx), "exact")
    best_cost = ctx.cost(best, "exact")
    states, certified = 0, True
    try:
        for batches in partitions(sorted(ctx.orders), ctx.loads, instance.operations.capacity):
            for assignment in product(range(instance.operations.pickers), repeat=len(batches)):
                deadline_check(deadline)
                per_picker = [[i for i, picker in enumerate(assignment) if picker == p] for p in range(instance.operations.pickers)]
                for schedules in product(*(permutations(indices) for indices in per_picker)):
                    deadline_check(deadline)
                    if states >= max_states:
                        raise BudgetExpired
                    plan = freeze([[batches[index] for index in seq] for seq in schedules])
                    cost = ctx.cost(plan, "exact")
                    states += 1
                    if cost < best_cost - 1e-12:
                        best, best_cost = plan, cost
    except BudgetExpired:
        certified = False
    result = ctx.evaluate(best, "exact", details=True)
    errors = validate_solution(instance, result)
    if errors:
        raise RuntimeError("; ".join(errors))
    result.update(method="EXACT", feasible=True, certified_optimal=certified, states=states, elapsed_seconds=time.perf_counter() - started)
    return result
