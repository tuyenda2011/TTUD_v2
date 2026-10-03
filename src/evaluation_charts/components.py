"""Paired objective-component improvement figures."""
from __future__ import annotations

import statistics

from .common import GROUP_LABELS, METRIC_LABELS, METHOD_STYLES, _clean_axis, _figure, _method_order, _spec


def build_figures(group: dict, rows: list[dict], reference: str, style: str) -> list[dict]:
    methods = _method_order(row["method"] for row in rows if row["method"] != reference)
    metrics = list(METRIC_LABELS)
    if not methods or not any(row.get(f"{metric}_improvement_pct") is not None for row in rows if row["method"] != reference for metric in metrics):
        return [_spec(group, "components", reason=f"Thiếu cặp thành phần mục tiêu với {reference}; thành phần tham chiếu bằng 0 là N/A.")]

    def build(selected: list[str], suffix: str = "") -> dict:
        fig = _figure(11.5 if len(selected) > 1 else 8.5, max(3.8, 1.8 + len(methods) * .47), style)
        axes = fig.subplots(1, len(selected), squeeze=False)[0]
        for axis, metric in zip(axes, selected):
            for index, method in enumerate(methods):
                values = [row[f"{metric}_improvement_pct"] for row in rows
                          if row["method"] == method and row.get(f"{metric}_improvement_pct") is not None]
                color, marker, _ = METHOD_STYLES[method]
                if values:
                    axis.scatter(values, [index] * len(values), s=18, color=color, alpha=.35, zorder=2)
                    mean = statistics.mean(values)
                    axis.errorbar([mean], [index], xerr=[[mean - min(values)], [max(values) - mean]],
                                  fmt=marker, color=color, markersize=7, linewidth=1.2, capsize=3, zorder=3)
                    axis.annotate(f"n={len(values)}", (1, index), xycoords=("axes fraction", "data"),
                                  xytext=(-3, 8), textcoords="offset points", ha="right",
                                  fontsize=14 if style == "presentation" else 8, color="#64748b")
                else:
                    axis.text(.5, index, "N/A", transform=axis.get_yaxis_transform(),
                              color="#64748b", ha="center", va="center", fontsize=17 if style == "presentation" else 9)
            axis.set_yticks(range(len(methods)), methods)
            axis.set_ylim(len(methods) - .5, -.5)
            axis.axvline(0, color="#64748b", linewidth=1)
            axis.set_title(METRIC_LABELS[metric])
            axis.set_xlabel(f"Cải thiện so với {reference} (%)")
            _clean_axis(axis)
        fig.suptitle(f"Các thành phần mục tiêu · {GROUP_LABELS.get(group['name'], group['name'])}", weight="bold")
        caption = (f"Tính phần trăm cải thiện so với {reference} từ trung bình seed trong từng instance rồi mới lấy trung bình qua instance. "
                   "Chấm mờ = giá trị từng instance; ký hiệu đậm = trung bình; thanh ngang = min–max giữa instance, không phải khoảng tin cậy. "
                   "Mẫu số tham chiếu bằng 0 bị loại khỏi tỷ lệ (N/A), n ghi số cặp hợp lệ cho từng thành phần. Không gộp giá trị vật lý khác đơn vị.")
        spec = _spec(group, "components", caption, fig, suffix=suffix)
        spec["title"] += f" · {METRIC_LABELS[selected[0]]}"
        return spec

    return [build([metric], f"_{metric}") for metric in metrics]
