"""Seeded synthetic single-block warehouses; no external datasets are claimed."""
from dataclasses import replace
import random

from .models import Edge, InputError, Instance, Node, Operations, Order, Product
from .evaluator import Evaluator


def generate(n=30, seed=42, pickers=3, capacity=30., aisles=5, rows=6, tightness=.25, spread=.5):
    if any(type(x) is not int or x < 1 for x in (n, pickers, aisles, rows)):
        raise InputError("n, pickers, aisles and rows must be positive integers")
    from .models import number
    number(capacity, "capacity", strict=True)
    number(tightness, "tightness", strict=True)
    number(spread, "spread")
    if capacity < 1:
        raise InputError("Synthetic unit-sized products require capacity >= 1")
    rng = random.Random(seed)
    nodes, edges, aisle_ids, products = [], [], [], []
    for a in range(aisles):
        ids = [f"A{a:02d}-R{r:02d}" for r in range(rows + 2)]
        aisle_ids.append(ids)
        for r, node_id in enumerate(ids):
            nodes.append(Node(node_id, a * 8., r * 4.))
            if r:
                edges.append(Edge(ids[r - 1], node_id, 4.))
            if 0 < r < rows + 1:
                products.append(Product(f"SKU-{a:02d}-{r:02d}", node_id))
        if a:
            for end in (0, -1):
                edges.append(Edge(aisle_ids[a - 1][end], ids[end], 8.))
    orders = []
    for i in range(n):
        quantity = rng.randint(1, min(int(capacity), 10))
        choices = rng.sample(products, min(quantity, rng.randint(1, 4), len(products)))
        items = {p.id: 1 for p in choices}
        for _ in range(quantity - len(choices)):
            items[rng.choice(choices).id] += 1
        orders.append(Order(f"O{i + 1:04d}", items, 0., i))
    instance = Instance(f"synthetic-n{n}-seed{seed}", aisle_ids[0][0], nodes, edges, products, orders,
        Operations(pickers=pickers, capacity=capacity),
        {"source": "synthetic/internal-v1", "seed": seed, "units": {"distance": "metre", "time": "minute", "capacity": "item"}, "layout": {"type": "single_block", "aisles": aisle_ids}, "due_dates": {"synthetic": True, "rule": "p_i + tau * H * (1 + spread * U_i)", "tightness": tightness, "spread": spread, "reference_pickers": pickers}})
    ctx = Evaluator(instance)
    individual = [ctx.batch_info((o.id,), "nn")[2] for o in orders]
    horizon = max(max(individual), sum(individual) / pickers)
    instance.orders = [replace(o, due=p + tightness * horizon * (1 + spread * rng.random())) for o, p in zip(orders, individual)]
    instance.metadata["due_dates"]["horizon"] = horizon
    return instance.validate()
