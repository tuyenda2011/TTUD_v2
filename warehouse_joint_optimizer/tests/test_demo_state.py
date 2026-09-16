import copy
import json
from pathlib import Path

import pytest

from demo.state import (
    KRIS,
    SYNTHETIC,
    UPLOAD,
    fail_run,
    finish_run,
    improvement,
    is_stale,
    methods_for,
    prepare_instance,
    run_scenario,
    start_run,
    upload_digest,
)
from warehouse_opt.demo_snapshot import validate_snapshot
from warehouse_opt.models import InputError

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def draft():
    return {"source": SYNTHETIC, "orders": 3, "pickers": 3, "capacity": 20,
            "tightness": .15, "seed": 42, "seconds": .2, "vns": False, "comparison": False}


def test_default_run_and_export(draft):
    instance = prepare_instance(draft, ROOT)
    messages = []
    snapshot = run_scenario(instance, draft, lambda value, text: messages.append(text))
    assert methods_for(draft) == ["B0", "ALNS"]
    assert set(snapshot["results"]) == {"B0", "ALNS"}
    assert len(messages) == 2
    assert validate_snapshot(json.loads(json.dumps(snapshot)))
    state = {}
    start_run(state)
    finish_run(state, snapshot)
    assert state["run_status"] == "success"
    assert not is_stale(snapshot, draft)
    draft["seed"] += 1
    assert is_stale(snapshot, draft)
    assert snapshot["draft"]["seed"] == 42
    start_run(state)
    assert "snapshot" not in state
    fail_run(state, "invalid input")
    assert state == {"run_status": "error", "run_error": "invalid input"}


def test_upload_valid_invalid_and_changed_bytes(draft):
    instance = prepare_instance(draft, ROOT)
    content = json.dumps(instance.to_dict()).encode()
    uploaded = {**draft, "source": UPLOAD, "upload_sha256": upload_digest(content)}
    assert prepare_instance(uploaded, ROOT, content).to_dict() == instance.to_dict()
    assert upload_digest(content) != upload_digest(content + b" ")
    for data in (None, b"{}", b"not json", b"[]", b"null"):
        with pytest.raises((InputError, ValueError)):
            prepare_instance(uploaded, ROOT, data)
    broken = copy.deepcopy(instance.to_dict())
    broken["operations"]["capacity"] = .1
    with pytest.raises(InputError):
        prepare_instance(uploaded, ROOT, json.dumps(broken).encode())


def test_kris_path_cannot_escape_dataset(draft):
    with pytest.raises(InputError):
        prepare_instance({**draft, "source": KRIS, "file": "../README.md"}, ROOT)


def test_zero_baseline():
    assert improvement(0, 0) is None
    assert improvement(10, 0) is None
    assert improvement(8, 10) == 20
    assert improvement(12, 10) == -20


def test_filters_idle_picker_and_default_methods():
    pytest.importorskip("streamlit")
    pytest.importorskip("matplotlib")
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / "demo/app.py"), default_timeout=30).run()
    app.number_input(key="orders").set_value(1)
    app.slider(key="budget").set_value(.2)
    app.button(key="run").click().run()
    assert not app.exception
    assert set(app.session_state["snapshot"]["results"]) == {"B0", "ALNS"}
    assert app.selectbox(key="route_batch").value != "Tất cả"
    app.selectbox(key="route_picker").set_value(3).run()
    assert not app.exception
    assert any("không có chuyến" in row.value for row in app.info)
    assert not any(w.key == "route_batch" for w in app.selectbox)
    app.selectbox(key="route_picker").set_value(1).run()
    assert app.selectbox(key="route_batch").value == "P1-B1"
