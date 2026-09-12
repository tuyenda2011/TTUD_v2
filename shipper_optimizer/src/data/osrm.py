"""
OSRM (Open Source Routing Machine) API Integration
Free, no API key required
"""
import requests
import time
from typing import List, Tuple, Optional, Dict
import numpy as np
from dataclasses import dataclass


@dataclass
class OSRMRoute:
    """Route result from OSRM"""
    distance_km: float
    duration_minutes: float
    geometry: Optional[List[List[float]]] = None


class OSRMAPI:
    """
    OSRM API client - Free, no API key needed
    Uses public demo server: router.project-osrm.org
    """
    BASE_URL = "http://router.project-osrm.org"

    def __init__(self, base_url: str = None):
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_route(self, lat1: float, lng1: float, lat2: float, lng2: float, get_geometry: bool = False) -> Optional[OSRMRoute]:
        """Get route between two points."""
        coords = f"{lng1},{lat1};{lng2},{lat2}"
        url = f"{self.base_url}/route/v1/driving/{coords}"
        params = {
            "overview": "full" if get_geometry else "false",
            "steps": "false",
            "geometries": "polyline"
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('code') == 'Ok' and 'routes' in data and len(data['routes']) > 0:
                route = data['routes'][0]
                geom = None
                if get_geometry and 'geometry' in route:
                    geom = decode_polyline(route['geometry'])

                return OSRMRoute(
                    distance_km=route['distance'] / 1000,
                    duration_minutes=route['duration'] / 60,
                    geometry=geom
                )
        except Exception as e:
            print(f"OSRM error: {e}")
        return None

    def build_distance_matrix(self, locations: List, max_requests: int = 50, get_geometries: bool = True) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Build distance matrix with route geometries for map."""
        n = len(locations)
        dist_matrix = np.zeros((n, n))
        time_matrix = np.zeros((n, n))
        geometries = {}

        print(f"Building OSRM distance matrix ({n} points, max {max_requests} calls)...")
        call_count = 0

        for i in range(n):
            for j in range(i + 1, n):
                if call_count >= max_requests:
                    from src.models.location import haversine_distance
                    d = haversine_distance(
                        locations[i].lat, locations[i].lng,
                        locations[j].lat, locations[j].lng
                    )
                    dist_matrix[i, j] = dist_matrix[j, i] = d
                    time_matrix[i, j] = time_matrix[j, i] = d / 40 * 60
                    continue

                route = self.get_route(
                    locations[i].lat, locations[i].lng,
                    locations[j].lat, locations[j].lng,
                    get_geometry=get_geometries
                )

                if route:
                    dist_matrix[i, j] = dist_matrix[j, i] = route.distance_km
                    time_matrix[i, j] = time_matrix[j, i] = route.duration_minutes
                    if route.geometry:
                        geometries[(i, j)] = route.geometry
                        geometries[(j, i)] = list(reversed(route.geometry))
                else:
                    from src.models.location import haversine_distance
                    d = haversine_distance(
                        locations[i].lat, locations[i].lng,
                        locations[j].lat, locations[j].lng
                    )
                    dist_matrix[i, j] = dist_matrix[j, i] = d
                    time_matrix[i, j] = time_matrix[j, i] = d / 40 * 60

                call_count += 1
                if call_count % 10 == 0:
                    print(f"  Progress: {call_count}/{min(max_requests, n*(n-1)//2)}")
                time.sleep(0.1)

        print(f"OSRM matrix complete: {n}x{n}, {len(geometries)} route segments")
        return dist_matrix, time_matrix, geometries

    def test_connection(self) -> bool:
        """Test if OSRM server is accessible"""
        route = self.get_route(20.9821, 105.7913, 21.0285, 105.7891)
        if route:
            print("[OK] OSRM connected! Distance: {:.2f} km".format(route.distance_km))
            return True
        print("[FAIL] OSRM not available")
        return False


def decode_polyline(encoded: str) -> List[List[float]]:
    """Decode Google polyline to list of [lat, lng] coordinates."""
    index = 0
    lat = 0
    lng = 0
    coordinates = []

    while index < len(encoded):
        shift = 0
        result = 0
        byte = 0

        while byte < 0x20:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1f) << shift
            shift += 5

        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat

        shift = 0
        result = 0
        byte = 0

        while byte < 0x20:
            byte = ord(encoded[index]) - 63
            index += 1
            result |= (byte & 0x1f) << shift
            shift += 5

        dlng = ~(result >> 1) if result & 1 else result >> 1
        lng += dlng

        coordinates.append([lat / 1e5, lng / 1e5])

    return coordinates


if __name__ == "__main__":
    osrm = OSRMAPI()
    osrm.test_connection()
