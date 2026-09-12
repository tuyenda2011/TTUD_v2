"""
Benchmark and Evaluation Engine for Shipper Route Optimizer.
Compares Dijkstra, Nearest Neighbor, Nearest Neighbor + 2-Opt, Clarke-Wright, and Clarke-Wright + 2-Opt.
"""

from __future__ import annotations
import os
import json
import time
from typing import List, Dict, Optional, Any
import numpy as np

from src.models.location import Location
from src.models.route import VRPSolution
from src.algorithms.dijkstra import Dijkstra
from src.algorithms.nearest_neighbor import NearestNeighbor
from src.algorithms.clarke_wright import ClarkeWrightSavings
from src.algorithms.two_opt import TwoOpt


class BenchmarkEngine:
    """
    Runs multi-algorithm benchmark and produces evaluation reports.
    """
    def __init__(
        self,
        locations: List[Location],
        distance_matrix: np.ndarray,
        vehicle_capacity_kg: float = 200.0,
        depot_idx: int = 0
    ):
        self.locations = locations
        self.dist = distance_matrix
        self.n = len(locations)
        self.capacity = vehicle_capacity_kg
        self.depot_idx = depot_idx
        self.solutions: Dict[str, VRPSolution] = {}
        self.dijkstra_stats: Dict[str, Any] = {}

    def run_all(self) -> Dict[str, VRPSolution]:
        """Execute all algorithms and gather solutions."""
        print("\n🚀 [1/5] Running Dijkstra Shortest Path Analysis...")
        dijkstra = Dijkstra(self.locations, self.dist)
        _, d_time = dijkstra.compute_all_pairs_matrix()
        self.dijkstra_stats = dijkstra.get_summary_statistics()
        self.dijkstra_stats["dijkstra_time_sec"] = d_time
        print(f"      ✓ Matrix: {self.dijkstra_stats['matrix_shape']}, Avg distance: {self.dijkstra_stats['avg_distance_km']} km (took {d_time:.4f}s)")

        print("🚀 [2/5] Running Nearest Neighbor (TSP)...")
        nn_solver = NearestNeighbor(self.locations, self.dist, depot_idx=self.depot_idx)
        sol_nn = nn_solver.solve()
        self.solutions["Nearest Neighbor (TSP)"] = sol_nn
        print(f"      ✓ Total Distance: {sol_nn.total_distance_km:.2f} km | Time: {sol_nn.execution_time_sec:.4f}s")

        print("🚀 [3/5] Running Nearest Neighbor + 2-Opt (TSP Optimized)...")
        two_opt = TwoOpt(self.dist)
        sol_nn_2opt = two_opt.optimize_solution(sol_nn, self.locations, name_suffix=" + 2-Opt")
        self.solutions["NN + 2-Opt (TSP)"] = sol_nn_2opt
        print(f"      ✓ Total Distance: {sol_nn_2opt.total_distance_km:.2f} km | Time: {sol_nn_2opt.execution_time_sec:.4f}s")

        print(f"🚀 [4/5] Running Clarke-Wright Savings (VRP, Capacity={self.capacity} kg)...")
        cw_solver = ClarkeWrightSavings(
            self.locations,
            self.dist,
            vehicle_capacity=self.capacity,
            depot_idx=self.depot_idx
        )
        sol_cw = cw_solver.solve()
        self.solutions["Clarke-Wright (VRP)"] = sol_cw
        print(f"      ✓ Total Distance: {sol_cw.total_distance_km:.2f} km | Vehicles: {sol_cw.num_vehicles} | Time: {sol_cw.execution_time_sec:.4f}s")

        print("🚀 [5/5] Running Clarke-Wright + 2-Opt (VRP Hybrid Optimal)...")
        sol_cw_2opt = two_opt.optimize_solution(sol_cw, self.locations, name_suffix=" + 2-Opt")
        self.solutions["Clarke-Wright + 2-Opt (VRP)"] = sol_cw_2opt
        print(f"      ✓ Total Distance: {sol_cw_2opt.total_distance_km:.2f} km | Vehicles: {sol_cw_2opt.num_vehicles} | Time: {sol_cw_2opt.execution_time_sec:.4f}s")

        return self.solutions

    def generate_summary_table(self) -> str:
        """Create formatted ASCII comparison table."""
        if not self.solutions:
            return "No benchmark results available. Run run_all() first."

        base_dist = self.solutions["Nearest Neighbor (TSP)"].total_distance_km

        lines = [
            "┌─────────────────────────────────────┬────────────┬──────────┬───────────┬──────────────┬───────────────┐",
            "│ Algorithm                           │ Total KM   │ Vehicles │ Time (s)  │ vs Baseline  │ Fuel Cost/trip│",
            "├─────────────────────────────────────┼────────────┼──────────┼───────────┼──────────────┼───────────────┤"
        ]

        for name, sol in self.solutions.items():
            dist_km = sol.total_distance_km
            diff_pct = ((dist_km - base_dist) / base_dist) * 100.0
            diff_str = f"{diff_pct:+.1f}%" if name != "Nearest Neighbor (TSP)" else "Baseline"
            fuel_str = f"{int(sol.fuel_cost_vnd):,} VND"
            
            line = f"│ {name:<35} │ {dist_km:>8.2f} km │ {sol.num_vehicles:>8} │ {sol.execution_time_sec:>7.4f}s  │ {diff_str:>12} │ {fuel_str:>13} │"
            lines.append(line)

        lines.append("└─────────────────────────────────────┴────────────┴──────────┴───────────┴──────────────┴───────────────┘")
        return "\n".join(lines)

    def calculate_cost_savings(self) -> Dict[str, Any]:
        """Compute estimated fuel and annual financial savings for TSP and VRP."""
        d0 = self.depot_idx
        # Baseline 1: Naive roundtrips (every customer served separately from depot: depot -> i -> depot)
        naive_vrp_km = sum(2.0 * self.dist[d0, i] for i in range(self.n) if i != d0)
        
        # TSP comparison
        nn_km = self.solutions.get("Nearest Neighbor (TSP)", None)
        nn_2opt_km = self.solutions.get("NN + 2-Opt (TSP)", None)
        
        tsp_saved_km = (nn_km.total_distance_km - nn_2opt_km.total_distance_km) if (nn_km and nn_2opt_km) else 0.0
        tsp_saved_pct = (tsp_saved_km / nn_km.total_distance_km * 100.0) if nn_km else 0.0

        # VRP comparison vs naive roundtrips
        cw_2opt = self.solutions.get("Clarke-Wright + 2-Opt (VRP)", None)
        vrp_km = cw_2opt.total_distance_km if cw_2opt else 0.0
        vrp_saved_km = max(0.0, naive_vrp_km - vrp_km)
        vrp_saved_pct = (vrp_saved_km / naive_vrp_km * 100.0) if naive_vrp_km > 0 else 0.0

        fuel_per_km = 2400.0  # VND/km
        annual_trips = 365

        return {
            "naive_separate_routes_km": round(naive_vrp_km, 2),
            "vrp_optimized_km": round(vrp_km, 2),
            "vrp_saved_km": round(vrp_saved_km, 2),
            "vrp_saved_pct": round(vrp_saved_pct, 1),
            "vrp_annual_saved_vnd": int(vrp_saved_km * fuel_per_km * annual_trips),
            "tsp_raw_nn_km": round(nn_km.total_distance_km, 2) if nn_km else 0.0,
            "tsp_2opt_km": round(nn_2opt_km.total_distance_km, 2) if nn_2opt_km else 0.0,
            "tsp_saved_km": round(tsp_saved_km, 2),
            "tsp_saved_pct": round(tsp_saved_pct, 1),
            "tsp_annual_saved_vnd": int(tsp_saved_km * fuel_per_km * annual_trips)
        }

    def export_results_json(self, output_path: str):
        """Export full benchmark dataset to JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        data = {
            "dijkstra_stats": self.dijkstra_stats,
            "cost_savings": self.calculate_cost_savings(),
            "solutions": {name: sol.to_dict() for name, sol in self.solutions.items()}
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
