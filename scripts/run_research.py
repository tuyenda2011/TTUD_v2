"""Locked, sequential tuning/holdout study with independent solution revalidation."""
import argparse
import hashlib
import json
import statistics
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from warehouse_opt.benchmark import benchmark
from warehouse_opt.comparison import paired_comparisons
from warehouse_opt.evaluator import Evaluator
from warehouse_opt.exact import solve_exact
from warehouse_opt.generator import generate
from warehouse_opt.heuristics import fcfs, greedy, list_schedule
from warehouse_opt.models import InputError, read_instance, write_json
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import fingerprint, solve
from warehouse_opt.validator import validate_solution


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    files = [*sorted((ROOT / "warehouse_opt").glob("*.py")), Path(__file__).resolve()]
    return {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in files}


def seal(path, data):
    if path.exists():
        raise InputError(f"Refusing to overwrite sealed file: {path}")
    write_json(path, data)
    path.with_suffix(".sha256").write_text(digest(path) + "\n", encoding="utf-8")


def checked_seal(path):
    if digest(path) != path.with_suffix(".sha256").read_text().strip():
        raise InputError(f"Seal mismatch: {path}")
    return read(path)


def prepare(protocol, output):
    if output.exists() and any(output.iterdir()):
        raise InputError("Prepare requires a new empty output directory; old evidence is never overwritten")
    cohorts = ("tuning", "holdout", "ablation", "sensitivity")
    seed_sets = [set(protocol[name]["instance_seeds"]) for name in cohorts]
    if any(a & b for i, a in enumerate(seed_sets) for b in seed_sets[i + 1:]):
        raise InputError("Tuning, holdout, ablation and sensitivity instance seeds must be disjoint")
    datasets = {}
    for name in cohorts:
        datasets[name] = []
        for n in protocol[name]["sizes"]:
            for seed in protocol[name]["instance_seeds"]:
                instance = generate(n=n, seed=seed, **protocol["generator"])
                instance.name = f"{name}-{instance.name}"
                path = output / "datasets" / f"{instance.name}.json"
                write_json(path, instance.to_dict())
                datasets[name].append({"file": path.relative_to(output).as_posix(), "sha256": fingerprint(instance)})
    datasets["exact"] = []
    for case in protocol["exact"]["cases"]:
        instance = generate(**case, aisles=2, rows=2)
        instance.name = f"exact-{instance.name}"
        path = output / "datasets" / f"{instance.name}.json"
        write_json(path, instance.to_dict())
        datasets["exact"].append({"file": path.relative_to(output).as_posix(), "sha256": fingerprint(instance)})
    seal(output / "protocol.lock.json", {"created_utc": datetime.now(timezone.utc).isoformat(),
         "protocol": protocol, "source_sha256": source_hashes(), "datasets": datasets})
    for relative in source_hashes():
        target = output / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    print("Prepared and sealed all datasets before tuning or holdout evaluation", flush=True)


def checked_protocol(output):
    locked = checked_seal(output / "protocol.lock.json")
    if locked["source_sha256"] != source_hashes():
        raise InputError("Source changed after preregistration; use a new study directory")
    for entries in locked["datasets"].values():
        for entry in entries:
            if fingerprint(read_instance(output / entry["file"])) != entry["sha256"]:
                raise InputError(f"Dataset changed: {entry['file']}")
    return locked


def benchmark_config(output, locked, cohort, search, methods=None, weights=None):
    protocol = locked["protocol"]
    return {"instances": [str((output / r["file"]).resolve()) for r in locked["datasets"][cohort]],
            "search_seeds": protocol[cohort]["search_seeds"], "search": search,
            "methods": methods or protocol["methods"],
            "weights": weights or protocol["primary_weights"]}


def run_benchmark(config, path):
    if path.exists():
        raise InputError(f"Refusing to overwrite benchmark: {path}")
    count = 0

    def progress(row):
        nonlocal count
        count += 1
        if count % 10 == 0:
            print(f"{path.name}: {count} runs; {row['instance']} {row['method']} "
                  f"iterations={row['iterations_completed']}", flush=True)

    return benchmark(config, path, progress=progress)


def tune(output, locked):
    protocol = locked["protocol"]
    candidates = []
    for name, preset in sorted(protocol["presets"].items()):
        search = {**protocol["search"], **preset}
        rows = run_benchmark(benchmark_config(output, locked, "tuning", search, ["B0", "B2", "ALNS"]),
                             output / "tuning" / name)
        scores = defaultdict(list)
        for row in rows:
            if row["method"] == "ALNS":
                scores[row["instance"]].append(row["objective"])
        candidates.append({"name": name, "score": statistics.mean(statistics.mean(v) for v in scores.values()),
                           "search": search})
    selected = min(candidates, key=lambda r: (r["score"], r["name"]))
    seal(output / "selection.lock.json", {"selected": selected, "candidates": candidates,
         "primary_weights": protocol["primary_weights"], "protocol_sha256": digest(output / "protocol.lock.json"),
         "selected_utc": datetime.now(timezone.utc).isoformat(),
         "note": "Weights are a predeclared objective, not tuned by comparing incompatible F scales."})
    print(f"Selected {selected['name']} using tuning only; selection sealed before holdout", flush=True)


def selection(output):
    selected = checked_seal(output / "selection.lock.json")
    if selected["protocol_sha256"] != digest(output / "protocol.lock.json"):
        raise InputError("Selection belongs to a different protocol")
    return selected["selected"]["search"]


def holdout(output, locked):
    run_benchmark(benchmark_config(output, locked, "holdout", selection(output)), output / "holdout")


def ablation(output, locked):
    base = {**selection(output), "seconds": locked["protocol"]["ablation"]["seconds"]}
    variants = {"full": ("ALNS", {}), "uniform": ("LNS", {}),
                "no_schedule_local": ("ALNS_NO_SCHEDULE", {}), "no_2opt_compound": ("ALNS_NO_2OPT", {})}
    for op in ("random", "related", "late", "batch"):
        variants[f"without_{op}"] = ("ALNS", {"destroy_operators": [v for v in SearchConfig().destroy_operators if v != op]})
    variants["greedy_only"] = ("ALNS", {"repair_operators": ["greedy"]})
    variants["regret_only"] = ("ALNS", {"repair_operators": ["regret2"]})
    all_rows = []
    for name, (method, changes) in variants.items():
        config = benchmark_config(output, locked, "ablation", {**base, **changes}, ["B0", method])
        rows = run_benchmark(config, output / "ablation" / name)
        all_rows.extend({**row, "method": name} for row in rows if row["method"] == method)
    write_json(output / "ablation" / "comparison.json", paired_comparisons(all_rows, ("full",)))


def pareto_profiles(rows):
    keys = ("distance", "makespan", "tardiness", "late_orders")
    groups = defaultdict(list)
    for row in rows:
        groups[row["instance"], row["profile"]].append(row)
    means = [{"instance": name, "profile": profile,
              **{k: statistics.mean(r[k] for r in group) for k in keys}}
             for (name, profile), group in sorted(groups.items())]
    for row in means:
        row["nondominated"] = not any(
            other["instance"] == row["instance"] and all(other[k] <= row[k] for k in keys)
            and any(other[k] < row[k] for k in keys) for other in means)
    return means


def sensitivity(output, locked):
    rows = []
    for name, weights in locked["protocol"]["weight_profiles"].items():
        config = benchmark_config(output, locked, "sensitivity", selection(output), ["B0", "ALNS"], weights)
        results = run_benchmark(config, output / "sensitivity" / name)
        rows.extend({**r, "profile": name} for r in results if r["method"] == "ALNS")
    write_json(output / "sensitivity" / "summary.json", pareto_profiles(rows))


def save_validated(output, instance, result, filename):
    errors = validate_solution(instance, result)
    if errors:
        raise InputError(str(errors))
    result["instance_sha256"] = fingerprint(instance)
    path = output / "raw" / filename
    write_json(path, result)
    return {"file": f"raw/{filename}", "instance_sha256": fingerprint(instance)}


def exact_and_routing(output, locked):
    target = output / "exact"
    if target.exists():
        raise InputError("Exact output already exists")
    protocol = locked["protocol"]
    search = SearchConfig(**selection(output))
    records, gaps, routing = [], [], []
    for entry in locked["datasets"]["exact"]:
        instance = read_instance(output / entry["file"])
        write_json(target / "instances" / f"{instance.name}.json", instance.to_dict())
        oracle = solve_exact(instance, protocol["exact"]["seconds"], protocol["exact"]["max_states"])
        records.append(save_validated(target, instance, oracle, f"{instance.name}-EXACT.json"))
        optimum = oracle["metrics"]["objective"]
        for method in protocol["methods"]:
            result = solve(instance, method, 42, search, protocol["primary_weights"])
            if result["objective_config"] != oracle["objective_config"]:
                raise InputError("Exact and heuristic objective scales differ")
            records.append(save_validated(target, instance, result, f"{instance.name}-{method}.json"))
            value = result["metrics"]["objective"]
            if oracle["certified_optimal"] and value < optimum - 1e-9:
                raise InputError("Heuristic scored below certified oracle")
            gap = 100 * (value - optimum) / optimum if oracle["certified_optimal"] and optimum > 0 else None
            gaps.append({"instance": instance.name, "method": method, "objective": value,
                         "exact_objective": optimum, "certified_optimal": oracle["certified_optimal"],
                         "gap_pct": gap, "states": oracle["states"]})
        ctx = Evaluator(instance)
        baseline = list_schedule(ctx, fcfs(ctx), "nn")
        ctx.set_reference(baseline, protocol["primary_weights"])
        plan = list_schedule(ctx, greedy(ctx), "2opt")
        for mode in ("nn", "2opt", "s_shape", "exact"):
            result = ctx.evaluate(plan, mode, details=True)
            result.update(method=f"FIXED_PLAN_{mode}", feasible=True)
            records.append(save_validated(target, instance, result, f"{instance.name}-route-{mode}.json"))
            routing.append({"instance": instance.name, "routing": mode, **result["metrics"]})
        print(f"Exact {instance.name}: certified={oracle['certified_optimal']}; states={oracle['states']}", flush=True)
    write_json(target / "manifest.json", {"runs": records})
    write_json(target / "summary.json", gaps)
    write_json(target / "routing.json", routing)


def verify(output, locked):
    selection(output)
    count = 0
    manifests = sorted(p for p in output.rglob("manifest.json") if "source" not in p.parts)
    expected = len(locked["protocol"]["presets"]) + 1 + 10 + len(locked["protocol"]["weight_profiles"]) + 1
    if len(manifests) != expected:
        raise InputError(f"Incomplete study: expected {expected} manifests, found {len(manifests)}")
    for path in manifests:
        instances = {}
        for record in read(path)["runs"]:
            result = read(path.parent / record["file"])
            name = result["instance"]
            if name not in instances:
                instances[name] = read_instance(path.parent / "instances" / f"{name}.json")
            instance = instances[name]
            if fingerprint(instance) != record["instance_sha256"] or fingerprint(instance) != result["instance_sha256"]:
                raise InputError(f"Fingerprint mismatch: {path}")
            errors = validate_solution(instance, result)
            if errors:
                raise InputError(f"{record['file']}: {errors}")
            count += 1
    write_json(output / "verification.json", {"solutions": count, "manifest_count": len(manifests),
               "protocol_sha256": digest(output / "protocol.lock.json"),
               "selection_sha256": digest(output / "selection.lock.json"), "source_matches": True})
    print(f"Revalidated {count} solutions in {len(manifests)} experiment groups", flush=True)
    return count


def report(output, locked):
    selected = checked_seal(output / "selection.lock.json")
    comparisons = read(output / "holdout" / "comparison.json")
    summaries = read(output / "holdout" / "summary.json")
    alns = [r for r in summaries if r["method"] == "ALNS"]
    zero = sum(r["search_diagnostics"]["zero_iteration_runs"] for r in alns)
    adapted = sum(r["search_diagnostics"]["adapted_runs"] for r in alns)
    total = sum(r["runs"] for r in alns)
    lines = ["# Nghiên cứu bổ sung: ALNS tích hợp với bộ giải mã tuyến heuristic", "",
             ("Đóng góp của đề tài là thiết kế và đánh giá cách áp dụng ALNS cho bài toán tích hợp. "
             "ALNS là khung thuật toán có sẵn; kết quả không chứng minh tối ưu toàn cục."), "",
             "## Quy trình đã khóa", "",
             f"Protocol SHA-256: `{digest(output / 'protocol.lock.json')}`.", "",
             f"Selection SHA-256: `{digest(output / 'selection.lock.json')}`.", "",
             (f"Preset được chọn trên tuning: **{selected['selected']['name']}**. "
             "Tuning: 3 instance, 2 search seed, 3 cấu hình; holdout: 6 instance (10/30/100 đơn), "
             "10 search seed. Các tập tuning, holdout, ablation, sensitivity có seed dữ liệu rời nhau. "
             "Toàn bộ dữ liệu được tạo và hash trước tuning; cấu hình được khóa trước lần giải holdout đầu tiên. "
             "Trọng số chính bằng nhau được chốt trước; không chọn trọng số bằng cách so F khác thang đo."), "",
             ("Ngân sách chính 2 giây tính cả khởi tạo, không gồm graph/B0 chung và validation; "
             "mọi thời gian tổng đều được ghi. Trần 100.000 vòng là điều kiện dừng phụ; "
             "không bảo đảm mọi method tiêu thụ hết 2 giây. Chạy tuần tự trên máy phát triển, không cô lập hệ điều hành."), "",
             "## ALNS so với đối chứng trên holdout", "",
             "| Reference | Win | Tie | Loss | Mean improvement F (%) |",
             "|---|---:|---:|---:|---:|"]
    for pair in comparisons:
        if pair["method"] == "ALNS":
            lines.append(f"| {pair['reference']} | {pair['win']} | {pair['tie']} | {pair['loss']} | {pair['mean_improvement_pct']:.3f} |")
    lines += ["", ("Mỗi instance có một phiếu sau khi trung bình seed. Đây là thống kê mô tả, "
              "không phải kiểm định ý nghĩa thống kê; sáu instance chưa đại diện mọi loại kho."), "",
              f"ALNS có **{zero}/{total} ca 0 vòng**, **{adapted}/{total} ca có vòng hoàn thành sau cập nhật trọng số**.", "",
              "| Instance | Min iterations | Median iterations | Adapted runs |",
              "|---|---:|---:|---:|"]
    for row in alns:
        d = row["search_diagnostics"]
        lines.append(f"| {row['instance']} | {d['iterations_min']} | {d['iterations_median']} | {d['adapted_runs']}/{row['runs']} |")
    lines += ["", "## Ablation", "",
              ("Các biến thể dùng cùng tập riêng, 10 search seed và ngân sách 1 giây. "
              "Uniform chỉ tắt thích nghi (LNS); các phép without_* bỏ đúng một destroy operator; "
              "greedy_only/regret_only bỏ một repair operator. no_schedule_local bỏ lượt local search lịch, "
              "repair vẫn có thể đổi lịch. no_2opt_compound đổi cả khởi tạo và giải mã nên là ablation kết hợp. "
              "So sánh decoder trên cùng plan ở phần sau giúp tách tác động tuyến."), "",
              "| Variant vs full ALNS | Win | Tie | Loss | Mean improvement F (%) |",
              "|---|---:|---:|---:|---:|"]
    for pair in read(output / "ablation" / "comparison.json"):
        lines.append(f"| {pair['method']} | {pair['win']} | {pair['tie']} | {pair['loss']} | {pair['mean_improvement_pct']:.3f} |")
    lines += ["", "## Độ nhạy trọng số", "",
              ("Giữ nguyên cấu hình search đã chọn. So các chỉ số vật lý trên cùng instance, "
              "không xếp hạng F giữa các trọng số. Pareto dưới đây tính trên trung bình seed của "
              "distance, makespan, tardiness và late orders trong bốn phương án đã chạy; "
              "không phải biên Pareto toàn cục."), "",
              "| Instance | Profile | Distance | Makespan | Tardiness | Late orders | Nondominated |",
              "|---|---|---:|---:|---:|---:|---|"]
    for row in read(output / "sensitivity" / "summary.json"):
        lines.append(f"| {row['instance']} | {row['profile']} | {row['distance']:.2f} | {row['makespan']:.3f} | "
                     f"{row['tardiness']:.3f} | {row['late_orders']:.2f} | {row['nondominated']} |")
    by_key = {(r["instance"], r["method"]): r for r in summaries}
    tradeoffs = []
    for row in alns:
        for reference in ("B0", "B2", "B3", "LNS", "VNS"):
            other = by_key[row["instance"], reference]
            if row["objective"]["mean"] < other["objective"]["mean"] and row["late_orders"]["mean"] > other["late_orders"]["mean"]:
                tradeoffs.append(f"- {row['instance']}: ALNS F={row['objective']['mean']:.5f} < {reference} "
                                 f"F={other['objective']['mean']:.5f}, nhưng số đơn trễ {row['late_orders']['mean']:.2f} "
                                 f"> {other['late_orders']['mean']:.2f}.")
    lines += ["", "Các ca F giảm nhưng số đơn trễ tăng trên holdout:", "", *(tradeoffs or ["Không quan sát thấy trong bộ chạy này; mô hình vẫn cho phép đánh đổi đó."])]
    lines += ["", "## Gap tối ưu trên bài nhỏ", "",
              ("Oracle vét cạn cả phân hoạch, phân công, thứ tự và tuyến. Chỉ tính gap khi certified_optimal=true "
              "và dùng cùng chuẩn B0/trọng số. Đây là sáu instance 4–6 đơn, 1–2 picker, capacity 10–20, "
              "deadline tightness 0,1–0,6; không ngoại suy gap sang bài 100 đơn."), "",
              "| Instance | Method | Certified | Gap (%) | States |", "|---|---|---|---:|---:|"]
    for row in read(output / "exact" / "summary.json"):
        gap = "N/A" if row["gap_pct"] is None else f"{row['gap_pct']:.4f}"
        lines.append(f"| {row['instance']} | {row['method']} | {row['certified_optimal']} | {gap} | {row['states']} |")
    lines += ["", "## Chất lượng tuyến trên cùng plan", "",
              ("Giữ nguyên batch, picker và thứ tự batch của B2. Chỉ thay decoder tuyến; thời gian và độ trễ "
              "được tính lại. S-Shape chỉ chạy trên layout single-block hợp lệ. Tập nhỏ có bốn vị trí SKU."), "",
              "| Instance | Decoder | Distance | Makespan | Tardiness |", "|---|---|---:|---:|---:|"]
    for row in read(output / "exact" / "routing.json"):
        lines.append(f"| {row['instance']} | {row['routing']} | {row['distance']:.2f} | {row['makespan']:.3f} | {row['tardiness']:.3f} |")
    lines += ["", "## Giới hạn và việc còn lại", "",
              "- Kết luận phải theo từng đối chứng và kích thước; không mặc định ALNS thắng LNS/VNS.",
              "- Một layout chính, picker đồng nhất, đơn tĩnh; chưa đo tác động congestion hoặc ca làm việc.",
              "- Chưa có kiểm định thống kê khẳng định ưu thế, chưa benchmark rộng dữ liệu tác giả.",
              "- Thử với ba người dùng thật chưa thực hiện; phiếu trong docs/USER_STUDY.md không được thay bằng dữ liệu mô phỏng.",
              "- Hash và validator chứng minh tính toàn vẹn/khả thi; chỉ oracle certified mới chứng minh tối ưu cho bài tương ứng.", ""]
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def package(output, locked):
    verify(output, locked)
    archive = output.parent / f"{output.name}.zip"
    if archive.exists():
        raise InputError("Archive already exists")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(output))
    archive.with_suffix(".zip.sha256").write_text(digest(archive) + "\n", encoding="utf-8")
    print(f"Packaged {archive}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "tune", "holdout", "ablation", "sensitivity", "exact", "report", "verify", "package", "all"))
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/research_protocol.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results/research_20260919")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.stage in ("prepare", "all"):
        prepare(read(args.protocol), output)
        if args.stage == "prepare":
            return
    locked = checked_protocol(output)
    stages = {"tune": tune, "holdout": holdout, "ablation": ablation, "sensitivity": sensitivity,
              "exact": exact_and_routing, "report": report, "verify": verify, "package": package}
    for name in stages if args.stage == "all" else [args.stage]:
        stages[name](output, locked)


if __name__ == "__main__":
    main()
