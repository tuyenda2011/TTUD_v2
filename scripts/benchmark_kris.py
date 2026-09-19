"""Small integration benchmark on unchanged author order/deadline data."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from warehouse_opt.models import read_instance, write_json
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import solve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=1.)
    args = parser.parse_args()
    catalog = json.loads((ROOT / "data/processed/kris_small/catalog.json").read_text())["instances"]
    selected = {}
    for row in sorted(catalog, key=lambda r: r["file"]):
        selected.setdefault(row["orders"], row)
    output = ROOT / "results/kris_author"
    rows = []
    for count, entry in sorted(selected.items()):
        instance = read_instance(ROOT / entry["file"])
        for method in ("B0", "B1", "B2", "B3", "LNS", "ALNS"):
            result = solve(instance, method, seed=42, config=SearchConfig(iterations=100, seconds=args.seconds))
            write_json(output / f"{instance.name}-{method}.json", result)
            row = {"instance": instance.name, "orders": count, "method": method, "raw_file": entry["raw_file"], "source_sha256": entry["sha256"], **result["metrics"]}
            rows.append(row)
            print(f"{instance.name} {method}: F={row['objective']:.6f}; late={row['late_orders']}", flush=True)
    write_json(output / "summary.json", rows)
    text = ["# Kiểm tra tích hợp trên dữ liệu tác giả Kris", "", "Đơn, SKU, kho, due dates, capacity, số picker và thời gian lấy từ file tác giả; không sinh đơn hoặc hạn mới. Khoảng cách và thời gian giữ nguyên đơn vị nguồn.", "", "Bộ giải vẫn dùng hàm mục tiêu hạn mềm chuẩn hóa của project. Đây không phải kết quả tái lập JOBPRSP-D hạn cứng, không đối chiếu với best-known của tác giả.", "", "| Instance | Orders | Method | F | Distance (source units) | Makespan (source units) | Tardiness (source units) | Late orders |", "|---|---:|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        text.append(f"| {row['instance']} | {row['orders']} | {row['method']} | {row['objective']:.6f} | {row['distance']:.1f} | {row['makespan']:.1f} | {row['tardiness']:.1f} | {row['late_orders']} |")
    text += ["", f"{len(rows)} nghiệm đã qua validator độc lập. Seed 42, tối đa 100 vòng / {args.seconds:g} giây, một instance mỗi kích thước. Chỉ là kiểm tra tích hợp, chưa phải nghiên cứu thống kê.", ""]
    (output / "REPORT.md").write_text("\n".join(text), encoding="utf-8")


if __name__ == "__main__":
    main()
