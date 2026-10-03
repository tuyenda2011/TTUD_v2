"""Controlled scalability figures using audited per-instance statistics."""
from __future__ import annotations

import json
import statistics

from .common import GROUP_LABELS, METHOD_STYLES, _clean_axis, _figure, _method_order, _spec


def _controlled_layout(group: dict) -> tuple[bool, str]:
    instances = group["instances"]
    if len({len(i["orders"]) for i in instances}) < 2:
        return False, "Cần ít nhất 2 quy mô đơn hàng trong cùng nhóm dữ liệu."
    controls = []
    for instance in instances:
        metadata = instance.get("metadata", {})
        controls.append(json.dumps({key: instance.get(key) for key in ("depot", "nodes", "edges", "products", "operations", "directed")}
                                   | {"layout": metadata.get("layout"), "units": metadata.get("units")},
                                   sort_keys=True, allow_nan=False))
    if len(set(controls)) != 1:
        return False, "Layout, SKU, đơn vị hoặc cấu hình picker khác nhau; đây là so sánh kịch bản, không phải bằng chứng scalability có kiểm soát."
    config = group.get("config", {})
    designated = (config.get("evaluation_role") == "scalability" or config.get("purpose") == "scalability"
                  or config.get("scalability") is True or group["name"].casefold() == "scalability")
    if not designated and not all(i.get("metadata", {}).get("layout") for i in instances):
        return False, "Nhóm chưa được chỉ định scalability và thiếu metadata layout có kiểm soát để xác nhận."
    return True, ""


def build_figures(group: dict, rows: list[dict], reference: str, style: str) -> list[dict]:
    valid, reason = _controlled_layout(group)
    if not valid:
        return [_spec(group, "scalability", reason=reason)]
    methods = _method_order(row["method"] for row in rows)
    sizes = sorted({row["n"] for row in rows})
    caption = ("Giữ nguyên layout, SKU, đơn vị và operations/picker giữa các quy mô. Seed được lấy trung bình trong instance trước; "
               "điểm = trung bình qua instance cùng n, râu = min–max giữa instance, không phải khoảng tin cậy. "
               "Thời gian tổng gồm tiền xử lý, khởi tạo, search và xác thực; tỷ lệ F dùng cặp cùng instance. "
               "Instance seed lặp giữa các n có tương quan; đường nối chỉ mô tả các quy mô đã đo, không chứng minh luật độ phức tạp.")
    specs = []
    metrics = ["total_seconds_mean", "objective_improvement_pct"]
    metric_sets = [[metric] for metric in metrics]
    for subset in metric_sets:
        fig = _figure(10.8, 4.2, style)
        axes = fig.subplots(1, len(subset), squeeze=False)[0]
        for axis, metric in zip(axes, subset):
            for method in methods:
                if metric == "objective_improvement_pct" and method == reference:
                    continue
                means, low, high, x = [], [], [], []
                for n in sizes:
                    values = [row[metric] for row in rows if row["method"] == method and row["n"] == n and row.get(metric) is not None]
                    if values:
                        avg = statistics.mean(values)
                        x.append(n); means.append(avg); low.append(avg - min(values)); high.append(max(values) - avg)
                if x:
                    color, marker, line = METHOD_STYLES[method]
                    axis.errorbar(x, means, yerr=[low, high], color=color, marker=marker,
                                  linestyle=line, linewidth=1.4, markersize=5, capsize=3, label=method)
            axis.set_xlabel("Số đơn hàng (n)")
            axis.set_xticks(sizes)
            _clean_axis(axis, "y")
            axis.legend(frameon=False, fontsize=14 if style == "presentation" else 8)
            if metric == "total_seconds_mean":
                axis.set_ylabel("Thời gian tổng trung bình (giây)")
            else:
                axis.set_ylabel(f"Cải thiện F so với {reference} (%)")
                axis.axhline(0, color="#64748b", linewidth=1)
        fig.suptitle(f"Thay đổi theo quy mô đơn hàng · {GROUP_LABELS.get(group['name'], group['name'])}", weight="bold")
        suffix = "_runtime" if subset[0] == "total_seconds_mean" else "_quality"
        spec = _spec(group, "scalability", caption, fig, suffix=suffix)
        spec["title"] += " · " + ("Thời gian tổng" if suffix == "_runtime" else "Chất lượng F")
        axes[0].set_title("Thời gian tổng" if suffix == "_runtime" else "Chất lượng F")
        specs.append(spec)
    return specs
