"""
Data loading and preprocessing utilities for Shipper Route Optimizer.
"""

from __future__ import annotations
import os
import csv
from typing import List, Dict, Tuple, Optional
import numpy as np

from src.models.location import Location, haversine_distance


def get_default_csv_path() -> str:
    """Find default CSV path in the project hierarchy."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(current_dir, "hanoi_deliveries.csv"),
        os.path.join(current_dir, "..", "..", "data", "hanoi_deliveries.csv"),
        os.path.join(os.getcwd(), "data", "hanoi_deliveries.csv"),
        os.path.join(os.getcwd(), "src", "data", "hanoi_deliveries.csv")
    ]
    for p in candidates:
        norm_p = os.path.normpath(p)
        if os.path.exists(norm_p):
            return norm_p
    return os.path.normpath(candidates[0])


def load_deliveries(csv_path: Optional[str] = None) -> List[Location]:
    """
    Load delivery locations from CSV file.
    
    Format expected:
        id,name,district,lat,lng,demand_kg
    """
    if csv_path is None or not os.path.exists(csv_path):
        csv_path = get_default_csv_path()
        
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Cannot find delivery dataset at: {csv_path}")

    locations: List[Location] = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            loc_id = row.get("id", "").strip()
            name = row.get("name", "").strip()
            district = row.get("district", "").strip()
            lat = float(row.get("lat", 0.0))
            lng = float(row.get("lng", 0.0))
            demand_kg = float(row.get("demand_kg", 0.0))
            traffic_zone = row.get("traffic_zone", "low")
            peak_multiplier = float(row.get("peak_hour_multiplier", 1.0))

            is_depot = (loc_id == "D0" or "kho" in name.lower())

            loc = Location(
                id=loc_id,
                name=name,
                district=district,
                lat=lat,
                lng=lng,
                demand_kg=demand_kg,
                is_depot=is_depot,
                traffic_zone=traffic_zone,
                peak_hour_multiplier=peak_multiplier
            )
            locations.append(loc)

    return locations


def build_distance_matrix(locations: List[Location]) -> np.ndarray:
    """
    Compute pairwise Haversine distance matrix (n x n) in kilometers.
    """
    n = len(locations)
    matrix = np.zeros((n, n), dtype=float)
    
    for i in range(n):
        for j in range(i + 1, n):
            d = locations[i].distance_to(locations[j])
            matrix[i, j] = d
            matrix[j, i] = d
            
    return matrix


def get_demands(locations: List[Location]) -> List[float]:
    """Extract demands list in kg matching location indices."""
    return [loc.demand_kg for loc in locations]


def get_depot_index(locations: List[Location]) -> int:
    """Find index of the depot location (defaults to 0)."""
    for idx, loc in enumerate(locations):
        if loc.is_depot:
            return idx
    return 0
