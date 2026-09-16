"""Views and controls for the warehouse demo."""
import json

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from demo.state import KRIS, SYNTHETIC, UPLOAD, improvement, upload_digest
from warehouse_opt.models import Instance
from warehouse_opt.plots import gantt_figure, warehouse_figure
from warehouse_opt.units import unit_label


def style():
    st.markdown("""<style>
    .stMainBlockContainer {max-width:1120px;padding-top:3rem;padding-bottom:3rem;}
    h1 {font-size:2rem !important;letter-spacing:-.025em;}
    h2 {font-size:1.5rem !important;}
    h3 {font-size:1.1rem !important;}
    [data-testid="stMetric"] {padding:12px 0;}
    [data-testid="stMetricValue"] {font-size:2rem;}
    button:focus-visible, a:focus-visible {outline:3px solid #176B5B !important;outline-offset:3px;}
    @media(max-width:640px) {
      .stMainBlockContainer {padding:3.5rem 1rem 2rem;}
      h1 {font-size:1.65rem !important;}
      [data-testid="stMetric"] {padding:4px 0;}
    }
    </style>""", unsafe_allow_html=True)


def sidebar(root, on_run):
    content = None
    with st.sidebar:
        st.header("Chuẩn bị dữ liệu")
        source = st.selectbox("Nguồn dữ liệu", [SYNTHETIC, KRIS, UPLOAD], key="source")
        draft = {"source": source}
        if source == SYNTHETIC:
            draft["orders"] = st.number_input("Số đơn", 1, 200, 10, key="orders")
            draft["pickers"] = st.number_input("Số nhân viên", 1, 12, 3, key="pickers")
            draft["capacity"] = st.number_input("Sức chứa mỗi chuyến", 1, 500, 20, key="capacity")
        elif source == KRIS:
            try:
                catalog = json.loads((root / "data/processed/kris_small/catalog.json").read_text(encoding="utf-8"))
                by_file = {r["file"]: r for r in sorted(catalog["instances"], key=lambda r: (r["orders"], r["file"]))}
                if by_file:
                    draft["file"] = st.selectbox("Bộ dữ liệu Kris", list(by_file), key="kris_file",
                        format_func=lambda name: f"{name.split('/')[-1].removesuffix('.json')} · {by_file[name]['orders']} đơn")
                else:
                    st.caption("Chưa có dữ liệu Kris. Bạn có thể dùng dữ liệu tổng hợp.")
            except (OSError, ValueError, KeyError, TypeError):
                st.caption("Chưa đọc được catalog Kris. Bạn có thể dùng dữ liệu tổng hợp.")
        else:
            upload = st.file_uploader("File dữ liệu JSON", type=["json"], key="upload",
                                      help="File instance theo docs/SCHEMA.md, không phải file kết quả.")
            content = upload.getvalue() if upload is not None else None
            draft["upload_sha256"] = upload_digest(content)
        with st.expander("Nâng cao", expanded=False):
            if source == SYNTHETIC:
                draft["tightness"] = st.slider("Độ nới hạn", .02, 1., .15, .01, key="tightness",
                                               help="Giá trị nhỏ làm thời hạn giao đơn gấp hơn.")
            draft["seed"] = st.number_input("Seed", min_value=0, value=42, key="seed")
            draft["seconds"] = st.slider("Ngân sách mỗi thuật toán (giây)", .2, 10., 2., .2, key="budget")
            draft["vns"] = st.checkbox("So sánh thêm VNS", value=False, key="vns")
            draft["comparison"] = st.checkbox("Thêm B1, B2, B3 và LNS", value=False, key="comparison")
            st.caption("Mặc định B0 và ALNS. Ngân sách tính riêng cho từng thuật toán tìm kiếm.")
        st.button("Chạy tối ưu", type="primary", width="stretch", key="run",
                  on_click=on_run, disabled=st.session_state.get("run_status") == "running")
        st.caption("Mỗi chuyến gom nhiều đơn, lấy đủ hàng rồi quay về điểm xuất phát.")
    return draft, content


def instance_summary(instance):
    st.write(f"**{len(instance.orders)} đơn** · {instance.operations.pickers} nhân viên · "
             f"Sức chứa {instance.operations.capacity:g} {unit_label(instance, 'capacity')} mỗi chuyến")


def figure(fig):
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def route_view(instance, result):
    picker_options = list(range(1, instance.operations.pickers + 1)) + ["Tất cả"]
    if st.session_state.get("route_picker") not in picker_options:
        st.session_state["route_picker"] = result["batches"][0]["picker"]
    picker = st.selectbox("Nhân viên", picker_options, key="route_picker",
                          format_func=lambda x: x if x == "Tất cả" else f"Nhân viên {x}")
    batches = [b for b in result["batches"] if picker == "Tất cả" or b["picker"] == picker]
    if batches:
        options = [b["id"] for b in batches] + ["Tất cả"]
        if st.session_state.get("route_batch") not in options:
            st.session_state["route_batch"] = options[0]
        batch = st.selectbox("Chuyến lấy hàng", options, key="route_batch")
        figure(warehouse_figure(instance, result, None if picker == "Tất cả" else picker,
                                None if batch == "Tất cả" else batch))
        st.caption("Ô vuông là điểm xuất phát. Số trên tuyến là thứ tự lấy hàng của chuyến đang chọn.")
        if batch != "Tất cả":
            chosen = next(b for b in batches if b["id"] == batch)
            with st.expander("Thứ tự điểm lấy hàng", expanded=False):
                stops = chosen["stops"][1:-1]
                st.dataframe(pd.DataFrame({"Thứ tự": range(1, len(stops) + 1), "Vị trí": stops}),
                             hide_index=True, width="stretch")
                st.caption("Bảng giúp đọc thứ tự trên màn hình nhỏ. Chuyến bắt đầu và kết thúc tại depot.")
    else:
        st.info("Nhân viên này không có chuyến được phân công.")
    st.subheader("Lịch làm việc")
    figure(gantt_figure(instance, result))
    st.caption("Màu nhân viên nhất quán với bản đồ. Viền đỏ đánh dấu chuyến có đơn trễ.")


def research_view(instance, results, result):
    with st.expander("Phân tích thuật toán", expanded=False):
        st.write(f"**Điểm tổng hợp F: {result['metrics']['objective']:.4f}** · Thấp hơn là tốt hơn trên cùng dữ liệu và trọng số.")
        columns = {"method": "Thuật toán", "objective": "Điểm F", "distance": f"Quãng đường ({unit_label(instance, 'distance')})",
                   "makespan": f"Hoàn tất ({unit_label(instance, 'time')})",
                   "tardiness": f"Tổng độ trễ ({unit_label(instance, 'time')})", "late_orders": "Đơn trễ",
                   "seconds": "Thời gian chạy (giây)"}
        rows = [{"method": m, **{k: r["metrics"][k] for k in columns if k not in ("method", "seconds")},
                 "seconds": r["timing"]["total_seconds"]} for m, r in results.items()]
        st.dataframe(pd.DataFrame(rows).rename(columns=columns), hide_index=True, width="stretch")
        fig, ax = plt.subplots(figsize=(8, 3), layout="constrained")
        for method, data in results.items():
            trace = data.get("search", {}).get("trace", [])
            if trace:
                ax.step([p["seconds"] for p in trace], [p["objective"] for p in trace], where="post", label=method)
        if ax.lines:
            ax.set(xlabel="Thời gian tối ưu, gồm khởi tạo (giây)", ylabel="Điểm F tốt nhất")
            ax.legend(frameon=False)
            ax.grid(alpha=.15)
            figure(fig)
        else:
            plt.close(fig)
        st.caption("F cân bằng quãng đường, thời gian hoàn tất và độ trễ; không bảo đảm mọi chỉ số đều giảm.")
        st.json(result.get("search", {}), expanded=False)


def results_view(snapshot):
    instance = Instance.from_dict(snapshot["instance"])
    results = snapshot["results"]
    st.caption(f"Lần chạy: {instance.name} · Seed {snapshot.get('seed', 'không lưu')} · "
               f"{'Bản lưu' if snapshot.get('saved_playback') else 'Kết quả trực tiếp'}")
    instance_summary(instance)
    names = list(results)
    if st.session_state.get("result_method") not in names:
        st.session_state["result_method"] = "ALNS" if "ALNS" in names else names[0]
    selected = st.selectbox("Phương án đang xem", names, key="result_method")
    result = results[selected]
    with st.expander("Tải kết quả", expanded=False):
        for label, data, filename in [
            ("Tải nghiệm JSON", result, f"{selected}-solution.json"),
            ("Tải dữ liệu đầu vào", instance.to_dict(), "warehouse-instance.json"),
            ("Tải toàn bộ lần chạy", snapshot, "warehouse-snapshot.json"),
        ]:
            st.download_button(label, json.dumps(data, ensure_ascii=False, indent=2),
                               file_name=filename, mime="application/json", key=filename)
    native = instance.metadata.get("units", {}).get("time") == "source_time_unit"
    time_unit, distance_unit = unit_label(instance, "time"), unit_label(instance, "distance")
    metrics, baseline = result["metrics"], results["B0"]["metrics"]
    for col, label, field, unit in zip(st.columns(3),
            ["Đơn trễ", "Thời gian hoàn tất", "Quãng đường"],
            ["late_orders", "makespan", "distance"], ["đơn", time_unit, distance_unit]):
        value = str(metrics[field]) if field == "late_orders" else f"{metrics[field]:,.1f}"
        col.metric(label, f"{value} {unit}")
    overview, routes, details = st.tabs(["Tổng quan", "Tuyến & lịch", "Chi tiết"])
    with overview:
        st.subheader("Kết quả của phương án")
        st.write(f"Đã phân công **{metrics['batches']} chuyến** cho **{metrics['used_pickers']} nhân viên**. "
                 f"**{len(instance.orders) - metrics['late_orders']}/{len(instance.orders)} đơn** hoàn thành đúng hạn.")
        pct = improvement(metrics["distance"], baseline["distance"])
        if selected != "B0":
            if pct is None:
                st.write("Quãng đường B0 bằng 0, không tính phần trăm thay đổi.")
            else:
                direction = "giảm" if pct >= 0 else "tăng"
                st.write(f"Quãng đường {direction} **{abs(pct):.1f}%** so với phương án cơ sở B0.")
        st.caption("Hạn mềm: phương án hợp lệ vẫn có thể có đơn trễ. Kết quả đã được kiểm tra tải, tuyến và lịch.")
        if native:
            st.caption("Kris giữ nguyên đơn vị nguồn, không đối chiếu trực tiếp với bài toán hạn cứng của tác giả.")
        research_view(instance, results, result)
    with routes:
        route_view(instance, result)
    with details:
        late_only = st.checkbox("Chỉ xem đơn trễ", key="late_only")
        rows = [r for r in result["orders"] if not late_only or r["tardiness"] > 1e-9]
        st.subheader("Đơn hàng")
        st.dataframe(pd.DataFrame(rows, columns=["id", "batch", "picker", "due", "completion", "tardiness"]).rename(columns={
            "id": "Đơn", "batch": "Chuyến", "picker": "Nhân viên", "due": f"Hạn ({time_unit})",
            "completion": f"Hoàn tất ({time_unit})", "tardiness": f"Trễ ({time_unit})"}), hide_index=True, width="stretch")
        st.subheader("Chuyến lấy hàng")
        cols = {"id": "Chuyến", "picker": "Nhân viên", "orders": "Các đơn", "load": "Tải",
                "distance": f"Quãng đường ({distance_unit})", "start": f"Bắt đầu ({time_unit})", "end": f"Kết thúc ({time_unit})"}
        st.dataframe(pd.DataFrame([{k: b[k] for k in cols} for b in result["batches"]]).rename(columns=cols),
                     hide_index=True, width="stretch")

