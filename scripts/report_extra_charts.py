"""Supplementary report figures generated exclusively from verified runs."""
import json
import textwrap

from src.models import read_instance
from src.plots import gantt_figure, warehouse_figure
from src.units import unit_label


def extra_charts(verified, output, labels):
    import matplotlib.pyplot as plt

    paths = []
    charts = output / "charts"
    charts.mkdir(exist_ok=True)
    instances = {i.name: i for i in (read_instance(p) for p in sorted((verified["root"] / "instances").glob("*.json")))}
    names = sorted(instances)
    methods = [m for m in ("B0", "B2", "LNS", "ALNS", "VNS") if any(r["method"] == m for r in verified["summaries"])]
    by = {(r["instance"], r["method"]): r for r in verified["summaries"]}
    colors = {"B0": "#d97706", "B2": "#15803d", "LNS": "#dc2626", "ALNS": "#2563eb", "VNS": "#7c3aed"}

    def save(fig, stem):
        for ext in ("png", "pdf"):
            path = charts / f"{stem}.{ext}"
            fig.savefig(path, dpi=300, facecolor="white")
            paths.append(path.relative_to(output).as_posix())
        plt.close(fig)

    for start in range(0, len(names), 5):
        page = names[start:start + 5]
        suffix = "" if start == 0 else f"_{start // 5 + 1:02d}"
        # Only combine physical metrics when the declared units match.
        units = {tuple(unit_label(instances[n], k) for k in ("distance", "time")) for n in page}
        if len(units) != 1:
            continue
        distance, time = next(iter(units))
        fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.6), layout="constrained")
        for ax, metric, title in zip(axes.flat, ("distance", "makespan", "tardiness", "late_orders"),
                                     (f"Quãng đường ({distance})", f"Thời gian hoàn tất ({time})", f"Tổng thời gian trễ ({time})", "Số đơn trễ")):
            for j, method in enumerate(methods):
                rows = [by.get((n, method)) for n in page]
                ax.errorbar([r[metric]["mean"] if r else float("nan") for r in rows],
                            [i + (j - (len(methods) - 1) / 2) * .13 for i in range(len(page))],
                            xerr=[r[metric]["std"] if r else 0 for r in rows], fmt="o", markersize=4,
                            capsize=2, color=colors[method], label=method)
            ax.set_yticks(range(len(page)), [f"M{start+i+1}" for i in range(len(page))])
            ax.set_ylim(len(page)-.5, -.5)
            ax.set_title(title, fontsize=10, fontweight="bold")
            ax.grid(axis="x", alpha=.2)
            ax.spines[["top", "right"]].set_visible(False)
        fig.suptitle("Các chỉ tiêu vận hành · Trung bình ± độ lệch chuẩn", fontsize=12)
        mapping = " | ".join(f"M{start+i+1}: {instances[n].metadata.get('scenario', {}).get('name', n).split(' (')[0]}" for i, n in enumerate(page))
        fig.set_size_inches(7.2, 7.2)
        fig.supxlabel(textwrap.fill(mapping, 95), fontsize=8)
        axes[0, 0].legend(ncol=3, fontsize=8, loc="best")
        save(fig, "operational_metrics" + suffix)

        fig, ax = plt.subplots(figsize=(7.2, 4.5), layout="constrained")
        for j, method in enumerate(methods):
            rows = [by.get((n, method)) for n in page]
            ax.errorbar([r["total_seconds"]["mean"] if r else float("nan") for r in rows],
                        [i + (j - (len(methods)-1)/2)*.13 for i in range(len(page))],
                        xerr=[r["total_seconds"]["std"] if r else 0 for r in rows],
                        fmt="o", capsize=2, markersize=5, color=colors[method], label=method)
        ax.set_yticks(range(len(page)), [labels.get(n, n) for n in page], fontsize=8)
        ax.set_ylim(len(page)-.5, -.5)
        ax.set_xlabel("Runtime tổng (giây) · Trung bình ± độ lệch chuẩn")
        ax.set_title("Chi phí tính toán theo bài toán", fontweight="bold")
        ax.legend(ncol=5, fontsize=9, loc="upper center", bbox_to_anchor=(.5, 1.0))
        ax.grid(axis="x", alpha=.2)
        ax.spines[["top", "right"]].set_visible(False)
        save(fig, "runtime_by_instance" + suffix)

    # Deterministic illustrative selection; never select by algorithm outcome.
    name = names[0]
    runs = [r for r in verified["results"] if r["instance"] == name and r["method"] in ("ALNS", "VNS")]
    selected = {}
    for r in sorted(runs, key=lambda r: r["search"]["seed"]):
        selected.setdefault(r["method"], r)
    limit = max((r["metrics"]["makespan"] for r in selected.values()), default=1)
    for method, run in selected.items():
        fig = gantt_figure(instances[name], run)
        fig.set_size_inches(7.2, 3.4)
        fig.axes[0].set_xlim(0, limit * 1.03)
        fig.axes[0].set_title(f"Lịch làm việc · {method} · M1 · seed {run['search']['seed']}")
        save(fig, f"schedule_example_{method}")
        # Display one complete picker route set, avoiding an unreadable overlay.
        picker = min((b["picker"] for b in run["batches"]), default=1)
        fig = warehouse_figure(instances[name], run, picker=picker)
        fig.set_size_inches(7.2, 5.2)
        fig.axes[0].set_title(f"Tuyến nhân viên {picker} · {method} · M1 · seed {run['search']['seed']}")
        save(fig, f"routes_example_{method}")
    notes = ["# Hướng dẫn dùng hình bổ sung", "", "## Mã bài toán", ""]
    notes += [f"- M{i+1}: {labels.get(n, n).replace(chr(10), ' · ')} (`{n}`)." for i, n in enumerate(names)]
    notes += ["", "Thanh sai số là độ lệch chuẩn qua search seed, không phải khoảng tin cậy. B0/B2 tất định chạy một lần.",
              "Trong lịch: B1/B2 là số chuyến của nhân viên, không phải tên thuật toán. Viền đỏ đánh dấu chuyến có đơn trễ.",
              "Runtime là total_seconds, bao gồm các chi phí ngoài ngân sách tìm kiếm; không coi runtime thấp là chất lượng nghiệm tốt hơn.",
              "Hình lịch/tuyến chọn bài đầu theo tên file và seed nhỏ nhất cho mỗi thuật toán, không chọn theo thắng/thua. Hai lịch dùng cùng trục thời gian. Tuyến chỉ minh họa nhân viên có mã nhỏ nhất của từng nghiệm; các đơn được phân công có thể khác nhau.",
              "Chỉ tiêu vận hành dùng đơn vị gốc khai báo trong dữ liệu; không áp dụng quy đổi minh họa của demo."]
    (output / "CHART_GUIDE.md").write_text("\n".join(notes), encoding="utf-8")
    (charts / "example_selection.json").write_text(json.dumps({"instance": name, "seeds": {m:r["search"]["seed"] for m,r in selected.items()}}, indent=2), encoding="utf-8")
    return paths
