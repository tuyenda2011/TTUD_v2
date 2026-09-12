"""
Location data model for Shipper Route Optimizer.
Includes GPS coordinates, district information, demand payload, and Haversine distance calculations.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Location:
    """Represents a geographic point (Depot or Delivery customer)."""
    id: str
    name: str
    district: str
    lat: float
    lng: float
    demand_kg: float = 0.0
    is_depot: bool = False
    traffic_zone: str = "low"  # none, low, medium, high
    peak_hour_multiplier: float = 1.0  # Thời gian x multiplier khi cao điểm

    def __post_init__(self):
        if self.id == "D0" or "kho" in self.name.lower() or "depot" in self.name.lower():
            self.is_depot = True
        if self.traffic_zone == "none":
            self.peak_hour_multiplier = 1.0

    def distance_to(self, other: Location, formula: str = "haversine") -> float:
        """
        Calculate distance between this location and another in kilometers.
        
        Args:
            other: Target Location object
            formula: 'haversine' (default spherical) or 'euclidean_approx'
            
        Returns:
            Distance in kilometers (km)
        """
        if formula == "haversine":
            return haversine_distance(self.lat, self.lng, other.lat, other.lng)
        else:
            # Flat-surface approximation around Hanoi coordinates
            # 1 deg latitude ≈ 111.0 km, 1 deg longitude ≈ 111.0 * cos(lat) km
            lat_mid_rad = math.radians((self.lat + other.lat) / 2.0)
            dx = (other.lng - self.lng) * 111.0 * math.cos(lat_mid_rad)
            dy = (other.lat - self.lat) * 111.0
            return math.sqrt(dx * dx + dy * dy)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "district": self.district,
            "lat": self.lat,
            "lng": self.lng,
            "demand_kg": self.demand_kg,
            "is_depot": self.is_depot
        }


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth in km.
    Radius of earth = 6371.0088 km
    """
    R = 6371.0088  # Mean Earth radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    
    # Avoid numerical instability with floating point precision
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c
