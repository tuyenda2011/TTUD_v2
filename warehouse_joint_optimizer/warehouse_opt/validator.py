"""Independent audit of exported routes/timing, without the routing/evaluator caches."""
from collections import Counter
import math


def validate_solution(instance, result):
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    def same(actual, expected, label):
        check(isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-7, abs_tol=1e-7), f"Mismatch: {label}")

    try:
        instance.validate()
        check(type(result["schema_version"]) is int and result["schema_version"] == 1, "Unsupported solution schema_version")
        check(result["instance"] == instance.name, "Wrong instance name")
        products = {p.id: p for p in instance.products}
        orders = {o.id: o for o in instance.orders}
        adjacency = {(e.source, e.target): e.distance for e in instance.edges}
        adjacency.update({(e.target, e.source): e.distance for e in instance.edges})
        op = instance.operations
        ends = [0.] * op.pickers
        sequences = [[] for _ in ends]
        seen, batch_ids, order_records = [], [], {}
        distance_total, tardiness_total, late = 0., 0., 0
        for batch in result["batches"]:
            ids = batch["orders"]
            check(bool(ids), "Empty batch")
            batch_ids.append(batch["id"])
            picker = batch["picker"] - 1
            check(type(batch["picker"]) is int and 0 <= picker < op.pickers, "Invalid picker")
            if not 0 <= picker < op.pickers:
                continue
            check(batch["position"] == len(sequences[picker]), "Nonsequential batch position")
            sequences[picker].append(ids)
            needed = {products[sku].location for oid in ids for sku in orders[oid].items}
            stops, walk = batch["stops"], batch["walk"]
            check(stops[0] == stops[-1] == instance.depot, "Service route depot mismatch")
            check(walk[0] == walk[-1] == instance.depot, "Physical route depot mismatch")
            check(Counter(stops[1:-1]) == Counter(needed - {instance.depot}), "Required service locations mismatch")
            check(needed <= set(walk), "Physical walk misses a pick location")
            # Service order must appear along the physical walk; repeated depot-only stops are allowed.
            cursor = 0
            for stop in stops:
                while cursor < len(walk) and walk[cursor] != stop:
                    cursor += 1
                check(cursor < len(walk), "Service order does not follow physical walk")
            walked = sum(adjacency[(u, v)] for u, v in zip(walk, walk[1:]))
            load = sum(products[sku].size * qty for oid in ids for sku, qty in orders[oid].items.items())
            handling = sum(products[sku].pick_minutes * qty for oid in ids for sku, qty in orders[oid].items.items())
            duration = op.batch_minutes + walked / op.speed + op.location_minutes * len(needed) + handling
            check(load <= op.capacity + 1e-9, "Overloaded batch")
            same(batch["load"], load, "load")
            same(batch["distance"], walked, "distance")
            same(batch["duration"], duration, "duration")
            same(batch["start"], ends[picker], "start/nonoverlap")
            completion = ends[picker] + duration
            same(batch["end"], completion, "completion")
            ends[picker] = completion
            distance_total += walked
            losses = 0.
            for oid in ids:
                seen.append(oid)
                loss = max(0., completion - orders[oid].due)
                losses += loss
                late += int(loss > 1e-9)
                order_records[oid] = (batch["id"], picker + 1, completion, loss)
            same(batch["tardiness"], losses, "batch tardiness")
            tardiness_total += losses
        check(Counter(seen) == Counter(orders.keys()), "Missing/duplicate/unknown orders")
        check(len(set(batch_ids)) == len(batch_ids), "Duplicate batch IDs")
        check(result["plan"] == sequences, "Plan and exported batches disagree")
        check(Counter(r["id"] for r in result["orders"]) == Counter(orders.keys()), "Order record coverage mismatch")
        for row in result["orders"]:
            bid, picker, completion, loss = order_records[row["id"]]
            check(row["batch"] == bid and row["picker"] == picker, "Order assignment mismatch")
            same(row["due"], orders[row["id"]].due, "due")
            same(row["completion"], completion, "order completion")
            same(row["tardiness"], loss, "order tardiness")
        expected = {"distance": distance_total, "makespan": max(ends), "tardiness": tardiness_total, "late_orders": late, "batches": len(batch_ids), "used_pickers": sum(bool(s) for s in sequences), "on_time_rate": 1 - late / len(orders)}
        for key, value in expected.items():
            same(result["metrics"][key], value, key)
        check(len(result["picker_ends"]) == op.pickers, "Picker end count mismatch")
        for actual, expected_end in zip(result["picker_ends"], ends):
            same(actual, expected_end, "picker end")
        objective = result["objective_config"]
        if objective is not None:
            refs = [objective[k] for k in ("distance_ref", "completion_ref", "tardiness_ref")]
            weights = objective["weights"]
            check(len(weights) == 3 and all(math.isfinite(w) and w > 0 for w in weights) and math.isclose(sum(weights), 1), "Invalid objective weights")
            check(all(math.isfinite(r) and r > 0 for r in refs), "Invalid objective references")
            value = sum(w * v / ref for w, v, ref in zip(weights, (distance_total, max(ends), tardiness_total), refs))
            same(result["metrics"]["objective"], value, "objective")
        else:
            check("objective" not in result["metrics"], "Objective metric lacks configuration")
    except (KeyError, TypeError, IndexError, ValueError, ZeroDivisionError) as exc:
        errors.append(f"Malformed solution or invalid route: {exc}")
    return errors
