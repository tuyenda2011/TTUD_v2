from pathlib import Path

import pytest

from warehouse_opt.generator import generate
from warehouse_opt.models import InputError, Instance


@pytest.mark.parametrize("field,value", [
    ("units", None), ("units", []), ("units", {"time": 60}),
    ("units", {"distance": ""}), ("layout", "single_block"),
    ("layout", {"type": "single_block", "aisles": []}),
    ("layout", {"type": "single_block", "aisles": [["missing", "node"]]}),
    ("layout", {"type": "single_block", "aisles": [None]}),
])
def test_invalid_plot_metadata_rejected_before_solve(field, value):
    data = generate(3, 42).to_dict()
    data["metadata"][field] = value
    with pytest.raises(InputError, match="metadata"):
        Instance.from_dict(data)


def test_uploaded_custom_units_are_preserved_in_demo():
    pytest.importorskip("streamlit")
    pytest.importorskip("matplotlib")
    from streamlit.testing.v1 import AppTest

    from warehouse_opt.solver import solve

    instance = generate(2, 42)
    instance.metadata["units"] = {"distance": "feet", "time": "seconds", "capacity": "kg"}
    snapshot = {"instance": instance.to_dict(), "seed": 42, "results": {"B0": solve(instance, "B0")}}
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "demo/app.py")).run()
    app.session_state["snapshot"] = snapshot
    app.run()
    assert not app.exception
    assert app.metric[1].value.endswith("seconds")
    assert app.metric[2].value.endswith("feet")


def test_bad_snapshot_shape_is_input_error():
    from warehouse_opt.demo_snapshot import validate_snapshot

    for snapshot in (None, [], {}, {"instance": generate(2).to_dict(), "results": []},
                     {"instance": generate(2).to_dict(), "results": {"ALNS": {}, "B0": None}}):
        with pytest.raises(InputError):
            validate_snapshot(snapshot)
