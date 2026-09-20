"""Run the 5 warehouse map scenarios benchmark with automated charts and reporting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmark import benchmark
from src.models import write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/map_scenarios_benchmark.json",
                        help="Path to scenarios benchmark config JSON (default: configs/map_scenarios_benchmark.json)")
    parser.add_argument("--output", type=Path, required=True,
                        help="New output directory for raw benchmark runs")
    parser.add_argument("--report-output", type=Path, default=None,
                        help="Output directory for charts and report (default: <output>_report)")
    parser.add_argument("--seconds", type=float, default=None,
                        help="Search budget in seconds per algorithm run")
    parser.add_argument("--search-seeds", type=int, nargs="+", default=None,
                        help="Random search seeds (e.g. 1 2 3)")
    parser.add_argument("--no-report", action="store_true",
                        help="Skip generating comparison charts and report")
    args = parser.parse_args(argv)

    config_path = args.config.resolve()
    if not config_path.is_file():
        raise SystemExit(f"Config file not found: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))

    if args.seconds is not None:
        config.setdefault("search", {})["seconds"] = args.seconds
    if args.search_seeds is not None:
        config["search_seeds"] = args.search_seeds

    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"Thư mục output đã tồn tại: {output}\nVui lòng chỉ định một thư mục mới (ví dụ: {output}_01).")

    report_output = args.report_output.resolve() if args.report_output else output.parent / f"{output.name}_report"

    print(f"🚀 [1/2] Bắt đầu chạy Benchmark 5 Map kịch bản (B0, B2, LNS, ALNS, VNS)...")
    print(f"   - File cấu hình: {config_path}")
    print(f"   - Thư mục lưu dữ liệu thô: {output}")

    rows = benchmark(config, output, progress=lambda row: print(
        f"   [{row['instance']}] {row['method']:<4} seed={row['search_seed']:<2} F={row['objective']:.5f} (quãng đường={row['distance']:.1f}m)", flush=True))

    print(f"\n✅ Đã hoàn thành {len(rows)} lượt chạy và lưu vào: {output}")

    if not args.no_report:
        from scripts.build_comparison_report import build_report
        print(f"\n📊 [2/2] Đang tự động kiểm định và vẽ biểu đồ so sánh...")
        build_report(output, report_output)
        print(f"🎉 Báo cáo và biểu đồ đã được lưu hoàn tất tại:")
        print(f"   📂 {report_output}")
        print(f"   ├── 📈 Biểu đồ so sánh: {report_output / 'charts'}")
        print(f"   ├── 📑 Bảng số liệu chi tiết: {report_output / 'comparison.csv'}")
        print(f"   └── 📝 Báo cáo tổng hợp: {report_output / 'REPORT.md'}\n")


if __name__ == "__main__":
    main()
