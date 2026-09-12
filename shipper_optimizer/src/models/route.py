"""
Route and Solution models for TSP and VRP optimization.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json


@dataclass
class Route:
    """Represents a single vehicle route starting and ending at the depot."""
    vehicle_id: int
    node_indices: List[int]           # Indices in distance matrix
    node_ids: List[str]               # Node IDs, e.g., ['D0', 'D1', 'D5', 'D0']
    node_names: List[str]             # Node names
    total_distance_km: float = 0.0
    total_demand_kg: float = 0.0
    num_deliveries: int = 0
    estimated_travel_time_min: float = 0.0  # Assumes 25 km/h urban speed + 5 min per stop

    def compute_summary(self, avg_speed_kmh: float = 25.0, stop_time_min: float = 5.0):
        """Compute estimated travel and service time."""
        travel_time = (self.total_distance_km / avg_speed_kmh) * 60.0
        service_time = self.num_deliveries * stop_time_min
        self.estimated_travel_time_min = travel_time + service_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "node_ids": self.node_ids,
            "node_names": self.node_names,
            "total_distance_km": round(self.total_distance_km, 2),
            "total_demand_kg": round(self.total_demand_kg, 2),
            "num_deliveries": self.num_deliveries,
            "estimated_travel_time_min": round(self.estimated_travel_time_min, 1)
        }


@dataclass
class VRPSolution:
    """Represents a complete solution for VRP or TSP."""
    algorithm_name: str
    routes: List[Route] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_demand_kg: float = 0.0
    total_deliveries: int = 0
    num_vehicles: int = 0
    vehicle_capacity_kg: float = 500.0
    execution_time_sec: float = 0.0
    is_feasible: bool = True
    optimality_gap_percent: Optional[float] = None
    fuel_cost_vnd: float = 0.0  # Estimated: 1 liter RON95 (24,000 VND) / 10 km (~2,400 VND/km)

    def __post_init__(self):
        if self.routes and self.total_distance_km == 0.0:
            self.total_distance_km = sum(r.total_distance_km for r in self.routes)
            self.total_demand_kg = sum(r.total_demand_kg for r in self.routes)
            self.total_deliveries = sum(r.num_deliveries for r in self.routes)
            self.num_vehicles = len(self.routes)
        
        # Estimate fuel cost (~2,400 VND/km for small delivery truck or ~600 VND/km for motorbike)
        # Using light delivery truck average 2,400 VND / km
        self.fuel_cost_vnd = self.total_distance_km * 2400.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm_name": self.algorithm_name,
            "total_distance_km": round(self.total_distance_km, 2),
            "total_demand_kg": round(self.total_demand_kg, 2),
            "total_deliveries": self.total_deliveries,
            "num_vehicles": self.num_vehicles,
            "vehicle_capacity_kg": self.vehicle_capacity_kg,
            "execution_time_sec": round(self.execution_time_sec, 4),
            "is_feasible": self.is_feasible,
            "optimality_gap_percent": round(self.optimality_gap_percent, 2) if self.optimality_gap_percent is not None else None,
            "fuel_cost_vnd": round(self.fuel_cost_vnd, 0),
            "routes": [r.to_dict() for r in self.routes]
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
