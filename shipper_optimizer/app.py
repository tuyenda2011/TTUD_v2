"""
🚚 Shipper Route Optimizer - Streamlit Web App
"""
import streamlit as st
import pandas as pd
import numpy as np
import os

# Page config
st.set_page_config(
    page_title="🚚 Shipper Route Optimizer",
    layout="wide"
)

# Import modules
from src.models.location import Location
from src.data.loader import load_deliveries, build_distance_matrix, get_depot_index
from src.algorithms.nearest_neighbor import NearestNeighbor
from src.algorithms.clarke_wright import ClarkeWrightSavings
from src.algorithms.two_opt import TwoOpt
from src.visualization.map_viz import generate_interactive_map
from src.data.graphhopper import GraphHopperAPI
from src.data.osrm import OSRMAPI

# GraphHopper API Key
GRAPH_HOPPER_API_KEY = "b10e32bf-7b05-4762-977b-ee3c7af85080"

# Custom CSS - Light theme
st.markdown("""
<style>
    /* Custom title */
    .custom-title {
        text-align: center;
        padding: 20px 0;
    }
    .custom-title h1 {
        font-size: 2.5rem;
        color: #1e40af;
        margin-bottom: 5px;
    }
    .custom-title p {
        color: #64748b;
        font-size: 1.1rem;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 600;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    }

    /* Sidebar header */
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1e40af;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)


def load_data(uploaded_file=None):
    """Load delivery data from file or use default"""
    if uploaded_file is not None:
        import io
        df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
        locations = []
        for _, row in df.iterrows():
            loc = Location(
                id=row['id'],
                name=row['name'],
                district=row.get('district', ''),
                lat=row['lat'],
                lng=row['lng'],
                demand_kg=row.get('demand_kg', 0),
                is_depot=(row['id'] == 'D0' or 'kho' in str(row['name']).lower()),
                traffic_zone=row.get('traffic_zone', 'low'),
                peak_hour_multiplier=row.get('peak_hour_multiplier', 1.0)
            )
            locations.append(loc)
        return locations
    else:
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'hanoi_traffic.csv')
        if os.path.exists(csv_path):
            return load_deliveries(csv_path)
        csv_path = os.path.join(os.path.dirname(__file__), 'src', 'data', 'hanoi_deliveries.csv')
        return load_deliveries(csv_path)


def render_metrics(locations, depot_idx):
    """Render metric cards"""
    n_deliveries = len(locations) - 1
    total_demand = sum(loc.demand_kg for loc in locations if not loc.is_depot)
    n_high_traffic = sum(1 for loc in locations if getattr(loc, 'traffic_zone', 'low') == 'high')
    depot = locations[depot_idx]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📍 Điểm giao", n_deliveries, delta="delivery points")
    with col2:
        st.metric("📦 Tổng khối lượng", f"{total_demand:.1f} kg")
    with col3:
        st.metric("🚦 Kẹt xe", n_high_traffic, delta_color="inverse")
    with col4:
        st.metric("🏭 Depot", depot.name)


def render_results(results, locations, dist_matrix, depot_idx):
    """Render optimization results"""

    # Find best solution
    best_sol = min(results.values(), key=lambda x: x.total_distance_km)
    best_name = [k for k, v in results.items() if v == best_sol][0]

    # Results comparison
    st.markdown("### 📊 So sánh thuật toán")

    comparison_data = []
    for name, sol in results.items():
        comparison_data.append({
            "Thuật toán": name,
            "Tổng km": f"{sol.total_distance_km:.2f}",
            "Số xe": sol.num_vehicles,
            "Thời gian": f"{sol.execution_time_sec*1000:.2f} ms",
            "Chi phí": f"{int(sol.fuel_cost_vnd):,} VND"
        })

    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Best result highlight
    st.success(f"✅ **Thuật toán tối ưu: {best_name}** — {best_sol.total_distance_km:.2f} km với {best_sol.num_vehicles} xe")

    return best_sol, best_name


def render_route_details(best_sol, locations):
    """Render route details"""
    st.markdown("### 🛣️ Chi tiết từng tuyến")

    for route in best_sol.routes:
        with st.expander(f"🚗 **Tuyến #{route.vehicle_id}** — {route.total_distance_km:.2f} km — {route.num_deliveries} điểm", expanded=True):

            route_data = []
            for i, (idx, name) in enumerate(zip(route.node_ids, route.node_names)):
                loc = next((l for l in locations if l.id == idx), None)
                if loc:
                    traffic = getattr(loc, 'traffic_zone', 'low')
                    traffic_emoji = "🔴" if traffic == 'high' else ("🟠" if traffic == 'medium' else "🟢")
                    route_data.append({
                        "Thứ tự": i,
                        "ID": idx,
                        "Tên": name,
                        "Quận": loc.district,
                        "Khối lượng": f"{loc.demand_kg} kg",
                        "Kẹt xe": f"{traffic_emoji} {traffic.upper()}"
                    })

            df_route = pd.DataFrame(route_data)
            st.dataframe(df_route, use_container_width=True, hide_index=True)


def render_map(locations, best_sol, route_geometries=None):
    """Render interactive map"""
    st.markdown("### 🗺️ Bản đồ lộ trình")

    os.makedirs("output", exist_ok=True)
    map_path = "output/streamlit_map.html"
    generate_interactive_map(locations, best_sol, output_html_path=map_path)

    # Read and display HTML
    with open(map_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Display map in full width container
    st.markdown("""
    <style>
    .map-container {
        width: 100%;
        height: 600px;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

    st.components.v1.html(html_content, height=650, scrolling=True)

    # Download button
    with open(map_path, "rb") as f:
        st.download_button(
            "📥 Tải bản đồ HTML",
            f,
            file_name="route_map.html",
            mime="text/html"
        )


def render_cost_analysis(best_sol, dist_matrix, depot_idx, locations):
    """Render cost analysis"""
    st.markdown("### 💰 Phân tích chi phí")

    naive_km = sum(2.0 * dist_matrix[depot_idx, i] for i in range(len(locations)) if i != depot_idx)
    saved_km = naive_km - best_sol.total_distance_km
    saved_pct = (saved_km / naive_km * 100) if naive_km > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Tuyến rời", f"{naive_km:.1f} km", delta_color="off")
    with col2:
        st.metric("Tối ưu", f"{best_sol.total_distance_km:.1f} km", delta=f"-{saved_km:.1f} km")
    with col3:
        st.metric("Tiết kiệm", f"{saved_pct:.1f}%", delta_color="normal")
    with col4:
        annual = saved_km * 2400 * 365
        st.metric("Tiết kiệm/năm", f"{int(annual/1000000):,}M VND", delta_color="normal")


def main():
    # Header
    st.markdown("""
    <div class="custom-title">
        <h1>🚚 Shipper Route Optimizer</h1>
        <p>Tối ưu hóa lộ trình giao hàng thông minh tại Hà Nội</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown('<p class="sidebar-header">⚙️ Cấu hình</p>', unsafe_allow_html=True)

        # Dataset upload
        st.markdown("#### 📁 Dataset")
        uploaded_file = st.file_uploader("Tải file CSV", type=['csv'], label_visibility="collapsed")

        # Vehicle settings
        st.markdown("#### 🚛 Xe giao hàng")
        capacity = st.slider("Sức chứa (kg)", 50, 500, 200, 10)

        # Algorithm selection
        st.markdown("#### 🔧 Thuật toán")
        use_nn = st.checkbox("Nearest Neighbor (TSP)", value=True)
        use_cw = st.checkbox("Clarke-Wright (VRP)", value=True)
        use_2opt = st.checkbox("+ 2-Opt tối ưu", value=True)

        # Distance calculation method
        st.markdown("#### 🗺️ Tính khoảng cách")
        distance_method = st.selectbox(
            "Phương pháp",
            ["Haversine (nhanh)", "OSRM (mien phi)", "GraphHopper (chinh xac)"],
            label_visibility="collapsed"
        )

        if distance_method == "Haversine (nhanh)":
            st.caption("Tinh khoang cach thang, khong can API")
        elif distance_method == "OSRM (mien phi)":
            st.caption("Theo duong that, khong can API key")
        else:
            st.caption("Theo duong that, can GraphHopper API key")

        # Time settings
        st.markdown("#### ⏰ Thời gian giao")
        time_options = {
            "🌅 Sáng sớm (5-7h)": 1.0,
            "🚗 Sáng (7-9h)": 1.5,
            "☀️ Trưa (9-12h)": 1.2,
            "🌤️ Chiều (12-14h)": 1.3,
            "🚦 Chiều muộn (14-17h)": 1.5,
            "🌆 Tối (17-19h)": 1.4,
            "🌙 Đêm (19-5h)": 1.0
        }
        selected_time = st.selectbox("Chọn khung giờ", list(time_options.keys()), label_visibility="collapsed")
        st.info(f"🚦 Traffic multiplier: **{time_options[selected_time]}x**")

        # Run button
        st.markdown("---")
        run_clicked = st.button("🚀 CHẠY TỐI ƯU", use_container_width=True)

    # Main content
    try:
        all_locations = load_data(uploaded_file)

        # Build distance matrix based on selected method
        route_geometries = None  # Default: no real route geometries

        if distance_method == "GraphHopper (chinh xac)":
            with st.spinner("Dang lay khoang cach tu GraphHopper API (toi da 10 diem)..."):
                gh = GraphHopperAPI(GRAPH_HOPPER_API_KEY)
                n_points = min(len(all_locations), 10)
                locations = all_locations[:n_points]
                depot_idx = get_depot_index(locations)
                dist_matrix, time_matrix = gh.build_distance_matrix(locations)
                st.success(f"Da lay khoang cach that tu GraphHopper cho {n_points} diem")
        elif distance_method == "OSRM (mien phi)":
            with st.spinner("Dang lay khoang cach tu OSRM (toi da 10 diem)..."):
                osrm = OSRMAPI()
                n_points = min(len(all_locations), 10)
                locations = all_locations[:n_points]
                depot_idx = get_depot_index(locations)
                dist_matrix, time_matrix, route_geometries = osrm.build_distance_matrix(locations, get_geometries=True)
                st.success(f"Da lay khoang cach that tu OSRM cho {n_points} diem (co duong di that)")
        else:
            locations = all_locations
            depot_idx = get_depot_index(locations)
            dist_matrix = build_distance_matrix(locations)

        # Show stats
        render_metrics(locations, depot_idx)

        st.markdown("---")

        # Run optimization
        if run_clicked or 'results' in st.session_state:
            if run_clicked:
                with st.spinner('Dang toi uu lo trinh...'):
                    results = {}
                    two_opt = TwoOpt(dist_matrix)

                    if use_nn:
                        nn = NearestNeighbor(locations, dist_matrix, depot_idx=depot_idx)
                        sol_nn = nn.solve()

                        if use_2opt:
                            results['NN + 2-Opt'] = two_opt.optimize_solution(sol_nn, locations)
                        else:
                            results['Nearest Neighbor'] = sol_nn

                    if use_cw:
                        cw = ClarkeWrightSavings(
                            locations, dist_matrix,
                            vehicle_capacity=capacity,
                            depot_idx=depot_idx
                        )
                        sol_cw = cw.solve()

                        if use_2opt:
                            results['Clarke-Wright + 2-Opt'] = two_opt.optimize_solution(sol_cw, locations)
                        else:
                            results['Clarke-Wright'] = sol_cw

                    st.session_state['results'] = results
                    st.session_state['locations'] = locations
                    st.session_state['dist_matrix'] = dist_matrix
                    st.session_state['depot_idx'] = depot_idx
                    st.session_state['route_geometries'] = route_geometries

            # Display results
            results = st.session_state['results']
            locations = st.session_state['locations']
            dist_matrix = st.session_state['dist_matrix']
            depot_idx = st.session_state['depot_idx']
            route_geometries = st.session_state.get('route_geometries')

            best_sol, best_name = render_results(results, locations, dist_matrix, depot_idx)
            render_route_details(best_sol, locations)
            render_map(locations, best_sol, route_geometries)
            render_cost_analysis(best_sol, dist_matrix, depot_idx, locations)

    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")


if __name__ == "__main__":
    main()
