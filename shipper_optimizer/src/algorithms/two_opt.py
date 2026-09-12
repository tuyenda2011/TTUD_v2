"""
Algorithm 3b: 2-Opt Local Search Improvement for TSP and VRP routes.
Iteratively removes edge crossings to achieve local optimality.
"""

from __future__ import annotations
import time
from typing import List, Tuple
import numpy as np

from src.models.location import Location
from src.models.route import Route, VRPSolution


class TwoOpt:
    """
    2-Opt local search optimizer for route improvement.
    """
    def __init__(self, distance_matrix: np.ndarray):
        self.dist = distance_matrix
        self.n = len(distance_matrix)

    def route_distance(self, route_nodes: List[int]) -> float:
        """Calculate total distance of node sequence."""
        return sum(self.dist[route_nodes[i], route_nodes[i + 1]] for i in range(len(route_nodes) - 1))

    def improve_single_route(
        self,
        route_nodes: List[int],
        max_iterations: int = 1000,
        tolerance: float = 1e-6
    ) -> Tuple[List[int], float, int]:
        """
        Apply 2-opt to a single route where start and end nodes are fixed (typically depot).
        
        Args:
            route_nodes: List of node indices [0, c1, c2, ..., ck, 0]
            max_iterations: Max number of improvement cycles
            tolerance: Minimum improvement threshold
            
        Returns:
            (optimized_route, new_distance, iterations_count)
        """
        # If route has 3 or fewer nodes (e.g. [0, c1, 0]), 2-opt cannot change it
        if len(route_nodes) <= 3:
            return list(route_nodes), self.route_distance(route_nodes), 0

        best_route = list(route_nodes)
        best_dist = self.route_distance(best_route)
        improved = True
        iterations = 0
        m = len(best_route)

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            # Try reversing sub-segment between index i and index j (1 <= i < j <= m - 2)
            # Keeping index 0 (depot) and index m-1 (depot) fixed
            for i in range(1, m - 2):
                for j in range(i + 1, m - 1):
                    u = best_route[i - 1]
                    v = best_route[i]
                    x = best_route[j]
                    y = best_route[j + 1]

                    # Delta calculation: new edges (u -> x) + (v -> y) vs old edges (u -> v) + (x -> y)
                    old_edges = self.dist[u, v] + self.dist[x, y]
                    new_edges = self.dist[u, x] + self.dist[v, y]
                    delta = new_edges - old_edges

                    if delta < -tolerance:
                        # Perform 2-opt swap: reverse segment from i to j
                        best_route[i : j + 1] = reversed(best_route[i : j + 1])
                        best_dist += delta
                        improved = True
                        break  # First improvement strategy for speed
                if improved:
                    break

        return best_route, best_dist, iterations

    def optimize_solution(
        self,
        solution: VRPSolution,
        locations: List[Location],
        name_suffix: str = " + 2-Opt"
    ) -> VRPSolution:
        """
        Optimize each route in a VRPSolution with 2-Opt.
        
        Returns:
            New optimized VRPSolution.
        """
        start_time = time.perf_counter()
        optimized_routes: List[Route] = []
        total_dist = 0.0
        total_demand = 0.0
        total_deliveries = 0

        for r in solution.routes:
            opt_nodes, opt_dist, _ = self.improve_single_route(r.node_indices)
            
            new_r = Route(
                vehicle_id=r.vehicle_id,
                node_indices=opt_nodes,
                node_ids=[locations[k].id for k in opt_nodes],
                node_names=[locations[k].name for k in opt_nodes],
                total_distance_km=opt_dist,
                total_demand_kg=r.total_demand_kg,
                num_deliveries=r.num_deliveries
            )
            new_r.compute_summary()
            optimized_routes.append(new_r)
            
            total_dist += opt_dist
            total_demand += r.total_demand_kg
            total_deliveries += r.num_deliveries

        elapsed = solution.execution_time_sec + (time.perf_counter() - start_time)

        new_sol = VRPSolution(
            algorithm_name=f"{solution.algorithm_name}{name_suffix}",
            routes=optimized_routes,
            total_distance_km=total_dist,
            total_demand_kg=total_demand,
            total_deliveries=total_deliveries,
            num_vehicles=len(optimized_routes),
            vehicle_capacity_kg=solution.vehicle_capacity_kg,
            execution_time_sec=elapsed,
            is_feasible=True
        )

        return new_sol
