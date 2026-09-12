"""
Map and Chart Visualization utilities using Folium and Matplotlib.
Generates interactive HTML maps with multi-vehicle routes and benchmark charts.
"""

from __future__ import annotations
import os
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    import folium
    from folium import plugins
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False

from src.models.location import Location
from src.models.route import VRPSolution, Route


ROUTE_COLORS = [
    "#E63946",  # Vibrant Red (Vehicle 1)
    "#2A9D8F",  # Deep Teal (Vehicle 2)
    "#457B9D",  # Steel Blue (Vehicle 3)
    "#F4A261",  # Sandy Orange (Vehicle 4)
    "#9B5DE5",  # Purple (Vehicle 5)
    "#00BBF9",  # Sky Blue (Vehicle 6)
    "#F15BB5",  # Pink (Vehicle 7)
    "#00F5D4"   # Neon Mint (Vehicle 8)
]

# Traffic zone colors
TRAFFIC_COLORS = {
    "none": "#16a34a",   # Green (depot)
    "low": "#22c55e",     # Light green
    "medium": "#f59e0b",  # Orange
    "high": "#ef4444"     # Red
}

TRAFFIC_ICONS = {
    "none": "home",
    "low": "truck",
    "medium": "car",
    "high": "warning"
}


def generate_interactive_map(
    locations: List[Location],
    solution: VRPSolution,
    output_html_path: str = "output/hanoi_routes.html",
    map_title: Optional[str] = None,
    route_geometries: Optional[Dict] = None  # {(i,j): [[lat,lng], ...]}
) -> str:
    """
    Generate rich interactive Folium map showing depot, deliveries and vehicle routes.

    Args:
        route_geometries: Dict mapping (i,j) to list of [lat, lng] coordinates

    Returns:
        Absolute path to generated HTML map.
    """
    if not FOLIUM_AVAILABLE:
        raise ImportError("Folium is not installed. Please install folium.")

    os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)

    depot = next((loc for loc in locations if loc.is_depot), locations[0])
    center_lat = sum(loc.lat for loc in locations) / len(locations)
    center_lng = sum(loc.lng for loc in locations) / len(locations)

    # Initialize Folium Map with full width/height
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles=None,  # We'll add custom tile layer
        width='100%',
        height='100%'
    )

    # Use OpenStreetMap tiles directly (no API key needed)
    folium.TileLayer(
        tiles='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='© OpenStreetMap contributors',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)

    # Alternative tile layer for better visualization
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        attr='© OpenStreetMap contributors, Tiles HOT',
        name='OSM Humanitarian',
        overlay=False,
        control=True
    ).add_to(m)

    # Add fullscreen button
    from folium import plugins
    plugins.Fullscreen().add_to(m)

    title_text = map_title or f"Shipper Route Optimizer - {solution.algorithm_name}"

    # Add title banner with higher z-index
    title_html = f'''
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); width: 500px; z-index: 9999;
                background: linear-gradient(135deg, #1e40af, #3b82f6); border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                padding: 15px 20px; font-family: Arial, sans-serif; color: white;">
        <h4 style="margin: 0 0 8px 0; font-size: 16px;">{title_text}</h4>
        <div style="font-size: 13px; display: flex; gap: 20px;">
            <span><b>Khoảng cách:</b> {solution.total_distance_km:.2f} km</span>
            <span><b>Xe:</b> {solution.num_vehicles}</span>
            <span><b>Điểm:</b> {solution.total_deliveries}</span>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Add Depot Marker
    depot_popup = f"""
    <div style="font-family: Arial; min-width: 160px;">
        <h4 style="margin:0; color: #16a34a;">🏭 {depot.name} (Depot)</h4>
        <p style="margin: 4px 0 0 0; font-size: 12px;"><b>Địa chỉ:</b> {depot.district}<br>
        <b>Tọa độ:</b> {depot.lat:.4f}, {depot.lng:.4f}</p>
    </div>
    """
    folium.Marker(
        location=[depot.lat, depot.lng],
        popup=folium.Popup(depot_popup, max_width=250),
        tooltip=f"Depot: {depot.name}",
        icon=folium.Icon(color="green", icon="home", prefix="fa")
    ).add_to(m)

    # Dictionary for fast location lookup
    loc_by_id = {loc.id: loc for loc in locations}

    # Draw each vehicle route
    for r_idx, route in enumerate(solution.routes):
        color = ROUTE_COLORS[r_idx % len(ROUTE_COLORS)]

        # Check if we have real route geometry
        if route_geometries:
            # Draw real road path using geometry segments between consecutive nodes
            loc_ids = route.node_ids  # e.g., [D0, D1, D3, D5, D0]
            route_tooltip = f"Tuyến Xe #{route.vehicle_id}: {route.total_distance_km:.2f} km (đường thật)"
            has_real_segments = False

            # For each consecutive pair, draw the real road segment
            for k in range(len(loc_ids) - 1):
                # Find indices in locations list
                try:
                    idx_from = next(i for i, l in enumerate(locations) if l.id == loc_ids[k])
                    idx_to = next(i for i, l in enumerate(locations) if l.id == loc_ids[k + 1])

                    # Look up real geometry
                    seg = route_geometries.get((idx_from, idx_to))

                    if seg:
                        folium.PolyLine(
                            locations=seg,
                            color=color,
                            weight=5,
                            opacity=0.8,
                            tooltip=route_tooltip
                        ).add_to(m)
                        has_real_segments = True
                    else:
                        # Fallback: straight line
                        loc_from = loc_by_id[loc_ids[k]]
                        loc_to = loc_by_id[loc_ids[k + 1]]
                        folium.PolyLine(
                            locations=[[loc_from.lat, loc_from.lng], [loc_to.lat, loc_to.lng]],
                            color=color,
                            weight=4,
                            opacity=0.85,
                            tooltip=route_tooltip
                        ).add_to(m)
                except StopIteration:
                    continue
        else:
            # Fallback: draw straight lines between all points
            coords: List[List[float]] = []
            for stop_num, loc_id in enumerate(route.node_ids):
                loc = loc_by_id.get(loc_id)
                if not loc:
                    continue
                coords.append([loc.lat, loc.lng])

            if coords:
                route_tooltip = f"Tuyến Xe #{route.vehicle_id}: {route.total_distance_km:.2f} km"
                folium.PolyLine(
                    locations=coords,
                    color=color,
                    weight=4,
                    opacity=0.85,
                    tooltip=route_tooltip
                ).add_to(m)

        # Draw markers for each stop (always draw these)
        for stop_num, loc_id in enumerate(route.node_ids):
            loc = loc_by_id.get(loc_id)
            if not loc:
                continue

            # If not depot, draw numbered marker for stop
            if not loc.is_depot:
                # Get traffic zone color
                tz = getattr(loc, 'traffic_zone', 'low')
                tz_color = TRAFFIC_COLORS.get(tz, TRAFFIC_COLORS['low'])

                popup_content = f"""
                <div style="font-family: Arial; min-width: 200px;">
                    <h5 style="margin:0; color:{color};">#{stop_num} {loc.id}: {loc.name}</h5>
                    <p style="margin:4px 0; font-size:12px;">
                        <b>Quận:</b> {loc.district}<br>
                        <b>Xe:</b> #{route.vehicle_id} | <b>Thứ tự:</b> #{stop_num}<br>
                        <b>Khối lượng:</b> {loc.demand_kg} kg<br>
                        <b>Kẹt xe:</b> <span style="color:{tz_color}; font-weight:bold;">{tz.upper()}</span>
                    </p>
                </div>
                """
                folium.CircleMarker(
                    location=[loc.lat, loc.lng],
                    radius=8,
                    color=color,
                    weight=2,
                    fill=True,
                    fill_color=tz_color,
                    fill_opacity=0.8,
                    popup=folium.Popup(popup_content, max_width=280),
                    tooltip=f"#{stop_num} {loc.name}"
                ).add_to(m)

    m.save(output_html_path)
    return os.path.abspath(output_html_path)


def plot_benchmark_chart(
    solutions: Dict[str, VRPSolution],
    output_png_path: str = "output/benchmark_chart.png"
) -> str:
    """
    Generate professional comparison bar chart and save to PNG.
    """
    if not MPL_AVAILABLE:
        raise ImportError("Matplotlib is not installed.")

    os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)

    names = list(solutions.keys())
    distances = [sol.total_distance_km for sol in solutions.values()]
    times_ms = [sol.execution_time_sec * 1000.0 for sol in solutions.values()]
    vehicles = [sol.num_vehicles for sol in solutions.values()]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.patch.set_facecolor('#ffffff')

    # Color palette
    colors = ['#3b82f6', '#0ea5e9', '#f59e0b', '#10b981']
    bar_colors = [colors[i % len(colors)] for i in range(len(names))]

    # Subplot 1: Total Distance Comparison
    y_pos = np.arange(len(names))
    bars = ax1.barh(y_pos, distances, color=bar_colors, height=0.55, edgecolor='#1e293b', linewidth=0.8)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, fontsize=11, fontweight='semibold')
    ax1.invert_yaxis()  # Labels read top-to-bottom
    ax1.set_xlabel('Tổng quãng đường (km)', fontsize=11, fontweight='bold')
    ax1.set_title('So Sánh Tổng Quãng Đường (Càng thấp càng tốt)', fontsize=12, fontweight='bold', pad=12)
    ax1.grid(axis='x', linestyle='--', alpha=0.5)

    base_dist = distances[0]
    for i, bar in enumerate(bars):
        dist = distances[i]
        diff_pct = ((dist - base_dist) / base_dist) * 100.0 if i > 0 else 0.0
        label_text = f"{dist:.1f} km"
        if i > 0 and diff_pct != 0.0:
            label_text += f" ({diff_pct:+.1f}%)"
        ax1.text(dist + 0.8, bar.get_y() + bar.get_height()/2.0, label_text, 
                 va='center', fontsize=10, fontweight='bold', color='#0f172a')

    # Subplot 2: Execution Time (ms)
    bars2 = ax2.bar(y_pos, times_ms, color=bar_colors, width=0.5, edgecolor='#1e293b', linewidth=0.8)
    ax2.set_xticks(y_pos)
    ax2.set_xticklabels([f"Algo {i+1}" for i in range(len(names))], fontsize=10)
    ax2.set_ylabel('Thời gian thực thi (mili-giây)', fontsize=11, fontweight='bold')
    ax2.set_title('Thời Gian Tính Toán (ms)', fontsize=12, fontweight='bold', pad=12)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    for bar, t_val in zip(bars2, times_ms):
        ax2.text(bar.get_x() + bar.get_width()/2.0, t_val + max(times_ms)*0.02, 
                 f"{t_val:.2f} ms", ha='center', va='bottom', fontsize=9, fontweight='semibold')

    # Legend for names on right plot
    legend_labels = [f"Algo {i+1}: {name} ({vehicles[i]} xe)" for i, name in enumerate(names)]
    ax2.legend(bars2, legend_labels, loc='upper left', fontsize=9, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_png_path, dpi=300, bbox_inches='tight')
    plt.close()

    return os.path.abspath(output_png_path)
