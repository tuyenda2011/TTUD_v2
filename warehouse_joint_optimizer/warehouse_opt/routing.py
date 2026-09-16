from dataclasses import dataclass
from itertools import permutations

from .models import InputError


@dataclass(frozen=True)
class Route:
    stops: tuple[str, ...]
    walk: tuple[str, ...]
    distance: float


class Router:
    def __init__(self, instance, graph):
        self.instance, self.graph = instance, graph
        self.cache = {}

    def length(self, stops):
        return sum(self.graph.distance(a, b) for a, b in zip(stops, stops[1:]))

    def route(self, locations, mode="2opt"):
        locations = frozenset(locations)
        key = (tuple(sorted(locations)), mode)
        if key in self.cache:
            return self.cache[key]
        depot = self.instance.depot
        remaining = set(locations) - {depot}
        if mode == "s_shape":
            result = self.s_shape(remaining)
        else:
            stops = [depot]
            while remaining:
                nxt = min(remaining, key=lambda n: (self.graph.distance(stops[-1], n), n))
                stops.append(nxt)
                remaining.remove(nxt)
            stops.append(depot)
            if mode == "2opt":
                improved = True
                while improved:
                    improved = False
                    for i in range(1, len(stops) - 2):
                        for j in range(i + 1, len(stops) - 1):
                            a, b, c, d = stops[i - 1], stops[i], stops[j], stops[j + 1]
                            delta = self.graph.distance(a, c) + self.graph.distance(b, d) - self.graph.distance(a, b) - self.graph.distance(c, d)
                            if delta < -1e-9:
                                stops[i:j + 1] = reversed(stops[i:j + 1])
                                improved = True
                                break
                        if improved:
                            break
            elif mode == "exact":
                if len(stops) - 2 > 8:
                    raise InputError("Exact routing limited to 8 distinct non-depot pick locations")
                candidates = ([depot, *seq, depot] for seq in permutations(sorted(set(locations) - {depot})))
                stops = min(candidates, key=lambda seq: (self.length(seq), seq))
            elif mode != "nn":
                raise InputError(f"Unknown routing mode: {mode}")
            walk = self.graph.expand(stops)
            result = Route(tuple(stops), walk, self.graph.walk_distance(walk))
        self.cache[key] = result
        return result

    def s_shape(self, required):
        """Single-block, two-cross-aisle policy; odd final aisle is a return visit."""
        layout = self.instance.metadata.get("layout", {})
        if layout.get("type") != "single_block":
            raise InputError("S-Shape requires a verified single_block layout")
        aisles = layout.get("aisles", [])
        depot = self.instance.depot
        listed = [n for aisle in aisles for n in aisle]
        if not aisles or any(len(a) < 2 for a in aisles) or len(listed) != len(set(listed)):
            raise InputError("Invalid aisle definitions")
        if set(listed) != set(self.graph.nodes) or depot != aisles[0][0]:
            raise InputError("S-Shape requires complete aisle metadata and depot at first aisle front")
        expected = {frozenset((a, b)) for aisle in aisles for a, b in zip(aisle, aisle[1:])}
        expected |= {frozenset((a[end], b[end])) for a, b in zip(aisles, aisles[1:]) for end in (0, -1)}
        actual = {frozenset((a, b)) for a in self.graph.adj for b in self.graph.adj[a]}
        if actual != expected:
            raise InputError("S-Shape graph does not match the single-block topology")
        active = [a for a in aisles if required.intersection(a)]
        walk, service = [depot], [depot]
        for idx, aisle in enumerate(active):
            ordered = aisle if idx % 2 == 0 else list(reversed(aisle))
            entry = ordered[0]
            walk.extend(self.graph.path(walk[-1], entry)[1:])
            visit = [n for n in ordered if n in required]
            service.extend(visit)
            if idx == len(active) - 1 and len(active) % 2 == 1:
                furthest = max(ordered.index(n) for n in visit)
                segment = ordered[:furthest + 1]
                walk.extend(segment[1:])
                walk.extend(list(reversed(segment))[1:])
            else:
                walk.extend(ordered[1:])
        walk.extend(self.graph.path(walk[-1], depot)[1:])
        service.append(depot)
        return Route(tuple(service), tuple(walk), self.graph.walk_distance(walk))
