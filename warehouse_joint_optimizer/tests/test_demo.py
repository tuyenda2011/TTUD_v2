from pathlib import Path

import pytest


def test_streamlit_end_to_end():
    pytest.importorskip("streamlit")
    pytest.importorskip("matplotlib")
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "demo" / "app.py"), default_timeout=30)
    app.run()
    assert not app.exception
    assert app.number_input(key="orders").value == 10
    app.number_input(key="orders").set_value(8)
    app.slider(key="budget").set_value(.2)
    app.checkbox(key="vns").check()
    app.button(key="run").click().run()
    assert not app.exception
    assert not app.error
    assert len(app.metric) == 3
    assert "snapshot" in app.session_state
    snapshot = app.session_state["snapshot"]
    assert set(snapshot["results"]) == {"B0", "ALNS", "VNS"}
    assert snapshot["results"]["ALNS"]["feasible"]
    # Selecting another result only displays the frozen run; it does not rerun search.
    duration = snapshot["results"]["ALNS"]["timing"]["total_seconds"]
    app.selectbox(key="result_method").set_value("B0").run()
    assert not app.exception
    assert app.session_state["snapshot"]["results"]["ALNS"]["timing"]["total_seconds"] == duration
    app.number_input(key="seed").set_value(43).run()
    assert any("chưa được áp dụng" in msg.value for msg in app.info)
    assert app.session_state["snapshot"]["seed"] == 42
    app.selectbox(key="source").set_value("JSON tải lên").run()
    assert not any(w.key == "orders" for w in app.number_input)
    app.button(key="run").click().run()
    assert app.error
    assert "snapshot" not in app.session_state
    assert not app.exception
