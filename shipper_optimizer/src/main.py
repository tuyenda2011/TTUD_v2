"""
🚚 SHIPPER ROUTE OPTIMIZER - CLI & Core Orchestrator
Optimizes delivery routes in Hanoi using Dijkstra, Nearest Neighbor, Clarke-Wright, and 2-Opt.
"""

from __future__ import annotations
import os
import sys
import argparse
from typing import List, Optional

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.models.location import Location
from src.data.loader import load_deliveries, build_distance_matrix, get_depot_index, get_default_csv_path
from src.algorithms.dijkstra import Dijkstra
from src.algorithms.nearest_neighbor import NearestNeighbor
from src.algorithms.clarke_wright import ClarkeWrightSavings
from src.algorithms.two_opt import TwoOpt
from src.algorithms.benchmark import BenchmarkEngine
from src.visualization.map_viz import generate_interactive_map, plot_benchmark_chart


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     🚚 SHIPPER ROUTE OPTIMIZER                               ║
║           Hệ thống Tối ưu hóa Lộ trình Giao hàng Thông minh tại Hà Nội       ║
║     Thuật toán: Dijkstra | Nearest Neighbor (TSP) | Clarke-Wright + 2-Opt     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_route_details(solution):
    """Print clean step-by-step route breakdown."""
    print(f"\n────────────────────────────────────────────────────────────────────────")
    print(f"🛣️  KẾT QUẢ THUẬT TOÁN: {solution.algorithm_name.upper()}")
    print(f"   • Tổng quãng đường: {solution.total_distance_km:.2f} km")
    print(f"   • Số phương tiện:    {solution.num_vehicles} xe")
    print(f"   • Tổng khối lượng:   {solution.total_demand_kg:.1f} kg")
    print(f"   • Thời gian tính:    {solution.execution_time_sec * 1000:.2f} ms")
    print(f"   • Ước tính tiền xăng: {int(solution.fuel_cost_vnd):,} VND / chuyến")
    print(f"────────────────────────────────────────────────────────────────────────")

    for r in solution.routes:
        print(f"\n🚗 TUYẾN XE #{r.vehicle_id}:")
        path_str = " ➔ ".join(r.node_ids)
        print(f"   Lộ trình ({len(r.node_ids)} điểm): {path_str}")
        print(f"   Chi tiết: {r.total_distance_km:.2f} km | {r.num_deliveries} đơn hàng | Tải trọng: {r.total_demand_kg:.1f} kg | Ước tính: {int(r.estimated_travel_time_min)} phút")
        
        # Print first few stops as preview
        stops_preview = ", ".join(r.node_names[1:-1][:4])
        if len(r.node_names) > 6:
            stops_preview += f", ... (+{len(r.node_names)-6} điểm khác)"
        print(f"   Điểm giao chính: {stops_preview}")


def run_benchmark_workflow(csv_path: str, capacity: float, output_dir: str):
    """Execute complete benchmark suite and save artifacts."""
    locations = load_deliveries(csv_path)
    dist_matrix = build_distance_matrix(locations)
    depot_idx = get_depot_index(locations)

    depot = locations[depot_idx]
    print(f"📦 Dataset: {len(locations)-1} điểm giao hàng tại Hà Nội")
    print(f"🏭 Điểm tập kết (Depot): {depot.name} ({depot.district}) [{depot.lat:.4f}, {depot.lng:.4f}]")
    print(f"🚛 Sức chứa mỗi xe (Capacity): {capacity} kg")

    engine = BenchmarkEngine(
        locations=locations,
        distance_matrix=dist_matrix,
        vehicle_capacity_kg=capacity,
        depot_idx=depot_idx
    )
    solutions = engine.run_all()

    print("\n" + "="*80)
    print("📊 BẢNG TỔNG HỢP SO SÁNH HIỆU NĂNG THUẬT TOÁN")
    print("="*80)
    print(engine.generate_summary_table())

    savings = engine.calculate_cost_savings()
    if savings:
        print("\n💰 PHÂN TÍCH TIẾT KIỆM CHI PHÍ & NHIÊN LIỆU:")
        print(f"   [1] Tối ưu hóa TSP (2-Opt vs Nearest Neighbor thô):")
        print(f"       • Quãng đường rút ngắn:    {savings['tsp_saved_km']} km (-{savings['tsp_saved_pct']}%)")
        print(f"       • Tiết kiệm ước tính/năm: {savings['tsp_annual_saved_vnd']:,} VND (365 chuyến/năm)")
        print(f"   [2] Tối ưu hóa VRP Đa phương tiện (Clarke-Wright+2Opt vs Tuyến rời):")
        print(f"       • Tổng quãng đường tuyến rời: {savings['naive_separate_routes_km']} km")
        print(f"       • Quãng đường VRP tối ưu:     {savings['vrp_optimized_km']} km")
        print(f"       • Quãng đường tiết kiệm:     {savings['vrp_saved_km']} km (-{savings['vrp_saved_pct']}%)")
        print(f"       • Tiền xăng tiết kiệm/năm:    {savings['vrp_annual_saved_vnd']:,} VND (365 ngày)")

    # Save artifacts
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "benchmark_results.json")
    engine.export_results_json(json_path)
    print(f"\n💾 Đã lưu kết quả chi tiết (JSON): {json_path}")

    # Generate Map
    best_sol = solutions.get("Clarke-Wright + 2-Opt (VRP)", list(solutions.values())[-1])
    map_path = os.path.join(output_dir, "hanoi_routes.html")
    generate_interactive_map(locations, best_sol, output_html_path=map_path)
    print(f"🗺️  Đã xuất bản đồ lộ trình tương tác: {map_path}")

    # Generate Chart
    chart_path = os.path.join(output_dir, "benchmark_chart.png")
    plot_benchmark_chart(solutions, output_png_path=chart_path)
    print(f"📈 Đã xuất biểu đồ so sánh: {chart_path}")
    print("="*80 + "\n")


def interactive_menu(csv_path: str, capacity: float, output_dir: str):
    """Interactive CLI menu loop."""
    locations = load_deliveries(csv_path)
    dist_matrix = build_distance_matrix(locations)
    depot_idx = get_depot_index(locations)
    two_opt = TwoOpt(dist_matrix)

    while True:
        print_banner()
        print(f"📂 Dataset hiện tại: {csv_path} ({len(locations)} điểm)")
        print(f"📦 Sức chứa xe:     {capacity} kg\n")
        print("Vui lòng chọn chức năng:")
        print("  [1] Chạy tất cả thuật toán & Xuất báo cáo Benchmark")
        print("  [2] Chạy Dijkstra (Ma trận khoảng cách & Đường đi ngắn nhất)")
        print("  [3] Chạy Nearest Neighbor (TSP 1 xe) & Cải tiến 2-Opt")
        print("  [4] Chạy Clarke-Wright Savings (VRP nhiều xe) & 2-Opt Hybrid")
        print("  [5] Xuất Bản đồ Tương tác Folium HTML")
        print("  [6] Thay đổi Sức chứa Xe (Capacity)")
        print("  [0] Thoát chương trình")
        
        choice = input("\n👉 Nhập lựa chọn của bạn [0-6]: ").strip()

        if choice == "1":
            run_benchmark_workflow(csv_path, capacity, output_dir)
            input("\nNhấn Enter để tiếp tục...")
        elif choice == "2":
            dijkstra = Dijkstra(locations, dist_matrix)
            stats = dijkstra.get_summary_statistics()
            print("\n" + "="*60)
            print("🛣️  KẾT QUẢ DIJKSTRA & PHÂN TÍCH MẠNG LƯỚI:")
            print(f"   • Số đỉnh: {stats['num_nodes']} (1 Kho + {stats['num_nodes']-1} Điểm giao)")
            print(f"   • Khoảng cách trung bình giữa 2 điểm: {stats['avg_distance_km']} km")
            print(f"   • Khoảng cách trung bình từ Kho đến các điểm: {stats['avg_distance_from_depot_km']} km")
            print(f"   • Cặp điểm xa nhất: {stats['max_pair'][0]} ↔ {stats['max_pair'][1]} ({stats['max_distance_km']} km)")
            print(f"     ({stats['max_pair_names'][0]} ➔ {stats['max_pair_names'][1]})")
            
            # Interactive shortest path query
            print("\n🔍 Thử tra cứu đường đi ngắn nhất giữa 2 điểm:")
            src = input(f"   Nhập ID nguồn (vd D0, D1...): ").strip().upper() or "D0"
            dst = input(f"   Nhập ID đích (vd D15, D30...): ").strip().upper() or "D30"
            
            src_idx = next((i for i, l in enumerate(locations) if l.id == src), 0)
            dst_idx = next((i for i, l in enumerate(locations) if l.id == dst), len(locations)-1)
            
            d_val, path = dijkstra.shortest_path(src_idx, dst_idx)
            path_names = " ➔ ".join([locations[k].id for k in path])
            print(f"   ✓ Khoảng cách ngắn nhất: {d_val:.2f} km")
            print(f"   ✓ Đường đi: {path_names}")
            print("="*60)
            input("\nNhấn Enter để tiếp tục...")
        elif choice == "3":
            nn_solver = NearestNeighbor(locations, dist_matrix, depot_idx=depot_idx)
            sol_nn = nn_solver.solve()
            print_route_details(sol_nn)
            
            sol_opt = two_opt.optimize_solution(sol_nn, locations)
            print_route_details(sol_opt)
            input("\nNhấn Enter để tiếp tục...")
        elif choice == "4":
            cw = ClarkeWrightSavings(locations, dist_matrix, vehicle_capacity=capacity, depot_idx=depot_idx)
            sol_cw = cw.solve()
            print_route_details(sol_cw)

            sol_hybrid = two_opt.optimize_solution(sol_cw, locations)
            print_route_details(sol_hybrid)
            input("\nNhấn Enter để tiếp tục...")
        elif choice == "5":
            cw = ClarkeWrightSavings(locations, dist_matrix, vehicle_capacity=capacity, depot_idx=depot_idx)
            sol_cw = cw.solve()
            sol_hybrid = two_opt.optimize_solution(sol_cw, locations)
            
            os.makedirs(output_dir, exist_ok=True)
            map_path = os.path.join(output_dir, "hanoi_routes.html")
            generate_interactive_map(locations, sol_hybrid, output_html_path=map_path)
            print(f"\n🗺️  Đã tạo bản đồ tương tác thành công tại:\n   👉 {os.path.abspath(map_path)}")
            input("\nNhấn Enter để tiếp tục...")
        elif choice == "6":
            try:
                new_cap = float(input(f"Nhập sức chứa xe mới (kg) [Hiện tại: {capacity}]: ").strip())
                if new_cap > 0:
                    capacity = new_cap
                    print(f"✓ Đã cập nhật sức chứa: {capacity} kg")
            except ValueError:
                print("⚠️ Giá trị không hợp lệ.")
            input("\nNhấn Enter để tiếp tục...")
        elif choice == "0":
            print("\n👋 Cảm ơn bạn đã sử dụng Shipper Route Optimizer! Tạm biệt.")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ, vui lòng chọn lại.")


def main():
    parser = argparse.ArgumentParser(description="Shipper Route Optimizer CLI")
    parser.add_argument("--benchmark", action="store_true", help="Run full benchmark suite")
    parser.add_argument("--algorithm", type=str, choices=["all", "dijkstra", "nn", "cw", "hybrid"], default="all")
    parser.add_argument("--dataset", type=str, default=None, help="Path to delivery CSV dataset")
    parser.add_argument("--capacity", type=float, default=200.0, help="Vehicle load capacity in kg")
    parser.add_argument("--output-dir", type=str, default="output", help="Directory to save output files")
    parser.add_argument("--no-interactive", action="store_true", help="Run without interactive prompt")

    args = parser.parse_args()
    csv_path = args.dataset or get_default_csv_path()

    if args.benchmark or args.no_interactive:
        print_banner()
        run_benchmark_workflow(csv_path, args.capacity, args.output_dir)
    else:
        interactive_menu(csv_path, args.capacity, args.output_dir)


if __name__ == "__main__":
    main()
