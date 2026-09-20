"""Dijkstra metric closure over actual warehouse aisles."""
import heapq


class WarehouseGraph:
    def __init__(self, instance):
        self.nodes = {n.id: n for n in instance.nodes}
        self.adj = {n.id: {} for n in instance.nodes}
        for edge in instance.edges:
            self.adj[edge.source][edge.target] = edge.distance
            self.adj[edge.target][edge.source] = edge.distance
        self.distances, self.parents = {}, {}
        for source in sorted({instance.depot} | {p.location for p in instance.products}):
            self._dijkstra(source)

    def _dijkstra(self, source):
        distances, parents = {source: 0.0}, {source: None}
        queue = [(0.0, source)]
        while queue:
            distance, current = heapq.heappop(queue)
            if distance != distances[current]:
                continue
            for neighbor, weight in sorted(self.adj[current].items()):
                candidate = distance + weight
                if candidate < distances.get(neighbor, float("inf")):
                    distances[neighbor] = candidate
                    parents[neighbor] = current
                    heapq.heappush(queue, (candidate, neighbor))
        self.distances[source], self.parents[source] = distances, parents

    def distance(self, source, target):
        if source not in self.distances:
            self._dijkstra(source)
        return self.distances[source][target]

    def path(self, source, target):
        self.distance(source, target)
        path = [target]
        while path[-1] != source:
            path.append(self.parents[source][path[-1]])
        return tuple(reversed(path))

    def expand(self, stops):
        walk = [stops[0]]
        for u, v in zip(stops, stops[1:]):
            walk.extend(self.path(u, v)[1:])
        return tuple(walk)

    def walk_distance(self, walk):
        return sum(self.adj[u][v] for u, v in zip(walk, walk[1:]))
