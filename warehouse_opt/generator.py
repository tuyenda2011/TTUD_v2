"""Seeded synthetic single-block warehouses; no external datasets are claimed."""
from dataclasses import replace
import random

from .models import Edge, InputError, Instance, Node, Operations, Order, Product
from .evaluator import Evaluator


MAP_SCENARIOS = {
    "single_block": {
        "name": "Kho Tiêu chuẩn (Single-Block)",
        "description": "5 dãy × 6 hàng (30 SKU), 2 lối ngang đầu/cuối",
        "aisles": 5, "rows": 6, "cross_aisles": 0, "pickers": 3,
        "n": 10, "capacity": 20., "tightness": .15, "demand_pattern": "uniform"
    },
    "double_block": {
        "name": "Kho 2 Khối có Lối Đi Giữa (Double-Block)",
        "description": "6 dãy × 8 hàng (48 SKU), 1 lối đi ngang ở giữa kho (2 blocks)",
        "aisles": 6, "rows": 8, "cross_aisles": 1, "pickers": 3,
        "n": 30, "capacity": 25., "tightness": .18, "demand_pattern": "uniform"
    },
    "mega_hub": {
        "name": "Đại Kho Vận 3 Khối (Mega Hub)",
        "description": "10 dãy × 16 hàng (160 SKU), 2 lối đi cắt ngang giữa (3 blocks)",
        "aisles": 10, "rows": 16, "cross_aisles": 2, "pickers": 5,
        "n": 40, "capacity": 30., "tightness": .20, "demand_pattern": "uniform"
    },
    "rush_hour": {
        "name": "Giờ Cao Điểm Hạn Gấp (Rush Hour)",
        "description": "6 dãy × 8 hàng (48 SKU), hạn giao cực gấp (tightness=0.06)",
        "aisles": 6, "rows": 8, "cross_aisles": 1, "pickers": 4,
        "n": 25, "capacity": 20., "tightness": .06, "demand_pattern": "uniform"
    },
    "abc_zonal": {
        "name": "Phân Khu Tần Suất (ABC Zonal Layout)",
        "description": "6 dãy × 10 hàng (60 SKU), 1 lối giữa, 20% SKU gần depot chiếm 70% lượt lấy",
        "aisles": 6, "rows": 10, "cross_aisles": 1, "pickers": 4,
        "n": 35, "capacity": 25., "tightness": .18, "demand_pattern": "abc_zonal"
    }
}


def generate(n=30, seed=42, pickers=3, capacity=30., aisles=5, rows=6, tightness=.25, spread=.5,
             cross_aisles=0, demand_pattern="uniform"):
    if any(type(x) is not int or x < 1 for x in (n, pickers, aisles, rows)):
        raise InputError("n, pickers, aisles and rows must be positive integers")
    if type(cross_aisles) is not int or cross_aisles < 0:
        raise InputError("cross_aisles must be a non-negative integer")
    from .models import number
    number(capacity, "capacity", strict=True)
    number(tightness, "tightness", strict=True)
    number(spread, "spread")
    if capacity < 1:
        raise InputError("Synthetic unit-sized products require capacity >= 1")
    rng = random.Random(seed)

    cross_rows = []
    if cross_aisles > 0:
        step = (rows + 1) / (cross_aisles + 1)
        cross_rows = sorted({max(1, min(rows, round(step * (i + 1)))) for i in range(cross_aisles)})

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
            for cr in cross_rows:
                edges.append(Edge(aisle_ids[a - 1][cr], ids[cr], 8.))

    if demand_pattern == "abc_zonal" and products:
        # 20% SKU closest to depot get 70% weight, next 30% get 20%, remaining 50% get 10%
        # Distance from depot at (0, 0)
        sorted_prods = sorted(products, key=lambda p: int(p.location.split("-")[0][1:]) + int(p.location.split("-")[1][1:]))
        n_p = len(sorted_prods)
        idx_a = max(1, int(n_p * 0.2))
        idx_b = max(idx_a + 1, int(n_p * 0.5))
        weights = []
        for i, p in enumerate(sorted_prods):
            if i < idx_a:
                weights.append(0.70 / idx_a)
            elif i < idx_b:
                weights.append(0.20 / (idx_b - idx_a))
            else:
                weights.append(0.10 / max(1, n_p - idx_b))
        prod_weight_map = {p.id: w for p, w in zip(sorted_prods, weights)}
        sample_weights = [prod_weight_map[p.id] for p in products]
    else:
        sample_weights = None

    orders = []
    for i in range(n):
        quantity = rng.randint(1, min(int(capacity), 10))
        k = min(quantity, rng.randint(1, 4), len(products))
        if sample_weights:
            # Weighted sampling without replacement
            chosen_indices = []
            pool = list(range(len(products)))
            p_weights = list(sample_weights)
            for _ in range(k):
                total_w = sum(p_weights)
                if total_w <= 0:
                    break
                r_val = rng.uniform(0, total_w)
                cum = 0.0
                for idx_in_pool, (item_idx, w) in enumerate(zip(pool, p_weights)):
                    cum += w
                    if cum >= r_val:
                        chosen_indices.append(item_idx)
                        pool.pop(idx_in_pool)
                        p_weights.pop(idx_in_pool)
                        break
            choices = [products[idx] for idx in chosen_indices] or rng.sample(products, k)
        else:
            choices = rng.sample(products, k)
        items = {p.id: 1 for p in choices}
        for _ in range(quantity - len(choices)):
            items[rng.choice(choices).id] += 1
        orders.append(Order(f"O{i + 1:04d}", items, 0., i))

    layout_info = {"type": "multi_block" if cross_aisles > 0 else "single_block", "aisles": aisle_ids}
    if cross_aisles > 0:
        layout_info["cross_aisles"] = cross_rows

    instance = Instance(f"synthetic-n{n}-seed{seed}", aisle_ids[0][0], nodes, edges, products, orders,
        Operations(pickers=pickers, capacity=capacity),
        {"source": "synthetic/internal-v1", "seed": seed, "units": {"distance": "metre", "time": "minute", "capacity": "item"},
         "layout": layout_info,
         "due_dates": {"synthetic": True, "rule": "p_i + tau * H * (1 + spread * U_i)", "tightness": tightness, "spread": spread, "reference_pickers": pickers}})
    ctx = Evaluator(instance)
    individual = [ctx.batch_info((o.id,), "nn")[2] for o in orders]
    horizon = max(max(individual), sum(individual) / pickers)
    instance.orders = [replace(o, due=p + tightness * horizon * (1 + spread * rng.random())) for o, p in zip(orders, individual)]
    instance.metadata["due_dates"]["horizon"] = horizon
    return instance.validate()


def generate_scenario(scenario_key="single_block", seed=42, **overrides):
    config = dict(MAP_SCENARIOS.get(scenario_key, MAP_SCENARIOS["single_block"]))
    config.pop("name", None)
    config.pop("description", None)
    config.update(overrides)
    config["seed"] = seed
    return generate(**config)

