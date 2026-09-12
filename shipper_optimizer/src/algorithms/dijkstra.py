"""
Algorithm 1: Dijkstra Shortest Path and All-Pairs Distance Matrix Construction.
Uses Min-Heap Priority Queue (heapq) with O((V + E) log V) complexity.
"""

from __future__ import annotations
import heapq
import time
from typing import List, Dict, Tuple, Optional
import numpy as np

from src.models.location import Location


class Dijkstra:
    """
    Dijkstra's Single-Source and All-Pairs Shortest Path solver.
    """
    def __init__(self, locations: List[Location], distance_matrix: Optional[np.ndarray] = None):
        self.locations = locations
        self.n = len(locations)
        self.loc_ids = [loc.id for loc in locations]
        self.loc_names = [loc.name for loc in locations]
        
        if distance_matrix is not None:
            self.dist_matrix = distance_matrix
        else:
            self.dist_matrix = self._compute_direct_matrix()

    def _compute_direct_matrix(self) -> np.ndarray:
        """Compute direct pairwise distances using Haversine."""
        matrix = np.zeros((self.n, self.n), dtype=float)
        for i in range(self.n):
            for j in range(i + 1, self.n):
                d = self.locations[i].distance_to(self.locations[j])
                matrix[i, j] = d
                matrix[j, i] = d
        return matrix

    def shortest_path(self, source_idx: int, target_idx: int) -> Tuple[float, List[int]]:
        """
        Find shortest path from source to target using Min-Heap priority queue.
        
        Returns:
            (shortest_distance_km, path_indices)
        """
        if source_idx < 0 or source_idx >= self.n or target_idx < 0 or target_idx >= self.n:
            raise ValueError("Source or Target index out of bounds.")

        dist = [float('inf')] * self.n
        prev = [None] * self.n
        dist[source_idx] = 0.0

        # Min-Heap tuple: (distance, u)
        pq = [(0.0, source_idx)]
        visited = [False] * self.n

        while pq:
            d_u, u = heapq.heappop(pq)

            if visited[u]:
                continue
            visited[u] = True

            if u == target_idx:
                break

            # Relaxation of all neighboring edges
            for v in range(self.n):
                if v != u and not visited[v]:
                    weight = self.dist_matrix[u, v]
                    if dist[u] + weight < dist[v]:
                        dist[v] = dist[u] + weight
                        prev[v] = u
                        heapq.heappush(pq, (dist[v], v))

        # Reconstruct path from target to source
        path: List[int] = []
        curr = target_idx
        while curr is not None:
            path.append(curr)
            curr = prev[curr]
        path.reverse()

        return dist[target_idx], path

    def compute_all_pairs_matrix(self) -> Tuple[np.ndarray, float]:
        """
        Compute full n x n shortest path matrix.
        
        Returns:
            (matrix, execution_time_sec)
        """
        start_time = time.perf_counter()
        matrix = np.zeros((self.n, self.n), dtype=float)
        
        for i in range(self.n):
            # Run Dijkstra from source i
            dist = [float('inf')] * self.n
            dist[i] = 0.0
            pq = [(0.0, i)]
            visited = [False] * self.n
            
            while pq:
                d_u, u = heapq.heappop(pq)
                if visited[u]:
                    continue
                visited[u] = True
                
                for v in range(self.n):
                    if v != u and not visited[v]:
                        w = self.dist_matrix[u, v]
                        if dist[u] + w < dist[v]:
                            dist[v] = dist[u] + w
                            heapq.heappush(pq, (dist[v], v))
                            
            matrix[i] = dist

        elapsed = time.perf_counter() - start_time
        return matrix, elapsed

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Compute key network statistics."""
        # Non-diagonal elements
        mask = ~np.eye(self.n, dtype=bool)
        non_diag = self.dist_matrix[mask]
        
        avg_dist = float(np.mean(non_diag))
        min_dist = float(np.min(non_diag))
        max_dist = float(np.max(non_diag))
        
        # Find maximum distance pair
        max_idx = np.unravel_index(np.argmax(self.dist_matrix), self.dist_matrix.shape)
        u_max, v_max = int(max_idx[0]), int(max_idx[1])
        
        # Find depot-to-all statistics (assuming depot is index 0)
        depot_dists = self.dist_matrix[0, 1:]
        avg_depot_dist = float(np.mean(depot_dists))
        
        return {
            "num_nodes": self.n,
            "matrix_shape": f"{self.n}x{self.n}",
            "avg_distance_km": round(avg_dist, 2),
            "min_distance_km": round(min_dist, 2),
            "max_distance_km": round(max_dist, 2),
            "max_pair": (self.loc_ids[u_max], self.loc_ids[v_max]),
            "max_pair_names": (self.loc_names[u_max], self.loc_names[v_max]),
            "avg_distance_from_depot_km": round(avg_depot_dist, 2)
        }
