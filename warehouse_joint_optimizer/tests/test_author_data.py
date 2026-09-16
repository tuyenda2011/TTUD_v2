from pathlib import Path

import pytest

from warehouse_opt.author_data import read_kris
from warehouse_opt.models import InputError
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import solve
from warehouse_opt.validator import validate_solution

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/KrisSmallDataCorrected/small/instances_100_1.txt"


@pytest.fixture
def raw_path():
    if not RAW.exists():
        pytest.skip("Author archive not downloaded")
    return RAW


def test_source_fields_preserved(raw_path):
    instance = read_kris(raw_path)
    assert len(instance.orders) == 18
    assert instance.operations.pickers == 2
    assert instance.operations.capacity == 12
    assert instance.operations.batch_minutes == 5400
    assert instance.operations.speed == 1 / 3
    assert instance.operations.location_minutes == 0
    assert instance.orders[0].due == 36000
    assert instance.orders[0].items == {"1": 1}
    assert instance.products[0].pick_minutes == 300
    assert instance.metadata["due_dates"]["regenerated"] is False
    assert instance.metadata["conversion"]["depot_contraction_verified"] is True


@pytest.mark.parametrize("method", ["B0", "B1", "B2", "B3", "LNS", "ALNS"])
def test_author_instance_solution_valid(raw_path, method):
    instance = read_kris(raw_path)
    result = solve(instance, method, config=SearchConfig(iterations=5, seconds=0, candidate_limit=8))
    assert validate_solution(instance, result) == []
    assert all(row["due"] == next(o.due for o in instance.orders if o.id == row["id"]) for row in result["orders"])


def test_reject_changed_depot(raw_path, tmp_path):
    path = tmp_path / "invalid.txt"
    path.write_text(raw_path.read_text().replace('72 0.0 0.0 "depot"', '72 1.0 0.0 "depot"'))
    with pytest.raises(InputError, match="Distinct physical depots"):
        read_kris(path)


def test_author_demo_selected_source():
    pytest.importorskip("streamlit")
    pytest.importorskip("matplotlib")
    if not (ROOT / "data/processed/kris_small/catalog.json").exists():
        pytest.skip("Author dataset not prepared")
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / "demo/app.py"), default_timeout=30).run()
    assert not app.exception
    app.selectbox(key="source").set_value("Kris — benchmark tác giả").run()
    assert not any(w.key == "orders" for w in app.number_input)
    app.slider(key="budget").set_value(.2)
    app.button(key="run").click().run()
    assert not app.exception
    assert not app.error
    snapshot = app.session_state["snapshot"]
    assert snapshot["instance"]["metadata"]["due_dates"]["regenerated"] is False
    assert snapshot["results"]["ALNS"]["feasible"]


def test_imported_shortest_paths_match_author_matrix(raw_path):
    from warehouse_opt.graph import WarehouseGraph
    instance = read_kris(raw_path)
    graph = WarehouseGraph(instance)
    source = instance.metadata["source_parameters"]
    depot_start, depot_end = str(int(source["DepartingDepot"])), str(int(source["ArrivalDepot"]))
    locations = {p.location for p in instance.products}
    in_matrix = False
    checked = 0
    for line in raw_path.read_text().splitlines():
        if line.startswith("//LocStart LocEnd ShortestPath"):
            in_matrix = True
            continue
        if line.startswith("//") and in_matrix:
            break
        if in_matrix and line.strip():
            a, b, distance = line.split()
            if (a in locations or a == depot_start) and (b in locations or b == depot_end) and not (a == depot_start and b == depot_end):
                assert graph.distance(a, depot_start if b == depot_end else b) == pytest.approx(float(distance))
                checked += 1
    assert checked > len(locations) ** 2
