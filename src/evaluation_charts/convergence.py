"""Observed convergence figures from audited benchmark runs."""
from __future__ import annotations

from bisect import bisect_right
import math
import statistics

from ..benchmark import STOCHASTIC
from .common import (
    GROUP_LABELS,
    METHOD_STYLES,
    _clean_axis,
    _eligible_seed_runs,
    _figure,
    _instance_labels,
    _label_caption,
    _method_order,
    _spec,
    representative_instances,
)


def _observed_trace(run: dict) -> tuple[list[float], list[float]] | None:
    points = run["search"].get("trace", [])
    times, values = [], []
    for point in points:
        seconds, objective = point.get("seconds"), point.get("objective")
        if (isinstance(seconds, bool) or isinstance(objective, bool)
                or not isinstance(seconds, (int, float)) or not isinstance(objective, (int, float))
                or not math.isfinite(seconds) or not math.isfinite(objective) or seconds < 0
                or (times and seconds < times[-1])):
            return None
        best = min(values[-1], objective) if values else objective
        if times and seconds == times[-1]:
            values[-1] = best
        else:
            times.append(seconds)
            values.append(best)
    return (times, values) if len(times) >= 2 else None


def build_figures(group: dict, runs: dict, style: str) -> list[dict]:
    selected = representative_instances(group)
    labels = _instance_labels(group)
    single_run = group["name"] == "current_run"
    panels, exclusions = [], []
    for name in selected:
        eligible, excluded = _eligible_seed_runs(runs[name], trace=True, single_run=single_run)
        traces = {}
        for method, method_runs in eligible.items():
            observed = [_observed_trace(run) for run in method_runs]
            if any(trace is None for trace in observed):
                excluded.append(f"{method}: trace thiếu hoặc thời gian không hợp lệ")
            else:
                traces[method] = observed
        all_traces = [trace for method in traces.values() for trace in method]
        if all_traces:
            start, end = max(trace[0][0] for trace in all_traces), min(trace[0][-1] for trace in all_traces)
            if start < end:
                panels.append((name, traces, start, end))
            else:
                excluded.append("không có khoảng thời gian quan sát chung giữa các seed/method")
        exclusions.extend(f"{name} / {entry}" for entry in excluded)
    if not panels:
        reason = ("Lần chạy hiện tại cần trace có ít nhất 2 mốc thời gian khác nhau và khoảng quan sát dương; không suy diễn trace hoặc mốc kết thúc."
                  if single_run else "Cần ít nhất 2 search seed có trace hợp lệ và khoảng thời gian quan sát chung dương; không suy diễn trace hoặc mốc kết thúc.")
        return [_spec(group, "convergence", reason=reason + (" " + "; ".join(exclusions) if exclusions else ""))]
    intervals = [f"{name}: [{start:.6g}, {end:.6g}] giây" for name, _, start, end in panels]
    statistic = ("Một search seed: đường bậc thang là F best-so-far của lần chạy hiện tại; không có vùng phân tán, không đánh giá độ ổn định. "
                 if single_run else "Đường bậc thang = trung bình F best-so-far qua seed; vùng mờ = min–max seed, không phải khoảng tin cậy. ")
    caption = (statistic +
               "Đường ngang là nghiệm heuristic cuối cùng, không mô tả thời gian heuristic hoàn tất. "
               "Chỉ dùng giao khoảng thời gian thực đã quan sát của mọi seed/method được vẽ trên cùng instance; "
               "giữ giá trị quan sát trước theo bậc thang, không ngoại suy trước khởi tạo hoặc sau điểm trace cuối, không thêm mốc kết thúc chưa ghi. "
               f"Ví dụ cố định theo số đơn/tên trước khi xem kết quả: {', '.join(selected)}. "
               "Khoảng chung: " + "; ".join(intervals) + ". " + ("Không đủ dữ liệu: " + "; ".join(exclusions) if exclusions else ""))
    specs = []
    panel_sets = [[panel] for panel in panels]
    for subset in panel_sets:
        fig = _figure(11.8 if len(subset) > 1 else 8.5, 4.3, style)
        axes = fig.subplots(1, len(subset), squeeze=False)[0]
        for axis, (name, traces, start, end) in zip(axes, subset):
            grid = sorted({start, end, *(t for method in traces.values() for times, _ in method for t in times if start <= t <= end)})
            for method, method_traces in traces.items():
                series = [[values[bisect_right(times, seconds) - 1] for seconds in grid] for times, values in method_traces]
                means = [statistics.mean(values) for values in zip(*series)]
                lower = [min(values) for values in zip(*series)]
                upper = [max(values) for values in zip(*series)]
                color, marker, line = METHOD_STYLES[method]
                axis.step(grid, means, where="post", color=color, linestyle=line, marker=marker,
                          markevery=max(1, len(grid) // 5), markersize=5 if style == "presentation" else 4,
                          linewidth=1.6, label=f"{method} ({len(series)} seed)")
                if len(series) > 1:
                    axis.fill_between(grid, lower, upper, step="post", color=color, alpha=.12, linewidth=0)
            for method in _method_order(m for m in runs[name] if m not in STOCHASTIC):
                color, _, line = METHOD_STYLES[method]
                axis.axhline(statistics.mean(r["metrics"]["objective"] for r in runs[name][method]),
                             color=color, linestyle=line, linewidth=1, label=f"{method} · heuristic")
            axis.set_xlim(start, end)
            axis.set_title(labels[name], fontsize=18 if style == "presentation" else 12,
                           pad=45 if style == "presentation" else 30)
            axis.set_xlabel("Thời gian tối ưu gồm khởi tạo (giây)")
            axis.set_ylabel("F tốt nhất đến thời điểm đó")
            _clean_axis(axis, "y")
            axis.legend(loc="lower center", bbox_to_anchor=(.5, 1.02), ncols=min(5, len(axis.lines)),
                        frameon=False, fontsize=14 if style == "presentation" else 9)
        fig.suptitle(f"Hội tụ theo thời gian thực · {GROUP_LABELS.get(group['name'], group['name'])}", weight="bold")
        suffix = "" if style == "report" and group["name"] == "current_run" else f"_example{selected.index(subset[0][0]) + 1}"
        spec = _spec(group, "convergence", caption + _label_caption(labels, [subset[0][0]]), fig, suffix=suffix)
        spec["title"] += f" · {labels[subset[0][0]]}"
        specs.append(spec)
    return specs
