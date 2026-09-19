"""Bounded VNS: shaking followed by sampled variable-neighborhood descent."""
from dataclasses import asdict
import random
import time

from .heuristics import freeze, mutable
from .search import BudgetExpired, deadline_check, order_neighbor, schedule_neighbor


def batch_neighbor(ctx, plan, rng):
    candidate = mutable(plan)
    coordinates = [(p, i) for p, seq in enumerate(candidate) for i in range(len(seq))]
    if not coordinates:
        return plan
    p, i = rng.choice(coordinates)
    batch = candidate[p][i]
    if len(batch) > 1 and rng.random() < .5:
        selected = set(rng.sample(batch, rng.randint(1, len(batch) - 1)))
        candidate[p][i] = [o for o in batch if o not in selected]
        target = rng.randrange(len(candidate))
        candidate[target].insert(rng.randrange(len(candidate[target]) + 1), sorted(selected))
    elif len(coordinates) > 1:
        q, j = rng.choice([c for c in coordinates if c != (p, i)])
        if sum(ctx.loads[o] for o in batch + candidate[q][j]) > ctx.instance.operations.capacity + 1e-9:
            return plan
        candidate[q][j].extend(batch)
        candidate[p].pop(i)
    return freeze(candidate)


def optimize_vns(ctx, initial, seed, config, mode="2opt", deadline=None):
    started = time.perf_counter()
    deadline = deadline if deadline is not None else (started + config.seconds if config.seconds else float("inf"))
    rng = random.Random(seed)
    best, best_cost = initial, ctx.cost(initial, mode)
    initial_cost = best_cost
    trace = [{"iteration": 0, "seconds": 0., "objective": best_cost}]
    neighbors = [lambda p: order_neighbor(ctx, p, rng), lambda p: schedule_neighbor(p, rng),
                 lambda p: batch_neighbor(ctx, p, rng)]
    uses = [0, 0, 0]
    level, completed, accepted, evaluations = 1, 0, 0, 1
    reason = "iterations"
    try:
        for iteration in range(1, config.iterations + 1):
            deadline_check(deadline)
            candidate = best
            for _ in range(level):
                deadline_check(deadline)
                index = (level - 1) % len(neighbors)
                candidate = neighbors[index](candidate)
                uses[index] += 1
            cost = ctx.cost(candidate, mode)
            evaluations += 1
            neighborhood = 0
            # Bounded sampled descent; does not claim exhaustive local optimality.
            for _ in range(config.local_trials):
                deadline_check(deadline)
                trial = neighbors[neighborhood](candidate)
                uses[neighborhood] += 1
                trial_cost = ctx.cost(trial, mode)
                evaluations += 1
                if trial_cost < cost - 1e-12:
                    candidate, cost, neighborhood = trial, trial_cost, 0
                else:
                    neighborhood = (neighborhood + 1) % len(neighbors)
            completed = iteration
            if cost < best_cost - 1e-12:
                best, best_cost, level = candidate, cost, 1
                accepted += 1
                trace.append({"iteration": iteration, "seconds": time.perf_counter() - started, "objective": cost})
            else:
                level = level % 6 + 1
    except BudgetExpired:
        reason = "time_limit"
    ctx.check_plan(best)
    trace.append({"iteration": completed, "seconds": time.perf_counter() - started, "objective": best_cost})
    return best, {"seed": seed, "config": asdict(config), "initial_objective": initial_cost,
                  "iterations_completed": completed, "accepted": accepted, "stop_reason": reason,
                  "evaluations": evaluations, "neighborhood_uses": dict(zip(("order", "schedule", "batch"), uses)),
                  "variant": "VNS with bounded sampled descent; shaking levels 1..6", "trace": trace}
