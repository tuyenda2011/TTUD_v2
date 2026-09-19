"""Reproducible experiment runner with raw results and per-instance paired summaries."""
import csv
import hashlib
import platform
import statistics
import time
from collections import defaultdict
from pathlib import Path

from .comparison import paired_comparisons
from .generator import generate
from .models import InputError, read_instance, write_json
from .search import SearchConfig
from .solver import METHODS, fingerprint, solve

STOCHASTIC = {"B3", "LNS", "ALNS", "VNS", "ALNS_NO_SCHEDULE", "ALNS_NO_2OPT"}


def benchmark(config, output, progress=None):
    output = Path(output)
    methods = config.get("methods", ["B0", "B1", "B2", "B3", "LNS", "ALNS"])
    if not methods or "B0" not in methods or len(methods) != len(set(methods)) or any(m not in METHODS for m in methods):
        raise InputError("Benchmark methods must be unique, supported and include B0")
    sizes = config.get("sizes", [20, 50])
    instance_seeds = config.get("instance_seeds", [101])
    search_seeds = config.get("search_seeds", [7])
    if any(not values or len(values) != len(set(values)) for values in (sizes, instance_seeds, search_seeds)):
        raise InputError("Sizes and seed lists must be nonempty and unique")
    options = SearchConfig(**config.get("search", {})).validate()
    started = time.perf_counter()
    rows, runs = [], []
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob("*.py"))}
    datasets = [(read_instance(path), None) for path in config.get("instances", [])]
    if not datasets:
        datasets = [(generate(n=n, seed=s, **config.get("generator", {})), s) for n in sizes for s in instance_seeds]
    names = [instance.name.casefold() for instance, _ in datasets]
    if len(names) != len(set(names)):
        raise InputError("Benchmark instance names must be unique (case-insensitive) to avoid overwriting results")
    write_json(output / "config.json", config)
    # Seal input identities before evaluating any method on them.
    write_json(output / "preregistered.json", {
        "config": config, "source_sha256": source_hashes,
        "instances": {instance.name: fingerprint(instance) for instance, _ in datasets}})
    for instance, instance_seed in datasets:
            n = len(instance.orders)
            write_json(output / "instances" / f"{instance.name}.json", instance.to_dict())
            for method in methods:
                for seed in search_seeds if method in STOCHASTIC else [search_seeds[0]]:
                    result = solve(instance, method, seed, options, tuple(config.get("weights", [1/3, 1/3, 1/3])))
                    file_name = f"{instance.name}-{method}-seed{seed}.json"
                    write_json(output / "raw" / file_name, result)
                    row = {"instance": instance.name, "n": n, "instance_seed": instance_seed, "method": method, "search_seed": seed, "feasible": result["feasible"], **result["metrics"], **result["timing"],
                           **{key: result["search"][key] for key in ("iterations_completed", "stop_reason", "adaptation_updates", "adapted_iterations", "search_executed", "budget_scope")}}
                    rows.append(row)
                    runs.append({"file": f"raw/{file_name}", "instance_sha256": result["instance_sha256"]})
                    if progress:
                        progress(row)
    with (output / "runs.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["instance"], row["method"])].append(row)
    summaries = []
    metric_names = ("objective", "distance", "makespan", "tardiness", "late_orders", "on_time_rate", "total_seconds")
    for (name, method), group in sorted(grouped.items()):
        baseline = grouped[(name, "B0")][0]
        summary = {"instance": name, "method": method, "runs": len(group), "feasible_rate": sum(row["feasible"] for row in group) / len(group)}
        summary["search_diagnostics"] = {
            "zero_iteration_runs": sum(r["iterations_completed"] == 0 for r in group) if method in STOCHASTIC else None,
            "iterations_min": min(r["iterations_completed"] for r in group),
            "iterations_median": statistics.median(r["iterations_completed"] for r in group),
            "adapted_runs": sum(r["adapted_iterations"] > 0 for r in group),
            "initialization_mean_seconds": statistics.mean(r["initialization_seconds"] for r in group),
            "search_mean_seconds": statistics.mean(r["search_seconds"] for r in group),
            "stop_reasons": {reason: sum(r["stop_reason"] == reason for r in group) for reason in sorted({r["stop_reason"] for r in group})}}
        for metric in metric_names:
            values = [r[metric] for r in group]
            avg = statistics.mean(values)
            sign = 1 if metric == "on_time_rate" else -1
            summary[metric] = {"mean": avg, "median": statistics.median(values), "std": statistics.stdev(values) if len(values) > 1 else 0., "best": max(values) if sign == 1 else min(values), "difference_vs_B0": avg - baseline[metric], "improvement_pct_vs_B0": 100 * sign * (avg - baseline[metric]) / baseline[metric] if baseline[metric] else None}
        summaries.append(summary)
    write_json(output / "summary.json", summaries)
    comparisons = paired_comparisons(rows, tuple(config.get("references", ["B0", "B2", "B3", "LNS", "VNS"])))
    write_json(output / "comparison.json", comparisons)
    write_json(output / "manifest.json", {"config": config, "source_sha256": source_hashes, "python": platform.python_version(), "platform": platform.platform(), "cpu": platform.processor(), "elapsed_seconds": time.perf_counter() - started, "runs": runs})
    lines = ["# Kết quả benchmark", "", "Dữ liệu tổng hợp; kết quả đo từ các lần chạy trong thư mục raw. Mỗi hàng tổng hợp seed trên cùng một instance, không coi seed là các instance độc lập.", "", "| Instance | Method | Runs | F mean ± std | Distance mean (m) | Makespan mean (min) | Tardiness mean (min) | Late mean | On-time rate | Total mean (s) | ΔF vs B0 (%) |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    if config.get("instances"):
        lines[2] = "Dữ liệu từ file cấu hình; giữ đơn vị nguồn và mục tiêu hạn mềm của project. Không so với best-known của bài toán gốc. Tổng hợp seed trong từng instance."
        lines[4] = lines[4].replace("(m)", "(instance units)").replace("(min)", "(instance units)")
    for row in summaries:
        f = row["objective"]
        improvement = "N/A" if f["improvement_pct_vs_B0"] is None else f"{f['improvement_pct_vs_B0']:.2f}"
        values = [row[m]["mean"] for m in metric_names[1:]]
        lines.append(f"| {row['instance']} | {row['method']} | {row['runs']} | {f['mean']:.5f} ± {f['std']:.5f} | " + " | ".join(f"{v:.3f}" for v in values) + f" | {improvement} |")
    lines += ["", f"Tất cả {len(rows)} nghiệm đã qua validator độc lập trước khi xuất.", "", "ΔF dương = cải thiện, âm = suy giảm. Thời gian tổng gồm graph/reference B0, khởi tạo và search. Ngân sách search tính cả khởi tạo, được kiểm tra giữa các thao tác; một phép tính đang chạy có thể vượt nhẹ giới hạn. Các method dùng cùng cấu hình search, heuristic dừng khi hoàn thành.", "", "Đây là báo cáo cho đúng cấu hình đã lưu, chưa phải bằng chứng tổng quát ALNS tốt hơn trên mọi dữ liệu.", ""]
    lines += ["## So sánh theo instance", "",
              ("Lấy trung bình seed trong từng instance trước; mỗi instance có một phiếu. "
              "Thắng/hòa/thua theo F với sai số tuyệt đối 1e-9. Không phải kiểm định ý nghĩa thống kê. "
              "Phần trăm cải thiện bỏ các mẫu có F tham chiếu bằng 0."), "",
              "| Method | Reference | Instances | Win | Tie | Loss | Mean improvement (%) |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for pair in comparisons:
        improvement = pair["mean_improvement_pct"]
        label = "N/A" if improvement is None else f"{improvement:.3f}"
        lines.append(f"| {pair['method']} | {pair['reference']} | {pair['instances']} | "
                     f"{pair['win']} | {pair['tie']} | {pair['loss']} | {label} |")
    lines += ["", "## Hoạt động tìm kiếm", "",
              ("Không loại ca 0 vòng khỏi bảng điểm để tránh thiên lệch chọn mẫu. Ca đó chỉ phản ánh khởi tạo; "
              "không dùng để khẳng định lợi ích search. Adapted runs đếm ca có vòng hoàn thành sau cập nhật trọng số. "
              "Một cập nhật ở cuối lần chạy chưa chứng minh trọng số đã được dùng. Median các chỉ số có trong summary.json."), "",
              "| Instance | Method | Zero-iteration runs | Min / median iterations | Adapted runs | Init mean (s) | Search mean (s) |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for row in summaries:
        if row["method"] not in STOCHASTIC:
            continue
        diag = row["search_diagnostics"]
        lines.append(f"| {row['instance']} | {row['method']} | {diag['zero_iteration_runs']} | "
                     f"{diag['iterations_min']} / {diag['iterations_median']} | {diag['adapted_runs']} | "
                     f"{diag['initialization_mean_seconds']:.4f} | {diag['search_mean_seconds']:.4f} |")
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return rows
