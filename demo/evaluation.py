"""Read-only assessment views backed by the portable evaluation API."""
from itertools import islice
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.evaluation import evaluation_tables, load_evaluation, snapshot_evaluation
from src.evaluation_figures import GROUP_LABELS, MAP_LABELS, figure_bytes, figure_specs
from demo.evaluation_text import localize_spec


VIEW_ERRORS = (ValueError, OSError, KeyError, TypeError)
SIMULATION = "Mô phỏng"
BENCHMARK = "Đánh giá benchmark"


def discover_evaluations(root, limit=40):
    """Inspect a bounded number of immediate results directories, never JSON paths."""
    workspace = Path(root).resolve()
    results = (workspace / "results").resolve()
    if not results.is_relative_to(workspace) or not results.is_dir():
        return []
    found = []
    for directory in islice(results.iterdir(), limit):
        try:
            candidate = (directory / "report" / "evaluation.json").resolve()
            if candidate.is_relative_to(results) and candidate.is_file():
                found.append(candidate)
        except OSError:
            continue
    return sorted(found)


@st.cache_data(show_spinner=False, max_entries=16)
def validated_content(content):
    """Cache the audit by actual bytes, including for local report files."""
    return load_evaluation(content)


@st.cache_data(show_spinner=False, max_entries=8)
def current_evaluation(snapshot):
    return snapshot_evaluation(snapshot)


def references_for(group):
    methods = {result["method"] for result in group["results"]}
    preferred = ["B2", "B0", "B3", "LNS", "ALNS", "VNS"]
    return [method for method in preferred if method in methods] + sorted(methods - set(preferred))


@st.cache_data(show_spinner=False, max_entries=16)
def chart_assets(payload, reference, group, style="report"):
    """Share report figures and encode them once for display and downloads."""
    assets = []
    specs = figure_specs(payload, reference=reference, group=group, style=style)
    try:
        for spec in specs:
            spec = localize_spec(spec, reference)
            asset = {key: spec.get(key) for key in ("id", "title", "caption", "reason", "technical_caption")}
            fig = spec.get("figure")
            asset["png"] = figure_bytes(fig, format="png") if fig is not None else None
            assets.append(asset)
    finally:
        for spec in specs:
            if spec.get("figure") is not None:
                plt.close(spec["figure"])
    return assets


def summary_frame(rows):
    labels = {"method": "Thuật toán", "reference": "Đối chứng", "instances": "Số bài toán",
              "win": "Thắng", "tie": "Hòa", "loss": "Thua", "mean_improvement_pct": "Cải thiện F (%)"}
    return pd.DataFrame([{labels[key]: row[key] for key in labels} for row in rows])


def instance_frame(rows, current=False, instances=()):
    if current:
        if not rows:
            return pd.DataFrame()
        labels = {"method": "Thuật toán", "objective_mean": "F",
                  "distance_mean": f"Quãng đường ({rows[0]['distance_unit']})",
                  "makespan_mean": f"Thời gian hoàn tất ({rows[0]['time_unit']})",
                  "tardiness_mean": f"Tổng độ trễ ({rows[0]['time_unit']})",
                  "late_orders_mean": "Đơn trễ", "total_seconds_mean": "Thời gian chạy (s)",
                  "objective_improvement_pct": "Cải thiện F (%)"}
        return pd.DataFrame([{labels[key]: row[key] for key in labels} for row in rows])
    map_names = {}
    for instance in instances:
        scenario = instance.get("metadata", {}).get("scenario", {})
        scenario_id = scenario.get("id") if isinstance(scenario, dict) else None
        if isinstance(scenario_id, str) and scenario_id in MAP_LABELS:
            map_names[instance["name"]] = MAP_LABELS[scenario_id]
    name_column = "Bản đồ" if map_names else "Bài toán"
    show_seed = any(row["instance_seed"] is not None for row in rows)
    return pd.DataFrame([{
        name_column: map_names.get(row["instance"], row["instance"]), "Số đơn": row["n"],
        **({"Seed dữ liệu": row["instance_seed"]} if show_seed else {}),
        "Thuật toán": row["method"], "Số lần chạy": row["runs"],
        "F trung bình ± độ lệch chuẩn": f"{row['objective_mean']:.4f} ± {row['objective_std']:.4f}",
        "Quãng đường": f"{row['distance_mean']:.3f} {row['distance_unit']}",
        "Thời gian hoàn tất": f"{row['makespan_mean']:.3f} {row['time_unit']}",
        "Tổng độ trễ": f"{row['tardiness_mean']:.3f} {row['time_unit']}",
        "Đơn trễ trung bình": row["late_orders_mean"],
        "Thời gian chạy (s)": row["total_seconds_mean"],
        "Cải thiện F (%)": row["objective_improvement_pct"],
    } for row in rows])


def table_view(rows, name, key, display=None):
    frame = pd.DataFrame(rows)
    if frame.empty:
        st.info("Chưa có kết quả để so sánh với đối chứng đã chọn trong nhóm này.")
        return
    st.dataframe(frame if display is None else display, hide_index=True, width="stretch")
    st.download_button(
        f"Tải bảng {name} (CSV)", frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{key}.csv", mime="text/csv", key=f"download_{key}",
    )


def chart_view(asset, key):
    if asset["png"] is None:
        st.info(asset["reason"] or "Chưa đủ dữ liệu để vẽ biểu đồ này.")
    else:
        st.image(asset["png"], width="stretch")
        st.download_button(
            "Tải hình PNG", asset["png"], file_name=f"{asset['id']}.png",
            mime="image/png", key=f"{key}_{asset['id']}_png",
        )
    if asset.get("caption") or asset.get("technical_caption"):
        with st.expander("Cách tính và phạm vi dữ liệu", expanded=False):
            if asset.get("caption"):
                st.caption(asset["caption"])
            if asset.get("technical_caption"):
                st.caption(asset["technical_caption"])


def figure_label(asset):
    for suffix, label in (("_distance", "Quãng đường"), ("_makespan", "Thời gian hoàn tất"), ("_tardiness", "Tổng độ trễ")):
        if asset["id"].endswith(suffix):
            return asset["title"] if asset["title"].endswith(f" · {label}") else f"{asset['title']} · {label}"
    page = asset["id"].rsplit("_p", 1)
    if len(page) == 2 and page[1].isdigit():
        suffix = f" · Trang {page[1]}"
        return asset["title"] if asset["title"].casefold().endswith(suffix.casefold()) else f"{asset['title']}{suffix}"
    return asset["title"]


def error_details(error):
    with st.expander("Chi tiết lỗi", expanded=False):
        st.text(str(error))


def benchmark_workspace(root):
    st.title("Đánh giá benchmark")
    with st.sidebar:
        st.header("Mở kết quả đánh giá")
        upload = st.file_uploader(
            "Tải tệp evaluation.json", type=["json"], key="evaluation_upload",
            help="Tệp kết quả đầy đủ của đợt thực nghiệm, gồm dữ liệu đầu vào và các phương án đã tính.",
        )
        try:
            local_paths = discover_evaluations(root)
        except VIEW_ERRORS as exc:
            local_paths = []
            st.caption("Không đọc được danh sách báo cáo trên máy. Bạn vẫn có thể tải tệp evaluation.json lên.")
            error_details(exc)
        choices = {path.relative_to(Path(root).resolve()).as_posix(): path for path in local_paths}
        placeholder = "Chọn báo cáo trên máy"
        options = [placeholder, *choices]
        if st.session_state.get("evaluation_local") not in options:
            st.session_state["evaluation_local"] = placeholder
        local_choice = st.selectbox("Báo cáo trên máy", options, key="evaluation_local",
                                    help="Nếu có tệp tải lên, ứng dụng ưu tiên dùng tệp đó.")

    try:
        if upload is not None:
            content, label = upload.getvalue(), upload.name
        elif local_choice in choices:
            path = choices[local_choice]
            content, label = path.read_bytes(), local_choice
        else:
            st.info("Tải tệp evaluation.json hoặc chọn báo cáo đã lưu để bắt đầu. Không cần chạy mô phỏng trước.")
            return
        payload = validated_content(content)
        mode = {"quick": "Quick — chạy thử", "report": "Report — thực nghiệm đầy đủ",
                "live": "Lần chạy hiện tại"}.get(payload["preset"], payload["preset"])
        st.caption(f"{label} · {mode}")
        if payload["preset"] == "quick":
            st.warning("Chế độ Quick: chạy thử, chưa đủ để kết luận về các thuật toán.")
        groups = {group["name"]: group for group in payload["groups"]}
        if st.session_state.get("evaluation_group") not in groups:
            st.session_state["evaluation_group"] = next(iter(groups))
        group_column, reference_column = st.columns(2)
        chosen = group_column.selectbox("Nhóm dữ liệu", list(groups), key="evaluation_group",
                                        format_func=lambda name: GROUP_LABELS.get(name, name))
        references = references_for(groups[chosen])
        if st.session_state.get("evaluation_reference") not in references:
            st.session_state["evaluation_reference"] = references[0]
        reference = reference_column.selectbox("Thuật toán đối chứng", references, key="evaluation_reference")
        config = groups[chosen]["config"]
        search = groups[chosen]["results"][0]["search"]["config"]
        weights = config.get("weights", [1/3, 1/3, 1/3])
        time_limit = f"{search['seconds']:g} giây" if search["seconds"] else "không giới hạn thời gian"
        selected_payload = {**payload, "groups": [groups[chosen]]}
        tables = evaluation_tables(selected_payload, reference=reference)
        summary, instances, charts = st.tabs(["Tổng hợp", "Từng bài toán", "Biểu đồ"])
        with summary:
            table_view(tables["summary"], "tổng hợp", "benchmark_summary", summary_frame(tables["summary"]))
        with instances:
            table_view(tables["per_instance"], "từng bài toán", "benchmark_per_instance",
                       instance_frame(tables["per_instance"], instances=groups[chosen]["instances"]))
            with st.expander("Bảng đầy đủ và kết quả từng lần chạy", expanded=False):
                st.dataframe(pd.DataFrame(tables["per_instance"]), hide_index=True, width="stretch")
                table_view(tables["raw_metrics"], "từng lần chạy", "benchmark_raw_metrics")
        with charts:
            style_column, figure_column = st.columns([1, 3])
            use = style_column.selectbox("Dùng cho", ["Báo cáo", "Slide"], key="evaluation_style")
            assets = chart_assets(selected_payload, reference, chosen, "report" if use == "Báo cáo" else "presentation")
            by_id = {asset["id"]: asset for asset in assets}
            if by_id:
                if st.session_state.get("evaluation_figure") not in by_id:
                    st.session_state["evaluation_figure"] = next(iter(by_id))
                figure_id = figure_column.selectbox(
                    "Chọn biểu đồ", list(by_id), format_func=lambda value: figure_label(by_id[value]),
                    key="evaluation_figure",
                )
                chart_view(by_id[figure_id], "benchmark")
            else:
                st.info("Chưa có biểu đồ cho nhóm dữ liệu này.")
        with st.expander("Thiết lập và cách tính", expanded=False):
            st.caption(f"{len(config.get('search_seeds', [7]))} seed khác nhau · "
                       f"Giới hạn tìm kiếm: {time_limit}, tối đa {search['iterations']} vòng.")
            st.caption(f"Trọng số cho quãng đường / thời gian hoàn tất / tổng độ trễ: "
                       f"{weights[0]:.3f} / {weights[1]:.3f} / {weights[2]:.3f}.")
            st.caption("Với mỗi bài toán, lấy trung bình các lần chạy trước khi so sánh. Mỗi bài toán có trọng số như nhau. Seed xác định yếu tố ngẫu nhiên của lần chạy; độ lệch chuẩn cho biết mức dao động giữa các lần chạy, không phải khoảng tin cậy. Các nhóm giữ nguyên đơn vị của dữ liệu.")
    except VIEW_ERRORS as exc:
        if isinstance(exc, OSError):
            st.error("Không đọc được tệp đã chọn. Hãy kiểm tra tệp còn trên máy và ứng dụng có quyền đọc tệp.")
        else:
            st.error("Tệp đánh giá không hợp lệ. Hãy dùng evaluation.json được xuất từ đợt thực nghiệm hoặc báo cáo.")
        error_details(exc)


def current_run_view(snapshot, selected):
    """Assess raw solver evidence before any display-only Kris conversion."""
    st.caption(f"Phương án đang xem: {selected} · Chỉ số giữ đơn vị gốc của dữ liệu, kể cả Kris.")
    st.warning("Một bài toán, một seed: chỉ phản ánh lần chạy này.")
    try:
        payload = current_evaluation(snapshot)
        group = payload["groups"][0]
        references = [method for method in ("B2", "B0") if method in references_for(group)]
        if st.session_state.get("objective_reference") not in references:
            st.session_state["objective_reference"] = references[0]
        reference = st.selectbox("Thuật toán đối chứng", references, key="objective_reference")
        tables = evaluation_tables(payload, reference=reference)
        result = snapshot["results"][selected]
        weights = result["objective_config"]["weights"]
        st.write(f"**Điểm F của {selected}: {result['metrics']['objective']:.4f}** · Đối chứng: {reference}")
        selected_row = next(row for row in tables["per_instance"] if row["method"] == selected)
        changes = []
        for metric, label in (("objective", "F"), ("distance", "quãng đường")):
            change = selected_row[f"{metric}_improvement_pct"]
            if change is None:
                changes.append(f"không tính tỷ lệ thay đổi của {label} vì giá trị đối chứng bằng 0")
            elif abs(change) < 1e-9:
                changes.append(f"{label} không đổi")
            else:
                changes.append(f"{label} {'giảm' if change > 0 else 'tăng'} {abs(change):.2f}%")
        late = selected_row["late_orders_difference"]
        changes.append("số đơn trễ không đổi" if abs(late) < 1e-9 else
                       f"số đơn trễ {'tăng' if late > 0 else 'giảm'} {abs(late):g} đơn")
        st.write(f"So với {reference}: {'; '.join(changes)}.")
        table_view(tables["per_instance"], "đánh giá lần chạy", "current_run_per_instance",
                   instance_frame(tables["per_instance"], current=True))
        with st.expander("Chỉ số đầy đủ của lần chạy", expanded=False):
            st.caption(f"Trọng số cho quãng đường / thời gian hoàn tất / tổng độ trễ: {weights[0]:.3f} / {weights[1]:.3f} / {weights[2]:.3f}. F thấp hơn chưa chắc mọi chỉ số đều tốt hơn.")
            st.dataframe(pd.DataFrame(tables["per_instance"]), hide_index=True, width="stretch")
        convergence = [asset for asset in chart_assets(payload, reference, group["name"])
                       if "__convergence" in asset["id"]]
        for asset in convergence:
            chart_view(asset, "current_run")
    except VIEW_ERRORS as exc:
        st.error("Không thể đọc kết quả của lần chạy này để đánh giá. Hãy mở lại kết quả đã lưu hoặc chạy lại.")
        error_details(exc)
