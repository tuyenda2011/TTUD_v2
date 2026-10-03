"""Validate one benchmark folder and export report-ready tables and charts.

The benchmark runner is the source of truth for raw solutions.  This command
re-audits those solutions, checks that CSV/summary/comparison files can be
reconstructed from the raw data, and writes flat CSV files that can be loaded
directly into a report or spreadsheet.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import shutil
import statistics
import sys
import textwrap
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.comparison import paired_comparisons
from src.models import InputError, read_instance
from src.solver import fingerprint
from src.search import SearchConfig
from src.validator import validate_solution

from src.benchmark_archive import METRICS, _assert_same, verify_benchmark


def _write_csv(path: Path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _flat_summaries(summaries):
    fields = ["instance", "method", "runs", "feasible_rate"]
    for metric in METRICS:
        fields.extend(f"{metric}_{key}" for key in ("mean", "median", "std", "best", "difference_vs_B0", "improvement_pct_vs_B0"))
    fields.extend(("zero_iteration_runs", "iterations_min", "iterations_median", "adapted_runs", "initialization_mean_seconds", "search_mean_seconds"))
    rows = []
    for summary in summaries:
        row = {key: summary[key] for key in fields[:4]}
        for metric in METRICS:
            row.update({f"{metric}_{key}": summary[metric][key] for key in ("mean", "median", "std", "best", "difference_vs_B0", "improvement_pct_vs_B0")})
        row.update(summary["search_diagnostics"])
        rows.append(row)
    return rows, fields


def _flat_comparisons(comparisons):
    fields = ["method", "reference", "instances", "win", "tie", "loss", "percentage_instances", "mean_improvement_pct"]
    return [{key: row.get(key) for key in fields} for row in comparisons], fields


def _comparison_pairs(comparisons):
    fields = ["method", "reference", "instance", "difference", "improvement_pct", "outcome"]
    rows = []
    for comparison in comparisons:
        for pair in comparison["pairs"]:
            rows.append({"method": comparison["method"], "reference": comparison["reference"], **pair})
    return rows, fields


def _make_charts(summaries, comparisons, output: Path, results=None, instance_labels=None):
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise InputError("Biểu đồ báo cáo cần matplotlib: pip install matplotlib; hoặc dùng --no-charts để chỉ xuất bảng.") from exc
    charts = output / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    instances = sorted({row["instance"] for row in summaries})
    methods = sorted({row["method"] for row in summaries})
    by = {(row["instance"], row["method"]): row for row in summaries}
    paths = []
    colors = {"B0": "#d97706", "B2": "#15803d", "LNS": "#dc2626", "ALNS": "#2563eb", "VNS": "#7c3aed"}

    def save(fig, stem):
        fig.tight_layout()
        for extension in ("png", "pdf"):
            path = charts / f"{stem}.{extension}"
            fig.savefig(path, dpi=300, facecolor="white")
            paths.append(path.relative_to(output).as_posix())
        plt.close(fig)

    # Keep a fixed printed size; paginate instead of shrinking hundreds of labels.
    labels = instance_labels or {}
    low = min(row["objective"]["mean"] for row in summaries)
    high = max(row["objective"]["mean"] for row in summaries)
    margin = max((high - low) * .12, .01)
    for start in range(0, len(instances), 5):
        page = instances[start:start + 5]
        fig, axis = plt.subplots(figsize=(7.2, 4.8))
        for method in methods:
            values = [by[(name, method)]["objective"]["mean"] if (name, method) in by else math.nan for name in page]
            axis.plot(range(len(page)), values, marker="o", markersize=5,
                      color=colors.get(method), label=method, linewidth=1.5)
        axis.set_xticks(range(len(page)), [labels.get(name, textwrap.fill(name, 19)) for name in page], fontsize=9)
        axis.set_ylim(low - margin, high + margin)
        axis.set_title("Giá trị F trung bình theo bài toán", fontsize=13, pad=38)
        axis.set_ylabel("F (càng thấp càng tốt)", fontsize=10)
        axis.grid(axis="y", alpha=.25)
        axis.legend(ncol=min(5, len(methods)), loc="lower center", bbox_to_anchor=(.5, 1.01), frameon=False)
        suffix = "" if start == 0 else f"_{start // 5 + 1:02d}"
        save(fig, "objective_by_instance" + suffix)

    pairs = [row for row in comparisons if row["win"] + row["tie"] + row["loss"]]
    main = [row for row in pairs if row["method"] == "ALNS"]
    others = [row for row in pairs if row["method"] != "ALNS"]
    groups = [("win_tie_loss", main)] if main else []
    groups += [(f"win_tie_loss_other_{i // 6 + 1:02d}", others[i:i + 6]) for i in range(0, len(others), 6)]
    for stem, rows in groups:
        fig, axis = plt.subplots(figsize=(7.2, 4.5))
        positions = list(range(len(rows)))
        left = [0] * len(rows)
        maximum = max(row["win"] + row["tie"] + row["loss"] for row in rows)
        for key, label, color in (("win", "Thắng", "#15803d"), ("tie", "Hòa", "#eab308"), ("loss", "Thua", "#dc2626")):
            values = [row[key] for row in rows]
            axis.barh(positions, values, left=left, height=.55, color=color, label=label)
            for i, value in enumerate(values):
                if value >= maximum * .055:
                    axis.text(left[i] + value / 2, i, str(value), ha="center", va="center", fontsize=10,
                              color="black" if key == "tie" else "white")
            left = [a + b for a, b in zip(left, values)]
        for i, row in enumerate(rows):
            axis.text(maximum * 1.025, i, f"{row['win']} / {row['tie']} / {row['loss']}", va="center", fontsize=9)
        axis.set_yticks(positions, [f"{r['method']} so với {r['reference']}" for r in rows], fontsize=10)
        axis.invert_yaxis()
        axis.set_xlim(0, maximum * 1.32)
        from matplotlib.ticker import MaxNLocator
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        axis.set_xlabel("Số bài toán · Số bên phải: thắng / hòa / thua", fontsize=9)
        axis.set_title("Kết quả so sánh theo từng bài toán", fontsize=13, pad=38)
        axis.legend(ncol=3, loc="lower center", bbox_to_anchor=(.5, 1.01), frameon=False)
        axis.spines[["top", "right"]].set_visible(False)
        save(fig, stem)
    schedule = _make_schedule_svg(results, output)
    if schedule:
        paths.append(schedule)
    return paths


def _svg_text(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _make_svg_charts(summaries, comparisons, output, results=None):
    """Create simple vector charts when optional matplotlib is unavailable."""
    charts = output / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    instances = sorted({row["instance"] for row in summaries})
    methods = sorted({row["method"] for row in summaries})
    by = {(row["instance"], row["method"]): row for row in summaries}
    colors = ("#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#0891b2", "#be123c")
    width, height, left, top, right, bottom = 1100, 560, 90, 55, 35, 125
    values = [row["objective"]["mean"] for row in summaries]
    low, high = min(values), max(values)
    span = high - low or 1.0
    x_step = (width - left - right) / max(1, len(instances) - 1)
    y = lambda value: top + (high - value) / span * (height - top - bottom)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="{left}" y="28" font-family="sans-serif" font-size="20">Mean F theo instance (thấp hơn tốt hơn)</text>',
             f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333"/>',
             f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#333"/>']
    for index, instance in enumerate(instances):
        x = left + index * x_step
        parts.append(f'<text x="{x:.1f}" y="{height-bottom+24}" text-anchor="end" transform="rotate(-35 {x:.1f} {height-bottom+24})" font-family="sans-serif" font-size="11">{_svg_text(instance)}</text>')
    for method_index, method in enumerate(methods):
        points = []
        for index, instance in enumerate(instances):
            row = by.get((instance, method))
            if row:
                points.append(f"{left + index*x_step:.1f},{y(row['objective']['mean']):.1f}")
        if points:
            color = colors[method_index % len(colors)]
            parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/>')
            legend_x = left + method_index * 135
            parts.append(f'<line x1="{legend_x}" y1="{height-28}" x2="{legend_x+18}" y2="{height-28}" stroke="{color}" stroke-width="3"/>')
            parts.append(f'<text x="{legend_x+23}" y="{height-24}" font-family="sans-serif" font-size="12">{_svg_text(method)}</text>')
    parts.append("</svg>")
    objective_path = charts / "objective_by_instance.svg"
    objective_path.write_text("\n".join(parts), encoding="utf-8")

    pairs = [row for row in comparisons if row["win"] + row["tie"] + row["loss"]]
    bar_width = 1100
    bar_height = max(420, 100 + len(pairs) * 34)
    max_count = max((max(row["win"], row["tie"], row["loss"]) for row in pairs), default=1) or 1
    bar_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {bar_width} {bar_height}">',
                 '<rect width="100%" height="100%" fill="white"/>',
                 '<text x="30" y="30" font-family="sans-serif" font-size="20">Thắng / hòa / thua theo instance</text>']
    for index, row in enumerate(pairs):
        y0 = 65 + index * 34
        label = f"{row['method']} vs {row['reference']}"
        bar_parts.append(f'<text x="30" y="{y0+14}" font-family="sans-serif" font-size="12">{_svg_text(label)}</text>')
        x0 = 180
        for value, color in ((row["win"], "#059669"), (row["tie"], "#d97706"), (row["loss"], "#dc2626")):
            bar_parts.append(f'<rect x="{x0}" y="{y0}" width="{max(1, 650*value/max_count):.1f}" height="18" fill="{color}"/>')
            x0 += 660 * value / max_count
    bar_parts.append("</svg>")
    comparison_path = charts / "win_tie_loss.svg"
    comparison_path.write_text("\n".join(bar_parts), encoding="utf-8")
    paths = [objective_path.relative_to(output).as_posix(), comparison_path.relative_to(output).as_posix()]
    schedule = _make_schedule_svg(results, output)
    if schedule:
        paths.append(schedule)
    return paths


def _make_schedule_svg(results, output):
    """Export one readable picker timeline for the first ALNS result."""
    if not results:
        return None
    priority = {"ALNS": 0, "LNS": 1, "VNS": 2, "B3": 3, "B2": 4, "B0": 5}
    candidates = sorted(results, key=lambda row: (priority.get(row.get("method"), 9), row.get("instance", "")))
    result = next((row for row in candidates if row.get("batches")), None)
    if result is None:
        return None
    batches = result["batches"]
    pickers = sorted({batch["picker"] for batch in batches})
    makespan = max((batch["end"] for batch in batches), default=0)
    if makespan <= 0:
        return None
    width, left, right, top, row_height, bottom = 1200, 170, 30, 75, 48, 55
    height = top + row_height * len(pickers) + bottom
    colors = ("#2563eb", "#059669", "#d97706", "#7c3aed", "#dc2626", "#0891b2")
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="30" y="30" font-family="sans-serif" font-size="20">Timeline picker — {_svg_text(result["instance"])} / {_svg_text(result["method"])}</text>',
             f'<text x="30" y="52" font-family="sans-serif" font-size="12">Mỗi thanh là một chuyến; trục x là thời gian, makespan = {makespan:.3f}</text>']
    scale = (width - left - right) / makespan
    for index, picker in enumerate(pickers):
        y0 = top + index * row_height
        parts.append(f'<text x="{left-12}" y="{y0+22}" text-anchor="end" font-family="sans-serif" font-size="13">Picker {picker}</text>')
        parts.append(f'<line x1="{left}" y1="{y0+row_height-6}" x2="{width-right}" y2="{y0+row_height-6}" stroke="#e5e7eb"/>')
        for batch_index, batch in enumerate(sorted((b for b in batches if b["picker"] == picker), key=lambda b: b["start"])):
            x = left + batch["start"] * scale
            bar_width = max(2, (batch["end"] - batch["start"]) * scale)
            color = colors[batch_index % len(colors)]
            parts.append(f'<rect x="{x:.1f}" y="{y0+6}" width="{bar_width:.1f}" height="24" rx="4" fill="{color}"/>')
            if bar_width >= 45:
                label = f"{batch['id']} ({len(batch['orders'])} đơn)"
                parts.append(f'<text x="{x+4:.1f}" y="{y0+22}" font-family="sans-serif" font-size="10" fill="white">{_svg_text(label)}</text>')
    parts.append(f'<text x="{left}" y="{height-17}" font-family="sans-serif" font-size="11">0</text>')
    parts.append(f'<text x="{width-right}" y="{height-17}" text-anchor="end" font-family="sans-serif" font-size="11">{makespan:.3f}</text>')
    parts.append("</svg>")
    path = output / "charts" / "schedule_by_picker.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
    return path.relative_to(output).as_posix()


def build_report(benchmark: Path, output: Path, charts=True):
    verified = verify_benchmark(benchmark)
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise InputError(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    _write_csv(output / "raw_metrics.csv", verified["csv_rows"], list(verified["csv_rows"][0]))
    summary_rows, summary_fields = _flat_summaries(verified["summaries"])
    _write_csv(output / "per_instance.csv", summary_rows, summary_fields)
    comparison_rows, comparison_fields = _flat_comparisons(verified["comparisons"])
    _write_csv(output / "comparison.csv", comparison_rows, comparison_fields)
    pair_rows, pair_fields = _comparison_pairs(verified["comparisons"])
    _write_csv(output / "comparison_pairs.csv", pair_rows, pair_fields)
    (output / "config.json").write_text(json.dumps(verified["config"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "source_manifest.json").write_text(json.dumps(verified["manifest"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_selection = verified["root"] / "source_selection.json"
    if source_selection.is_file():
        shutil.copyfile(source_selection, output / "source_selection.json")

    instance_labels = {}
    for path in sorted((verified["root"] / "instances").glob("*.json")):
        instance = read_instance(path)
        scenario = instance.metadata.get("scenario", {})
        if scenario.get("name"):
            title = scenario["name"].split(" (")[0]
            seed = instance.name.rsplit("seed", 1)[-1]
            instance_labels[instance.name] = textwrap.fill(title, 18) + f"\n{len(instance.orders)} đơn · seed {seed}"
    chart_paths = _make_charts(verified["summaries"], verified["comparisons"], output, verified["results"], instance_labels) if charts else []
    if charts:
        from scripts.report_extra_charts import extra_charts
        chart_paths.extend(extra_charts(verified, output, instance_labels))
    methods = sorted({result["method"] for result in verified["results"]})
    instances = sorted({result["instance"] for result in verified["results"]})
    source_digest = hashlib.sha256((verified["root"] / "manifest.json").read_bytes()).hexdigest()
    verification = {
        "benchmark": str(verified["root"]),
        "source_manifest_sha256": source_digest,
        "raw_runs": len(verified["results"]),
        "instances": len(instances),
        "methods": methods,
        "charts": chart_paths,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
    }
    if source_selection.is_file():
        verification["source_selection_sha256"] = hashlib.sha256(source_selection.read_bytes()).hexdigest()
    (output / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["# Bảng và biểu đồ so sánh từ benchmark", "", f"Nguồn benchmark: `{verified['root']}`.",
             f"Đã kiểm tra độc lập **{len(verified['results'])} run**, **{len(instances)} instance**, **{len(methods)} method**.",
             "Mỗi instance là một phiếu so sánh sau khi trung bình các search seed; không đếm seed như instance độc lập.", "",
             "## So sánh tổng hợp", "", "| Method | Reference | Instance | Thắng | Hòa | Thua | Cải thiện F trung bình (%) |", "|---|---|---:|---:|---:|---:|---:|"]
    for row in comparison_rows:
        improvement = "N/A" if row["mean_improvement_pct"] is None else f"{row['mean_improvement_pct']:.3f}"
        lines.append(f"| {row['method']} | {row['reference']} | {row['instances']} | {row['win']} | {row['tie']} | {row['loss']} | {improvement} |")
    lines += ["", "## So sánh theo từng instance", "", "| Instance | Method | Runs | F mean ± std | Distance mean | Makespan mean | Tardiness mean | Late orders mean | Runtime mean (s) |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary_rows:
        lines.append(f"| {row['instance']} | {row['method']} | {row['runs']} | {row['objective_mean']:.5f} ± {row['objective_std']:.5f} | {row['distance_mean']:.3f} | {row['makespan_mean']:.3f} | {row['tardiness_mean']:.3f} | {row['late_orders_mean']:.3f} | {row['total_seconds_mean']:.4f} |")
    chart_note = (
        "- " + ", ".join(f"`{path}`" for path in chart_paths) + ": biểu đồ so sánh."
        if chart_paths else
        "- Không sinh biểu đồ; các bảng CSV vẫn đầy đủ."
    )
    lines += ["", "## Tệp dùng cho báo cáo", "", "- `comparison.csv`: bảng thắng/hòa/thua và cải thiện trung bình.", "- `comparison_pairs.csv`: kết quả từng instance cho từng cặp so sánh.", "- `per_instance.csv`: trung bình, độ lệch chuẩn và chẩn đoán theo instance/method.", "- `raw_metrics.csv`: từng run sau khi benchmark đã ghi kết quả.", chart_note, "", "Các số liệu chỉ được xuất sau khi raw solution, fingerprint instance, CSV, summary và comparison khớp nhau.", ""]
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return verification


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, required=True, help="One completed benchmark directory")
    parser.add_argument("--output", type=Path, required=True, help="New directory for report-ready artifacts")
    parser.add_argument("--no-charts", action="store_true", help="Skip PNG/PDF chart generation")
    args = parser.parse_args(argv)
    try:
        verification = build_report(args.benchmark, args.output, charts=not args.no_charts)
    except (InputError, OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
