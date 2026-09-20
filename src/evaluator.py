"""Shared objective and complete schedule recomputation (no stale downstream times)."""
from dataclasses import asdict, dataclass
from collections import Counter
import math

from .graph import WarehouseGraph
from .models import InputError
from .routing import Router
from .cache import BoundedCache

# Immutable state: picker -> ordered batches -> order IDs. Routes are decoded by Router.
Plan = tuple[tuple[tuple[str, ...], ...], ...]


@dataclass(frozen=True)
class Objective:
    distance_ref: float
    completion_ref: float
    tardiness_ref: float
    weights: tuple[float, float, float] = (1 / 3, 1 / 3, 1 / 3)

    def __post_init__(self):
        if len(self.weights) != 3 or any(not math.isfinite(w) or w <= 0 for w in self.weights) or not math.isclose(sum(self.weights), 1):
            raise InputError("Objective weights must be three positive finite values summing to 1")
        if any(not math.isfinite(r) or r <= 0 for r in (self.distance_ref, self.completion_ref, self.tardiness_ref)):
            raise InputError("Objective references must be finite and positive")

    def score(self, distance, makespan, tardiness):
        return sum(w * value / ref for w, value, ref in zip(self.weights, (distance, makespan, tardiness), (self.distance_ref, self.completion_ref, self.tardiness_ref)))


class Evaluator:
    def __init__(self, instance, cache_limit=10000, incremental_validation=False):
        self.instance = instance.validate()
        self.graph = WarehouseGraph(instance)
        self.router = Router(instance, self.graph)
        self.router.cache = BoundedCache(cache_limit)
        self.orders = {o.id: o for o in instance.orders}
        self.products = {p.id: p for p in instance.products}
        self.loads = {o.id: sum(self.products[s].size * q for s, q in o.items.items()) for o in instance.orders}
        self.locations = {o.id: frozenset(self.products[s].location for s in o.items) for o in instance.orders}
        self.pick_times = {o.id: sum(self.products[s].pick_minutes * q for s, q in o.items.items()) for o in instance.orders}
        self.info_cache = BoundedCache(cache_limit)
        self.prefix_cache = BoundedCache(cache_limit)
        self.incremental_validation = incremental_validation
        self.sequence_masks = BoundedCache(cache_limit)
        self.order_bits = {oid: 1 << i for i, oid in enumerate(self.orders)}
        self.all_order_bits = (1 << len(self.orders)) - 1
        self.cost_evaluations = 0
        self.objective = None

    def batch_info(self, orders, mode="2opt"):
        orders = tuple(orders)
        key = (tuple(sorted(orders)), mode)
        if key not in self.info_cache:
            locations = frozenset().union(*(self.locations[o] for o in orders))
            route = self.router.route(locations, mode)
            op = self.instance.operations
            duration = op.batch_minutes + route.distance / op.speed + op.location_minutes * len(locations) + sum(self.pick_times[o] for o in orders)
            self.info_cache[key] = (sum(self.loads[o] for o in orders), route, duration)
        return self.info_cache[key]

    def check_plan(self, plan, partial=False):
        if len(plan) != self.instance.operations.pickers:
            raise InputError("Plan must contain exactly one sequence for each picker")
        if self.incremental_validation:
            visited = 0
            for sequence in plan:
                key = tuple(tuple(batch) for batch in sequence)
                mask = self.sequence_masks.get(key)
                if mask is None:
                    mask = 0
                    for batch in key:
                        if not batch:
                            raise InputError("Empty batch")
                        load = 0.
                        for oid in batch:
                            if oid not in self.order_bits:
                                raise InputError("Unknown order in plan")
                            bit = self.order_bits[oid]
                            if mask & bit:
                                raise InputError("Order appears more than once")
                            mask |= bit
                            load += self.loads[oid]
                        if load > self.instance.operations.capacity + 1e-9:
                            raise InputError("Batch exceeds capacity")
                    self.sequence_masks[key] = mask
                if visited & mask:
                    raise InputError("Order appears more than once")
                visited |= mask
            if not partial and visited != self.all_order_bits:
                raise InputError("Plan does not serve every order exactly once")
            return
        visited = []
        for sequence in plan:
            for batch in sequence:
                if not batch:
                    raise InputError("Empty batch")
                if any(o not in self.orders for o in batch):
                    raise InputError("Unknown order in plan")
                if sum(self.loads[o] for o in batch) > self.instance.operations.capacity + 1e-9:
                    raise InputError("Batch exceeds capacity")
                visited.extend(batch)
        if any(count != 1 for count in Counter(visited).values()):
            raise InputError("Order appears more than once")
        if not partial and set(visited) != set(self.orders):
            raise InputError("Plan does not serve every order exactly once")

    def evaluate(self, plan, mode="2opt", partial=False, details=False):
        self.check_plan(plan, partial)
        distance, makespan, tardiness, late = 0., 0., 0., 0
        batches, orders_out, picker_ends = [], [], []
        for picker, sequence in enumerate(plan):
            end = 0.
            for position, order_ids in enumerate(sequence):
                load, route, duration = self.batch_info(order_ids, mode)
                start, end = end, end + duration
                distance += route.distance
                batch_id = f"P{picker + 1}-B{position + 1}"
                batch_late = 0.
                for oid in order_ids:
                    loss = max(0., end - self.orders[oid].due)
                    tardiness += loss
                    batch_late += loss
                    late += int(loss > 1e-9)
                    if details:
                        orders_out.append({"id": oid, "batch": batch_id, "picker": picker + 1, "due": self.orders[oid].due, "completion": end, "tardiness": loss})
                if details:
                    batches.append({"id": batch_id, "picker": picker + 1, "position": position, "orders": list(order_ids), "load": load, "stops": list(route.stops), "walk": list(route.walk), "distance": route.distance, "duration": duration, "start": start, "end": end, "tardiness": batch_late})
            picker_ends.append(end)
            makespan = max(makespan, end)
        served = sum(len(batch) for sequence in plan for batch in sequence)
        metrics = {"distance": distance, "makespan": makespan, "tardiness": tardiness, "late_orders": late, "batches": sum(len(s) for s in plan), "used_pickers": sum(bool(s) for s in plan), "on_time_rate": 1 - late / served if served else 1.}
        if self.objective is not None:
            metrics["objective"] = self.objective.score(distance, makespan, tardiness)
        if not details:
            return metrics
        return {"schema_version": 1, "instance": self.instance.name, "routing": mode, "plan": [[list(b) for b in seq] for seq in plan], "metrics": metrics, "batches": batches, "orders": orders_out, "picker_ends": picker_ends, "objective_config": asdict(self.objective) if self.objective else None}

    def set_reference(self, baseline, weights=(1 / 3, 1 / 3, 1 / 3)):
        raw = self.evaluate(baseline, "nn")
        completion = max(raw["makespan"], 1.)
        self.objective = Objective(max(raw["distance"], 1.), completion, len(self.orders) * completion, tuple(weights))

    def cost(self, plan, mode="2opt", partial=False):
        if self.objective is None:
            raise InputError("Set B0 objective references before comparing solutions")
        self.check_plan(plan, partial)
        self.cost_evaluations += 1
        distance = tardiness = makespan = 0.
        for sequence in plan:
            sequence = tuple(tuple(batch) for batch in sequence)
            end = traveled = late = 0.
            offset = 0
            for length in range(len(sequence), 0, -1):
                cached = self.prefix_cache.get((mode, sequence[:length]))
                if cached is not None:
                    end, traveled, late = cached
                    offset = length
                    break
            for index in range(offset, len(sequence)):
                batch = sequence[index]
                _, route, duration = self.batch_info(batch, mode)
                end += duration
                traveled += route.distance
                late += sum(max(0., end - self.orders[o].due) for o in batch)
                self.prefix_cache[(mode, sequence[:index + 1])] = (end, traveled, late)
            distance += traveled
            tardiness += late
            makespan = max(makespan, end)
        return self.objective.score(distance, makespan, tardiness)
