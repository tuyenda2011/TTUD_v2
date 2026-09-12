"""
Unit tests for Shipper Route Optimizer algorithms and data structures.
Run with: pytest tests/
"""

import os
import pytest
import numpy as np

from src.models.location import Location, haversine_distance
from src.data.loader import load_deliveries, build_distance_matrix, get_depot_index
from src.algorithms.dijkstra import Dijkstra
from src.algorithms.nearest_neighbor import NearestNeighbor
from src.algorithms.clarke_wright import ClarkeWrightSavings
from src.algorithms.two_opt import TwoOpt
from src.algorithms.benchmark import BenchmarkEngine


@pytest.fixture
def sample_dataset():
    """Load default Hanoi 30 delivery points dataset."""
    locations = load_deliveries()
    dist_matrix = build_distance_matrix(locations)
    depot_idx = get_depot_index(locations)
    return locations, dist_matrix, depot_idx


def test_haversine_distance():
    """Test Haversine distance between known coordinates."""
    # Hanoi center (Hoan Kiem) to Noi Bai Airport
    lat1, lng1 = 21.0285, 105.8542
    lat2, lng2 = 21.2212, 105.8072
    dist = haversine_distance(lat1, lng1, lat2, lng2)
    # Expected distance ~ 22.0 km
    assert 20.0 < dist < 24.0

    # Distance to self must be 0
    assert haversine_distance(lat1, lng1, lat1, lng1) == 0.0


def test_dataset_loading(sample_dataset):
    locations, dist_matrix, depot_idx = sample_dataset
    assert len(locations) == 31  # 1 Depot + 30 Customers
    assert locations[0].is_depot is True
    assert depot_idx == 0
    assert dist_matrix.shape == (31, 31)
    # Symmetry check
    np.testing.assert_allclose(dist_matrix, dist_matrix.T, atol=1e-5)


def test_dijkstra_shortest_path(sample_dataset):
    locations, dist_matrix, _ = sample_dataset
    dijkstra = Dijkstra(locations, dist_matrix)
    
    # Test shortest path from D0 to D1
    dist_val, path = dijkstra.shortest_path(0, 1)
    assert dist_val > 0.0
    assert path[0] == 0
    assert path[-1] == 1
    assert dist_val == pytest.approx(dist_matrix[0, 1], rel=1e-4)


def test_nearest_neighbor_tsp(sample_dataset):
    locations, dist_matrix, depot_idx = sample_dataset
    nn = NearestNeighbor(locations, dist_matrix, depot_idx=depot_idx)
    solution = nn.solve()

    assert solution.is_feasible is True
    assert solution.num_vehicles == 1
    route = solution.routes[0]
    
    # Tour starts and ends at depot
    assert route.node_indices[0] == depot_idx
    assert route.node_indices[-1] == depot_idx
    
    # All nodes visited
    unique_visited = set(route.node_indices)
    assert len(unique_visited) == len(locations)
    assert solution.total_distance_km > 0.0


def test_clarke_wright_savings(sample_dataset):
    locations, dist_matrix, depot_idx = sample_dataset
    capacity = 200.0  # kg
    cw = ClarkeWrightSavings(locations, dist_matrix, vehicle_capacity=capacity, depot_idx=depot_idx)
    solution = cw.solve()

    assert solution.is_feasible is True
    assert solution.num_vehicles > 1
    
    # Verify every delivery is visited exactly once
    all_visited = []
    for r in solution.routes:
        # Check capacity constraint
        assert r.total_demand_kg <= capacity + 1e-4
        assert r.node_indices[0] == depot_idx
        assert r.node_indices[-1] == depot_idx
        all_visited.extend(r.node_indices[1:-1])

    assert sorted(all_visited) == list(range(1, len(locations)))


def test_two_opt_improvement(sample_dataset):
    locations, dist_matrix, depot_idx = sample_dataset
    nn = NearestNeighbor(locations, dist_matrix, depot_idx=depot_idx)
    sol_nn = nn.solve()
    
    two_opt = TwoOpt(dist_matrix)
    sol_opt = two_opt.optimize_solution(sol_nn, locations)
    
    # 2-Opt must not make the tour worse
    assert sol_opt.total_distance_km <= sol_nn.total_distance_km + 1e-5


def test_full_benchmark_engine(sample_dataset, tmp_path):
    locations, dist_matrix, depot_idx = sample_dataset
    engine = BenchmarkEngine(locations, dist_matrix, vehicle_capacity_kg=200.0, depot_idx=depot_idx)
    solutions = engine.run_all()

    assert "Nearest Neighbor (TSP)" in solutions
    assert "Clarke-Wright + 2-Opt (VRP)" in solutions
    
    # Clarke-Wright + 2-Opt should have better distance or multi-vehicle compliance
    table = engine.generate_summary_table()
    assert len(table) > 100
    
    json_path = os.path.join(tmp_path, "results.json")
    engine.export_results_json(json_path)
    assert os.path.exists(json_path)
