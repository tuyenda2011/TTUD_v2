"""
GraphHopper API Integration for Real Route Distances
"""
import requests
import time
from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class GraphHopperRoute:
    """Route result from GraphHopper"""
    distance_km: float
    time_minutes: float
    distance_matrix_idx: Optional[List[List[float]]] = None


class GraphHopperAPI:
    """
    GraphHopper Routing API client
    Docs: https://docs.graphhopper.com/
    """
    BASE_URL = "https://graphhopper.com/api/1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_route(self, lat1: float, lng1: float, lat2: float, lng2: float) -> Optional[GraphHopperRoute]:
        """
        Get route between two points.

        Args:
            lat1, lng1: Start coordinates
            lat2, lng2: End coordinates

        Returns:
            GraphHopperRoute with distance_km and time_minutes
        """
        url = f"{self.BASE_URL}/route"
        params = {
            "point": [f"{lat1},{lng1}", f"{lat2},{lng2}"],
            "vehicle": "car",
            "locale": "vi",
            "key": self.api_key,
            "points_encoded": "false"
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            # Check if response has valid paths
            if 'paths' in data and len(data['paths']) > 0:
                path = data['paths'][0]
                return GraphHopperRoute(
                    distance_km=path['distance'] / 1000,  # Convert m to km
                    time_minutes=path['time'] / 60000    # Convert ms to minutes
                )
            elif 'message' in data:
                print(f"GraphHopper error: {data['message']}")
                return None
            else:
                print(f"GraphHopper error: Invalid response")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def build_distance_matrix(self, locations: List, max_requests: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build distance and time matrices using GraphHopper API.
        ALWAYS returns a complete n x n matrix.

        Args:
            locations: List of Location objects
            max_requests: Limit API calls (recommended: 10 for quick test)

        Returns:
            (distance_matrix_km, time_matrix_min) - both n x n
        """
        n = len(locations)
        dist_matrix = np.zeros((n, n))
        time_matrix = np.zeros((n, n))

        # Default to 10 for quick test (avoid long waits)
        if max_requests is None:
            max_requests = 10
        else:
            max_requests = min(max_requests, 50)  # Cap at 50 for free tier

        print(f"Building GraphHopper distance matrix ({n} points)...")
        call_count = 0

        for i in range(n):
            for j in range(i + 1, n):
                # Diagonal is 0
                dist_matrix[i, i] = 0
                time_matrix[i, i] = 0

                if call_count >= max_requests:
                    # Use Haversine for remaining
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
                    locations[j].lat, locations[j].lng
                )

                if route:
                    dist_matrix[i, j] = dist_matrix[j, i] = route.distance_km
                    time_matrix[i, j] = time_matrix[j, i] = route.time_minutes
                else:
                    # Fallback to Haversine
                    from src.models.location import haversine_distance
                    d = haversine_distance(
                        locations[i].lat, locations[i].lng,
                        locations[j].lat, locations[j].lng
                    )
                    dist_matrix[i, j] = dist_matrix[j, i] = d
                    time_matrix[i, j] = time_matrix[j, i] = d / 40 * 60

                call_count += 1

                # Rate limiting: 1.2 seconds between requests
                time.sleep(1.2)

                if call_count % 5 == 0:
                    print(f"  API calls: {call_count}/{max_requests}")

        print(f"GraphHopper matrix complete: {n}x{n}")
        print(f"  (Used {min(call_count, max_requests)} API calls, rest used Haversine)")

        return dist_matrix, time_matrix

    def test_connection(self) -> bool:
        """Test if API key is valid"""
        route = self.get_route(20.9821, 105.7913, 21.0285, 105.7891)
        if route:
            print("[OK] GraphHopper API connected!")
            print(f"   Test route: Kho V9 -> Cau Giay")
            print(f"   Distance: {route.distance_km:.2f} km")
            print(f"   Time: {route.time_minutes:.1f} minutes")
            return True
        return False


# Test
if __name__ == "__main__":
    API_KEY = "b10e32bf-7b05-4762-977b-ee3c7af85080"
    gh = GraphHopperAPI(API_KEY)
    gh.test_connection()
