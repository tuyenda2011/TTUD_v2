"""
Algorithm 3a: Clarke-Wright Savings Algorithm for Capacitated Vehicle Routing Problem (CVRP).
Heuristic merging routes based on maximum distance savings.
"""

from __future__ import annotations
import time
from typing import List, Tuple, Dict, Optional
import numpy as np

from src.models.location import Location
from src.models.route import Route, VRPSolution


class ClarkeWrightSavings:
    """
    Clarke-Wright Savings algorithm for multi-vehicle CVRP.
    """
    def __init__(
        self,
        locations: List[Location],
        distance_matrix: np.ndarray,
        demands: Optional[List[float]] = None,
        vehicle_capacity: float = 200.0,
        depot_idx: int = 0
    ):
        self.locations = locations
        self.dist = distance_matrix
        self.n = len(locations)
        self.depot_idx = depot_idx
        self.demands = demands if demands is not None else [loc.demand_kg for loc in locations]
        self.capacity = vehicle_capacity

    def compute_savings_list(self) -> List[Tuple[float, int, int]]:
        """
        Compute and sort pairwise savings:
        s(i, j) = dist(i, depot) + dist(depot, j) - dist(i, j)
        """
        savings: List[Tuple[float, int, int]] = []
        d0 = self.depot_idx

        for i in range(self.n):
            if i == d0:
                continue
            for j in range(i + 1, self.n):
                if j == d0:
                    continue
                
                # Savings formula
                s = self.dist[i, d0] + self.dist[d0, j] - self.dist[i, j]
                savings.append((s, i, j))

        # Sort in descending order of savings
        savings.sort(key=lambda item: item[0], reverse=True)
        return savings

    def solve(self) -> VRPSolution:
        """
        Solve CVRP using parallel Clarke-Wright savings heuristic.
        
        Returns:
            VRPSolution with multiple optimized vehicle routes.
        """
        start_time = time.perf_counter()
        d0 = self.depot_idx

        # Initial state: Each customer has their own route: [depot, customer, depot]
        # Store customer sequences without depot for cleaner merging
        routes: List[List[int]] = [[i] for i in range(self.n) if i != d0]

        # Mapping: node -> route index in routes list
        def get_route_idx(node: int, current_routes: List[List[int]]) -> Optional[int]:
            for r_idx, r in enumerate(current_routes):
                if node in r:
                    return r_idx
            return None

        savings = self.compute_savings_list()

        for s_val, i, j in savings:
            r1_idx = get_route_idx(i, routes)
            r2_idx = get_route_idx(j, routes)

            # Cannot merge if in the same route
            if r1_idx is None or r2_idx is None or r1_idx == r2_idx:
                continue

            r1 = routes[r1_idx]
            r2 = routes[r2_idx]

            # Check capacity constraint
            demand_r1 = sum(self.demands[k] for k in r1)
            demand_r2 = sum(self.demands[k] for k in r2)
            if demand_r1 + demand_r2 > self.capacity:
                continue

            # Check if i and j are at the exterior of their routes
            merged = False
            new_r: List[int] = []

            # Case 1: i is at the end of r1, j is at the start of r2 -> r1 + r2
            if r1[-1] == i and r2[0] == j:
                new_r = r1 + r2
                merged = True
            # Case 2: j is at the end of r2, i is at the start of r1 -> r2 + r1
            elif r2[-1] == j and r1[0] == i:
                new_r = r2 + r1
                merged = True
            # Case 3: i is at the end of r1, j is at the end of r2 -> r1 + reversed(r2)
            elif r1[-1] == i and r2[-1] == j:
                new_r = r1 + list(reversed(r2))
                merged = True
            # Case 4: i is at the start of r1, j is at the start of r2 -> reversed(r1) + r2
            elif r1[0] == i and r2[0] == j:
                new_r = list(reversed(r1)) + r2
                merged = True

            if merged:
                # Remove old routes and append merged route
                if r1_idx > r2_idx:
                    routes.pop(r1_idx)
                    routes.pop(r2_idx)
                else:
                    routes.pop(r2_idx)
                    routes.pop(r1_idx)
                routes.append(new_r)

        elapsed = time.perf_counter() - start_time

        # Build full Route objects with depot at both ends
        route_objects: List[Route] = []
        total_distance = 0.0
        total_demand = 0.0
        total_deliveries = 0

        for v_id, customer_seq in enumerate(routes, start=1):
            full_nodes = [d0] + customer_seq + [d0]
            
            # Compute distance for this vehicle route
            r_dist = sum(self.dist[full_nodes[k], full_nodes[k + 1]] for k in range(len(full_nodes) - 1))
            r_demand = sum(self.demands[k] for k in customer_seq)
            r_deliveries = len(customer_seq)

            route_obj = Route(
                vehicle_id=v_id,
                node_indices=full_nodes,
                node_ids=[self.locations[k].id for k in full_nodes],
                node_names=[self.locations[k].name for k in full_nodes],
                total_distance_km=r_dist,
                total_demand_kg=r_demand,
                num_deliveries=r_deliveries
            )
            route_obj.compute_summary()
            route_objects.append(route_obj)

            total_distance += r_dist
            total_demand += r_demand
            total_deliveries += r_deliveries

        solution = VRPSolution(
            algorithm_name="Clarke-Wright Savings (VRP)",
            routes=route_objects,
            total_distance_km=total_distance,
            total_demand_kg=total_demand,
            total_deliveries=total_deliveries,
            num_vehicles=len(route_objects),
            vehicle_capacity_kg=self.capacity,
            execution_time_sec=elapsed,
            is_feasible=True
        )

        return solution
