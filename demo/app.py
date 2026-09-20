"""Run from project root: python -m streamlit run demo/app.py."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import streamlit as st

from demo.components import instance_summary, results_view, sidebar, style
from demo.state import (
    fail_run,
    finish_run,
    is_stale,
    prepare_instance,
    run_scenario,
    start_run,
)
from src.demo_snapshot import validate_snapshot
from src.models import Instance

st.set_page_config(page_title="Tối ưu lấy hàng", page_icon="📦", layout="wide")
style()


def begin():
    start_run(st.session_state)


@st.cache_data(show_spinner=False, max_entries=8)
def prepared(draft, content):
    return prepare_instance(draft, ROOT, content).to_dict()


draft, content = sidebar(ROOT, begin)
st.title("Tối ưu lấy hàng")
st.caption("Gom đơn thành chuyến · Chọn đường đi · Phân công nhân viên")

if st.session_state.get("run_status") == "running":
    progress = st.progress(0, text="Đang kiểm tra dữ liệu...")
    try:
        instance = Instance.from_dict(prepared(draft, content))
        snapshot = run_scenario(instance, draft, lambda value, text: progress.progress(value, text=text))
        finish_run(st.session_state, snapshot)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        fail_run(st.session_state, exc)
    progress.empty()
    st.rerun()

saved = ROOT / "results/demo_vns/snapshot.json"
if saved.is_file():
    with st.sidebar:
        if st.button("Mở lần chạy đã lưu", key="open_saved"):
            try:
                snapshot = validate_snapshot(json.loads(saved.read_text(encoding="utf-8")))
                start_run(st.session_state)
                finish_run(st.session_state, {**snapshot, "saved_playback": True})
                st.rerun()
            except (OSError, ValueError, KeyError, TypeError) as exc:
                fail_run(st.session_state, exc)

if st.session_state.get("run_status") == "error":
    st.error(f"Không thể chạy: {st.session_state['run_error']}")

snapshot = st.session_state.get("snapshot")
if snapshot:
    if is_stale(snapshot, draft):
        st.info("Đang xem kết quả của cấu hình đã lưu. Cấu hình bên trái chưa được áp dụng; bấm Chạy tối ưu để chạy lại.")
    results_view(snapshot)
else:
    st.subheader("Sẵn sàng cho lần chạy đầu tiên")
    try:
        instance = Instance.from_dict(prepared(draft, content))
        instance_summary(instance)
    except (OSError, ValueError, KeyError, TypeError):
        st.write("Chọn dữ liệu trong thanh bên để bắt đầu.")
    st.write("**1. Chọn dữ liệu** — dùng mẫu có sẵn hoặc nhập kho của bạn.")
    st.write("**2. Chạy tối ưu** — ứng dụng tự gom chuyến và phân công.")
    st.write("**3. Xem phương án** — kiểm tra đơn trễ, tuyến đi và tải kết quả.")
    st.button("Chạy với cấu hình này", type="secondary", key="run_main", on_click=begin)
