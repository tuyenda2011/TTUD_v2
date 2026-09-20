from .evaluator import Plan


def freeze(plan) -> Plan:
    return tuple(tuple(tuple(sorted(batch)) for batch in sequence) for sequence in plan)


def mutable(plan):
    return [[list(batch) for batch in sequence] for sequence in plan]


def fcfs(ctx):
    batches, current, load = [], [], 0.
    for order in sorted(ctx.orders.values(), key=lambda o: (o.rank, o.id)):
        if current and load + ctx.loads[order.id] > ctx.instance.operations.capacity + 1e-9:
            batches.append(tuple(current))
            current, load = [], 0.
        current.append(order.id)
        load += ctx.loads[order.id]
    if current:
        batches.append(tuple(current))
    return batches


def greedy(ctx):
    remaining, batches = set(ctx.orders), []
    while remaining:
        seed = min(remaining, key=lambda oid: (ctx.orders[oid].due, oid))
        batch, load = [seed], ctx.loads[seed]
        remaining.remove(seed)
        while True:
            feasible = [oid for oid in sorted(remaining) if load + ctx.loads[oid] <= ctx.instance.operations.capacity + 1e-9]
            if not feasible:
                break
            distance = ctx.batch_info(batch, "nn")[1].distance
            chosen = min(feasible, key=lambda oid: (ctx.batch_info([*batch, oid], "nn")[1].distance - distance, ctx.orders[oid].due, oid))
            batch.append(chosen)
            load += ctx.loads[chosen]
            remaining.remove(chosen)
        batches.append(tuple(batch))
    return batches


def list_schedule(ctx, batches, mode):
    plan = [[] for _ in range(ctx.instance.operations.pickers)]
    available = [0.] * len(plan)
    for index, batch in sorted(enumerate(batches), key=lambda row: (min(ctx.orders[o].due for o in row[1]), row[0])):
        picker = min(range(len(plan)), key=lambda p: (available[p], p))
        plan[picker].append(batch)
        available[picker] += ctx.batch_info(batch, mode)[2]
    return freeze(plan)
