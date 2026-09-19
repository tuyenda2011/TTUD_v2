"""Optional, local-only Matplotlib views of physical routes and picker schedules."""
from itertools import pairwise

from .units import unit_label

COLORS = ["#176b5b", "#2864ad", "#ad661e", "#80539a", "#b43c57", "#197e91", "#637a28", "#775b46"]


def warehouse_figure(instance, result, picker=None, batch_id=None):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(10, 6.5), layout="constrained")
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    nodes = {n.id: n for n in instance.nodes}
    layout = instance.metadata.get("layout", {})
    if layout.get("type") == "single_block":
        aisles = layout.get("aisles", [])
        for left, right in pairwise(aisles):
            a, b = nodes[left[0]], nodes[right[0]]
            top = nodes[left[-1]].y
            if b.x - a.x > 3 and top - a.y > 4:
                ax.add_patch(Rectangle((a.x + 1.4, a.y + 2), b.x - a.x - 2.8, top - a.y - 4, facecolor="#e2e8f0", edgecolor="#cbd5e1", linewidth=.7, zorder=0))
    for edge in instance.edges:
        a, b = nodes[edge.source], nodes[edge.target]
        ax.plot([a.x, b.x], [a.y, b.y], color="#cbd5e1", linewidth=2, zorder=1)
    product_nodes = {p.location for p in instance.products}
    ax.scatter([nodes[n].x for n in product_nodes], [nodes[n].y for n in product_nodes], s=16, color="#94a3b8", zorder=2)
    used = set()
    for batch in result["batches"]:
        if picker is not None and batch["picker"] != picker:
            continue
        if batch_id is not None and batch["id"] != batch_id:
            continue
        color = COLORS[(batch["picker"] - 1) % len(COLORS)]
        coords = [nodes[n] for n in batch["walk"]]
        label = f"Nhân viên {batch['picker']}" if batch["picker"] not in used else None
        ax.plot([p.x for p in coords], [p.y for p in coords], color=color, alpha=.9, linewidth=2.5, label=label, zorder=3)
        used.add(batch["picker"])
        for seq, stop in enumerate(batch["stops"][1:-1], start=1):
            node = nodes[stop]
            ax.scatter([node.x], [node.y], s=48, color=color, edgecolor="white", linewidth=.8, zorder=4)
            if batch_id:
                ax.annotate(str(seq), (node.x, node.y), xytext=(7, 5), textcoords="offset points",
                            color=color, fontsize=9, weight="bold",
                            bbox={"boxstyle": "round,pad=.15", "facecolor": "white", "edgecolor": "none", "alpha": .9})
    depot = nodes[instance.depot]
    ax.scatter([depot.x], [depot.y], s=180, marker="s", color="#0f172a", edgecolor="white", zorder=5)
    ax.annotate("Xuất phát", (depot.x, depot.y), xytext=(8, -16), textcoords="offset points", weight="bold", color="#0f172a")
    ax.set(title=f"Tuyến chuyến {batch_id}" if batch_id else "Các tuyến được chọn",
           xlabel="Tọa độ x", ylabel="Tọa độ y", aspect="equal")
    ax.margins(.12)
    if used:
        ax.legend(loc="upper center", bbox_to_anchor=(.5, -.12), ncol=min(4, len(used)), frameon=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors="#64748b")
    return fig


def gantt_figure(instance, result):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, max(2.4, instance.operations.pickers * .6)), layout="constrained")
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    for batch in result["batches"]:
        picker = batch["picker"]
        color = COLORS[(picker - 1) % len(COLORS)]
        late = batch["tardiness"] > 1e-9
        ax.barh(picker, batch["duration"], left=batch["start"], height=.55, color=color, alpha=.85, edgecolor="#dc2626" if late else "white", linewidth=2 if late else .8)
        if batch["duration"] > max(result["metrics"]["makespan"], 1) * .055:
            ax.text(batch["start"] + batch["duration"] / 2, picker, batch["id"].split("-")[-1], ha="center", va="center", color="white", fontsize=8)
    ax.set_yticks(range(1, instance.operations.pickers + 1), [f"Nhân viên {i}" for i in range(1, instance.operations.pickers + 1)])
    ax.invert_yaxis()
    ax.set_xlabel(f"Thời gian từ lúc bắt đầu ({unit_label(instance, 'time')})")
    ax.set_title("Lịch các chuyến lấy hàng")
    ax.set_xlim(0, max(1., result["metrics"]["makespan"]) * 1.03)
    ax.grid(axis="x", color="#cbd5e1", alpha=.4)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig


def convergence_figure(result):
    import matplotlib.pyplot as plt
    trace = result.get("search", {}).get("trace", [])
    fig, ax = plt.subplots(figsize=(8, 3), layout="constrained")
    if trace:
        ax.step([row["seconds"] for row in trace], [row["objective"] for row in trace], where="post", color="#2563eb")
    ax.set(xlabel="Thời gian tối ưu, gồm khởi tạo (giây)", ylabel="Điểm F tốt nhất", title="Quá trình cải thiện phương án")
    ax.grid(alpha=.2)
    return fig
