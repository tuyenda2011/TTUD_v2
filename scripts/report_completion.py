"""Build the final handoff from verified artifacts, without invented measurements."""
import argparse
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_research import digest, read, verify_aggregates
from src.models import read_instance, write_json
from src.solver import fingerprint
from src.validator import validate_solution


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=ROOT / "docs/BAO_CAO_HOAN_TAT_CAI_TIEN.md")
    args = parser.parse_args()
    root = args.artifacts.resolve()
    study = root / "study"
    # Re-audit with the exact source snapshot that produced the study, even if
    # later documentation-only fixes changed the working-tree runner hash.
    subprocess.run([sys.executable, str(study / "source/scripts/run_research.py"), "verify", "--output", str(study)], check=True)
    verified = read(study / "verification.json")["solutions"]
    preliminary = 0
    for group in ("baseline", "pilot", "development"):
        for path in sorted((root / group).rglob("manifest.json")):
            instances, results = {}, []
            for record in read(path)["runs"]:
                result = read(path.parent / record["file"])
                name = result["instance"]
                if name not in instances:
                    instances[name] = read_instance(path.parent / "instances" / f"{name}.json")
                instance = instances[name]
                assert fingerprint(instance) == result["instance_sha256"] == record["instance_sha256"]
                assert not validate_solution(instance, result)
                results.append(result)
            verify_aggregates(path.parent, results)
            preliminary += len(results)
    assert preliminary == 30 + 9 + 144, "Incomplete baseline, pilot or development evidence"
    decision = read(root / "development/decision.json")
    selected = read(study / "selection.lock.json")["selected"]
    summaries = read(study / "holdout/summary.json")
    alns = [r for r in summaries if r["method"] == "ALNS"]
    pairs = [r for r in read(study / "holdout/comparison.json") if r["method"] == "ALNS"]
    external = read(root / "external/verification.json")
    replay = read(root / "certified_replay/verification.json")
    browser = read(root / "ui/browser-checks.json")
    tests = read(root / "tests.json")
    write_json(root / "verification.json", {"preliminary_solutions": preliminary,
               "main_solutions": verified, "external_solutions": external["solutions"],
               "total_solutions": preliminary + verified + external["solutions"],
               "human_study_completed": False})
    base = "../" + root.relative_to(ROOT).as_posix()
    lines = ["# Báo cáo hoàn tất cải tiến và thực nghiệm", "",
             "Cập nhật: 20/09/2026. Báo cáo này thay thế trạng thái chưa chạy M5–M7 trong biên bản cũ.", "",
             "## Kết quả bàn giao", "",
             f"- M5: có baseline 30 nghiệm trước cải tiến, profile, và pilot 1/3/10 giây (9 nghiệm).",
             "- M6: đã đo 144 nghiệm trên tập phát triển, kiểm tra sai phân và quyết định không bật hai tùy chọn thử nghiệm.",
             f"- M7: **{verified} nghiệm** trong nghiên cứu chính, **{external['solutions']} nghiệm** trên {external['instances']} instance Kris; mọi nghiệm và bảng tổng hợp đã được kiểm tra lại.",
             f"- M8 tự động: kiểm tra trình duyệt luồng sử dụng và **{len(replay['cases'])} nghiệm exact có chứng nhận**, {sum(r['samples'] for r in replay['cases'])} mẫu đoạn chuyển động.",
             f"- Regression: **{tests['passed']} test passed**. Các thay đổi chưa được commit; hash source trong artifact nhận diện đúng mã đã chạy.",
             "- Sau các sửa cuối ở demo/report: chạy lại 22 test liên quan; bản export theo quy tắc Git đạt 128 test, 9 test tùy chọn skip vì thiếu dữ liệu nguồn. Đây là export working tree, không phải thay đổi đã xuất hiện trên remote.",
             "- M8 với người thật: **chưa thực hiện**. Không có căn cứ kết luận usability; phiếu sẵn ở [USER_STUDY.md](USER_STUDY.md).", "",
             "## Quyết định cải tiến", "",
             "ALNS là khung thuật toán có sẵn. Đóng góp của đồ án nằm ở mô hình tích hợp batching–routing–scheduling, các lựa chọn triển khai và bằng chứng thực nghiệm.", "",
             "Profile 30 đơn, 10 vòng: solve khoảng 0,821 s, repair 0,639 s, cost 0,553 s, check_plan 0,270 s (thời gian cộng dồn có lồng nhau, không cộng các cột này). Đây là phép đo có instrumentation.", "",
             "Evaluator gốc đã có cache batch/tuyến/prefix. Thử nghiệm mới cache validation theo lịch picker; không phải một bộ delta evaluator hoàn toàn mới.", "",
             "| Thử nghiệm | Kết quả trên development | Quyết định |",
             "|---|---|---|",
             f"| Cache validation | Plan/F bằng nhau ở số vòng cố định; thay đổi runtime trung vị {decision['median_runtime_improvement'] * 100:.2f}% (dương là nhanh hơn) | Không đạt ngưỡng nhanh hơn 5%; mặc định tắt |",
             f"| delay_chain | F cải thiện trung bình {decision['deadline_mean_F_improvement'] * 100:.3f}%; khoảng theo instance {min(decision['deadline_instance_improvements']) * 100:.3f}% đến {max(decision['deadline_instance_improvements']) * 100:.3f}% | Không đạt ngưỡng 1%; không thêm vào pool mặc định |", "",
             f"Quyết định đã khóa trước holdout: **{decision['selected']}**. Có chạy cả bản kết hợp; không chọn lại sau khi xem holdout. [Decision]({base}/development/decision.json), [profile]({base}/profile.json).", "",
             "Pilot 100 đơn cho trung vị 30/91,5/306 vòng ở 1/3/10 giây. Chọn 3 giây cho nghiên cứu chính; ngân sách gồm khởi tạo, không gồm graph/reference/validation. Runtime tổng vẫn được lưu riêng.", "",
             f"Tuning chọn preset **{selected['name']}** trên 6 instance × 2 seed × 3 preset. Holdout có 6 instance × 10 search seed cho mỗi phương pháp ngẫu nhiên; B0/B2 chạy một lần mỗi instance. Giữ bản mốc làm phương pháp chính nên không tạo một bản cải tiến giả để so trước/sau.", "",
             "## Holdout: ALNS so với các đối chứng", "",
             "F càng thấp càng tốt trên cùng instance/trọng số. Mỗi instance một phiếu sau trung bình seed; phần trăm dương là ALNS tốt hơn.", "",
             "| Đối chứng | Thắng | Hòa | Thua | Cải thiện F trung bình (%) |",
             "|---|---:|---:|---:|---:|"]
    for row in pairs:
        lines.append(f"| {row['reference']} | {row['win']} | {row['tie']} | {row['loss']} | {row['mean_improvement_pct']:.3f} |")
    vns = next(r for r in pairs if r["reference"] == "VNS")
    lns = next(r for r in pairs if r["reference"] == "LNS")
    lines += ["", f"ALNS so LNS chỉ thay đổi F trung bình {lns['mean_improvement_pct']:.3f}%; "
              f"so VNS là {vns['mean_improvement_pct']:.3f}%. "
              "Không có căn cứ kết luận ALNS luôn tốt nhất; kết quả so VNS phải được trình bày ngang với các kết quả có lợi. "
              "Chưa thực hiện kiểm định thống kê và không đổi cấu hình sau khi thấy bảng holdout."]
    lines += ["", "| Instance | F mean ± std | F median | Runtime tổng mean (s) | Vòng median | Có thích nghi |",
              "|---|---:|---:|---:|---:|---:|"]
    for row in alns:
        d = row["search_diagnostics"]
        lines.append(f"| {row['instance']} | {row['objective']['mean']:.5f} ± {row['objective']['std']:.5f} | {row['objective']['median']:.5f} | {row['total_seconds']['mean']:.3f} | {d['iterations_median']} | {d['adapted_runs']}/{row['runs']} |")
    lines += ["", f"Số run ALNS không hoàn thành vòng nào: **{sum(r['search_diagnostics']['zero_iteration_runs'] for r in alns)}/{sum(r['runs'] for r in alns)}**. Không loại ca bất lợi khỏi bảng.", "",
              "Seed 8401: single-block, độ nới hạn 0,15; seed 8402: multi-block, độ nới hạn 0,6. Hai yếu tố thay đổi cùng nhau, không được suy ra riêng tác động của layout hay deadline. Chỉ có sáu instance độc lập; không coi 60 seed-run là 60 bài toán độc lập.", "",
              "## Ablation, trọng số và optimality gap", "",
              "Đã chạy 10 biến thể × 2 instance × 10 search seed, ngân sách 1 giây; gồm adaptive/uniform, local lịch, 2-opt và từng destroy/repair operator. `no_2opt_compound` thay cả khởi tạo và decoder, không phải phép cô lập một bước 2-opt.", "",
              "| Biến thể so với full ALNS | Thắng | Hòa | Thua | Cải thiện F (%) |",
              "|---|---:|---:|---:|---:|"]
    ablation_rows = read(study / "ablation/comparison.json")
    for row in ablation_rows:
        lines.append(f"| {row['method']} | {row['win']} | {row['tie']} | {row['loss']} | {row['mean_improvement_pct']:.3f} |")
    ablated = {r["method"]: r for r in ablation_rows}
    lines += ["", f"Bỏ local search lịch thay đổi F {ablated['no_schedule_local']['mean_improvement_pct']:.3f}%; "
              f"bỏ 2-opt theo phép ablation kết hợp thay đổi F {ablated['no_2opt_compound']['mean_improvement_pct']:.3f}%. "
              "Giữ các thành phần này trong bản chính. Chỉ có hai instance ablation; không chọn lại pool toán tử từ một biến thể có lợi ở vài ca."]
    lines += ["", "Sensitivity gồm bốn vector trọng số trên 10/30/100 đơn × 3 seed. So distance/makespan/tardiness/late orders, không xếp hạng F giữa các vector trọng số.", "",
              "| Phương pháp | Gap trung bình (%) | Gap lớn nhất (%) | Số instance certified |",
              "|---|---:|---:|---:|"]
    gaps = read(study / "exact/summary.json")
    for method in ("B0", "B2", "B3", "LNS", "ALNS", "VNS"):
        values = [r["gap_pct"] for r in gaps if r["method"] == method and r["gap_pct"] is not None]
        lines.append(f"| {method} | {statistics.mean(values):.3f} | {max(values):.3f} | {len(values)} |" if values else f"| {method} | N/A | N/A | 0 |")
    lines += ["", "Oracle chỉ áp dụng sáu bài 4–6 đơn; không ngoại suy chứng nhận tối ưu sang 100 đơn. Có thêm so sánh NN/2-opt/S-Shape/exact trên cùng plan B2 để tách ảnh hưởng decoder.", "",
              f"[Báo cáo chi tiết, gồm trade-off F/đơn trễ và bảng Pareto]({base}/study/REPORT.md).", "",
              "## Kiểm tra trên dữ liệu ngoài generator", "",
              "Chọn trước hai tên file đầu theo thứ tự chữ ở mỗi nhóm 6/12/18 đơn, dùng seed 21/22/23 và cùng cấu hình được chọn trên tuning. Hash file nguồn được đối chiếu với catalog; giữ nguyên đơn, due dates và đơn vị nguồn.", "",
              "| Đối chứng | ALNS thắng | Hòa | Thua | Cải thiện F (%) |",
              "|---|---:|---:|---:|---:|"]
    for row in read(root / "external/benchmark/comparison.json"):
        if row["method"] == "ALNS":
            lines.append(f"| {row['reference']} | {row['win']} | {row['tie']} | {row['loss']} | {row['mean_improvement_pct']:.3f} |")
    lines += ["", "Đây là kiểm tra chuyển dữ liệu sang mục tiêu hạn mềm của project, không tái lập JOBPRSP-D hạn cứng và không so với best-known gốc. Chỉ chạy sáu instance, ba seed; không tuyên bố chạy toàn catalog. Không suy ra giấy phép phân phối từ việc tải được dữ liệu.", "",
              f"[Danh sách nguồn và cấu hình đã khóa]({base}/external/external.lock.json).", "",
              "## Demo và chất lượng phần mềm", "",
              f"Kiểm tra trình duyệt hoàn thành {len(browser['checks'])} nhóm tác vụ, không có page error: " + "; ".join(browser["checks"]) + ".", "",
              "Bài kiểm tra phát lại dùng đúng HTML gửi vào Streamlit, chạy JavaScript trong Edge và so vị trí/tải/trạng thái ở giữa từng segment với timeline của nghiệm certified. Play/pause/reset/tua cuối/zoom đều được thực thi. Đây là kiểm thử chức năng, không phải khảo sát người dùng hoặc đo FPS.", "",
              "Kiểm tra thực tế còn phát hiện và sửa: thanh tua bước cố định không tới đúng makespan, sai số dấu phẩy động khiến trạng thái chưa chuyển hoàn tất ở cuối ca, và nhãn thời gian chồng nút ở màn hình hẹp. Đã kiểm tra lại thanh điều khiển ở 1100 px và 390 px, không tràn vùng chứa.", "",
              "## Hướng phát triển tốt nhất sau đợt này", "",
              "Giữ ALNS hiện tại với cấu hình đã khóa làm bản nghiên cứu; trình bày riêng kết quả so LNS/VNS và chấp nhận ca thua. Không mở rộng thêm thuật toán chỉ để tìm một bảng thắng.", "",
              "Nếu tiếp tục nghiên cứu: tăng số instance độc lập, thiết kế factorial tách layout và deadline; profile repair/insertion trên bài lớn trước khi làm delta evaluator. Cache validation vừa thử không có lợi, không nên bật mặc định. Trước mọi sửa sau khi đã xem holdout, cần tập xác nhận mới.", "",
              "Nếu ưu tiên hoàn thiện đồ án: thực hiện phiếu ba người thật, bổ sung quan sát và sửa đúng vấn đề họ gặp. Các mở rộng congestion, online orders, picker không đồng nhất thuộc bài toán mới.", "",
              "## Tái lập và artifact", "",
              "```powershell",
              "python -m pytest -q -p no:cacheprovider",
              "python scripts/run_development.py --output results/dev_moi",
              "python scripts/run_research.py all --protocol configs/research_completion.json --output results/study_moi",
              "python scripts/run_external_check.py --study results/study_moi --output results/external_moi",
              "python scripts/check_certified_replay.py --study results/study_moi --output results/replay_moi",
              "```", "",
              "Dùng thư mục mới; runner từ chối ghi đè. Các benchmark phải chạy tuần tự; kết quả giới hạn wall-clock có thể đổi theo tải máy. Cùng seed và số vòng cố định là chế độ kiểm tra tái lập quyết định thuật toán.", "",
              f"- [Protocol và source snapshot]({base}/study/protocol.lock.json), SHA-256 `{digest(study / 'protocol.lock.json')}`.",
              f"- [Xác minh nghiên cứu]({base}/study/verification.json).",
              f"- [Archive nghiên cứu đã rà soát]({base}/study_reviewed.zip), checksum [SHA-256]({base}/study_reviewed.zip.sha256).",
              f"- [Hiệu chỉnh câu mô tả ngân sách]({base}/study/report_correction.json): sửa nhãn 2 giây còn sót thành ngân sách đã khóa 3 giây; không đổi raw/config/thuật toán. Bản nguồn chạy thực nghiệm và archive gốc vẫn được giữ.",
              "- Để kiểm tra lại đợt đã khóa sau khi mã working tree thay đổi, chạy `python results/completion_20260919/study/source/scripts/run_research.py verify --output results/completion_20260919/study`.",
              f"- [Kiểm tra browser]({base}/ui/browser-checks.json), [certified replay]({base}/certified_replay/verification.json).", ""]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(args.report)


if __name__ == "__main__":
    main()
