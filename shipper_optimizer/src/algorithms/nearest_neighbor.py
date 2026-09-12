"""
Algorithm 2: Nearest Neighbor Heuristic for Traveling Salesperson Problem (TSP).
Greedy construction algorithm with O(n^2) time complexity.
"""

from __future__ import annotations
import time
from typing import List, Tuple, Optional
import numpy as np

from src.models.location import Location
from src.models.route import Route, VRPSolution


class NearestNeighbor:
    """
    Greedy Nearest Neighbor heuristic for single-vehicle TSP tour construction.
    """
    def __init__(
        self,
        locations: List[Location],
        distance_matrix: np.ndarray,
        demands: Optional[List[float]] = None,
        depot_idx: int = 0
    ):
        self.locations = locations
        self.dist = distance_matrix
        self.n = len(locations)
        self.depot_idx = depot_idx
        self.demands = demands if demands is not None else [loc.demand_kg for loc in locations]

    def solve(self) -> VRPSolution:
        """
        Build TSP tour starting from depot, greedily visiting the closest unvisited node.
        
        Returns:
            VRPSolution object with complete route metrics.
        """
        start_time = time.perf_counter()
        
        unvisited = set(range(self.n))
        route_nodes = [self.depot_idx]
        current = self.depot_idx
        unvisited.remove(current)

        while unvisited:
            # Find closest unvisited node
            nearest = min(unvisited, key=lambda v: self.dist[current, v])
            route_nodes.append(nearest)
            unvisited.remove(nearest)
            current = nearest

        # Return to depot
        route_nodes.append(self.depot_idx)

        elapsed = time.perf_counter() - start_time

        # Calculate distance and demand
        total_dist = 0.0
        for i in range(len(route_nodes) - 1):
            u, v = route_nodes[i], route_nodes[i + 1]
            total_dist += self.dist[u, v]

        total_demand = sum(self.demands[i] for i in route_nodes[:-1])
        num_deliveries = len(route_nodes) - 2

        route_obj = Route(
            vehicle_id=1,
            node_indices=route_nodes,
            node_ids=[self.locations[idx].id for idx in route_nodes],
            node_names=[self.locations[idx].name for idx in route_nodes],
            total_distance_km=total_dist,
            total_demand_kg=total_demand,
            num_deliveries=num_deliveries
        )
        route_obj.compute_summary()

        solution = VRPSolution(
            algorithm_name="Nearest Neighbor (TSP)",
            routes=[route_obj],
            total_distance_km=total_dist,
            total_demand_kg=total_demand,
            total_deliveries=num_deliveries,
            num_vehicles=1,
            vehicle_capacity_kg=max(500.0, total_demand),
            execution_time_sec=elapsed,
            is_feasible=True
        )

        return solution

    def evaluate_tour_distance(self, tour: List[int]) -> float:
        """Calculate total tour length given node sequence."""
        return sum(self.dist[tour[i], tour[i+1]] for i in range(len(tour) - 1))
