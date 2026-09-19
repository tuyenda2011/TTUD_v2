"""Validated input schema. Units: metres, minutes, cart-capacity units."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import math


class InputError(ValueError):
    pass


def number(value, label, minimum=0, strict=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label}: expected a finite number")
    if not math.isfinite(value) or value < minimum or (strict and value == minimum):
        raise InputError(f"{label}: expected {'>' if strict else '>='} {minimum}")
    return value


@dataclass(frozen=True)
class Node:
    id: str
    x: float
    y: float


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    distance: float


@dataclass(frozen=True)
class Product:
    id: str
    location: str
    size: float = 1.0
    pick_minutes: float = 0.08


@dataclass(frozen=True)
class Order:
    id: str
    items: dict[str, int]
    due: float
    rank: int


@dataclass(frozen=True)
class Operations:
    pickers: int = 3
    capacity: float = 30.0
    speed: float = 60.0
    location_minutes: float = 0.1
    batch_minutes: float = 0.5


@dataclass
class Instance:
    name: str
    depot: str
    nodes: list[Node]
    edges: list[Edge]
    products: list[Product]
    orders: list[Order]
    operations: Operations = field(default_factory=Operations)
    metadata: dict = field(default_factory=dict)
    directed: bool = False
    schema_version: int = 1

    def validate(self):
        if self.schema_version != 1 or type(self.schema_version) is not int:
            raise InputError("Unsupported schema_version (expected 1)")
        if self.directed is not False:
            raise InputError("Only undirected warehouse graphs are supported")
        if not isinstance(self.name, str) or not self.name:
            raise InputError("Instance name must be a nonempty string")
        if not isinstance(self.metadata, dict):
            raise InputError("metadata must be an object")
        for field in ("units", "layout"):
            if field in self.metadata and not isinstance(self.metadata[field], dict):
                raise InputError(f"metadata.{field} must be an object")
        for field, value in self.metadata.get("units", {}).items():
            if not isinstance(value, str) or not value.strip():
                raise InputError(f"metadata.units.{field} must be a nonempty unit label")
        for label, rows in [("node", self.nodes), ("product", self.products), ("order", self.orders)]:
            ids = [row.id for row in rows]
            if not ids or any(not isinstance(i, str) or not i for i in ids):
                raise InputError(f"{label} IDs must be nonempty strings; dataset cannot be empty")
            if len(set(ids)) != len(ids):
                raise InputError(f"Duplicate {label} ID")
        node_ids = {node.id for node in self.nodes}
        layout = self.metadata.get("layout", {})
        if layout.get("type") == "single_block":
            aisles = layout.get("aisles")
            if not isinstance(aisles, list) or not aisles or any(
                not isinstance(aisle, list) or len(aisle) < 2
                or any(not isinstance(node, str) or node not in node_ids for node in aisle)
                for aisle in aisles
            ):
                raise InputError("metadata.layout.aisles must list aisles with at least two existing node IDs")
        if self.depot not in node_ids:
            raise InputError("Depot not found in graph")
        for node in self.nodes:
            for label, value in [("x", node.x), ("y", node.y)]:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise InputError(f"Node {node.id}: invalid {label}")
        adjacency = {key: set() for key in node_ids}
        seen_edges = set()
        for edge in self.edges:
            if edge.source not in node_ids or edge.target not in node_ids or edge.source == edge.target:
                raise InputError("Edge endpoint missing or self-loop supplied")
            number(edge.distance, "edge distance")
            key = frozenset((edge.source, edge.target))
            if key in seen_edges:
                raise InputError("Duplicate undirected edge")
            seen_edges.add(key)
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)
        reached, stack = {self.depot}, [self.depot]
        while stack:
            for neighbor in adjacency[stack.pop()]:
                if neighbor not in reached:
                    reached.add(neighbor)
                    stack.append(neighbor)
        if reached != node_ids:
            raise InputError("Warehouse graph is disconnected")
        op = self.operations
        if type(op.pickers) is not int or op.pickers < 1:
            raise InputError("pickers must be a positive integer")
        for label in ("capacity", "speed"):
            number(getattr(op, label), label, strict=True)
        for label in ("location_minutes", "batch_minutes"):
            number(getattr(op, label), label)
        products = {p.id: p for p in self.products}
        for product in self.products:
            if product.location not in node_ids:
                raise InputError(f"Product {product.id}: unknown location")
            number(product.size, "product size", strict=True)
            number(product.pick_minutes, "pick_minutes")
        for order in self.orders:
            number(order.due, f"Order {order.id}: due date")
            if type(order.rank) is not int or order.rank < 0:
                raise InputError(f"Order {order.id}: invalid FCFS rank")
            if not isinstance(order.items, dict) or not order.items:
                raise InputError(f"Order {order.id}: empty items")
            for sku, qty in order.items.items():
                if sku not in products or type(qty) is not int or qty <= 0:
                    raise InputError(f"Order {order.id}: unknown SKU or non-positive integer quantity")
            load = sum(products[sku].size * qty for sku, qty in order.items.items())
            if not math.isfinite(load) or load > op.capacity + 1e-9:
                raise InputError(f"Order {order.id}: load {load:g} exceeds capacity {op.capacity:g}; orders cannot be split")
        return self

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        try:
            unknown = set(data) - set(cls.__dataclass_fields__)
            if unknown:
                raise InputError(f"Unknown instance fields: {sorted(unknown)}")
            instance = cls(**{**data,
                "nodes": [Node(**row) for row in data["nodes"]],
                "edges": [Edge(**row) for row in data["edges"]],
                "products": [Product(**row) for row in data["products"]],
                "orders": [Order(**row) for row in data["orders"]],
                "operations": Operations(**data["operations"])})
            return instance.validate()
        except (KeyError, TypeError, AttributeError) as exc:
            raise InputError(f"Invalid instance schema: {exc}") from exc


def read_instance(path):
    return Instance.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
