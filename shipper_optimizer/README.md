# 🚚 SHIPPER ROUTE OPTIMIZER (HÀ NỘI)

> **Hệ thống tối ưu hóa lộ trình giao hàng đa phương tiện tại Hà Nội**  
> Ứng dụng các thuật toán: **Dijkstra**, **Nearest Neighbor (TSP)**, **Clarke-Wright Savings (VRP)** và **2-Opt Local Search**.

---

## 📌 1. CÁC THUẬT TOÁN ĐÃ CÀI ĐẶT

1. **Dijkstra (`src/algorithms/dijkstra.py`)**:
   - Xây dựng ma trận khoảng cách $N \times N$ dựa trên công thức tọa độ Haversine.
   - Tìm đường đi ngắn nhất giữa 2 điểm bất kỳ bằng Min-Heap ($O((V + E) \log V)$).
2. **Nearest Neighbor (`src/algorithms/nearest_neighbor.py`)**:
   - Thuật toán tham lam xây dựng lộ trình TSP cho 1 xe đi qua toàn bộ 30 điểm giao và quay về kho ($O(n^2)$).
3. **Clarke-Wright Savings (`src/algorithms/clarke_wright.py`)**:
   - Thuật toán ghép lộ trình tối ưu cho bài toán định tuyến nhiều xe có ràng buộc tải trọng (CVRP).
   - Tự động phân chia cụm khách hàng theo sức chứa của xe.
4. **2-Opt Local Search (`src/algorithms/two_opt.py`)**:
   - Tối ưu cải thiện cục bộ, khử các đoạn đường bị cắt chéo (crossover), giảm đáng kể quãng đường di chuyển.
5. **Benchmark & Evaluation (`src/algorithms/benchmark.py`)**:
   - So sánh toàn diện hiệu năng, thời gian chạy, số xe, lượng xăng tiêu thụ và chi phí tiết kiệm.
6. **Bản đồ tương tác Folium (`src/visualization/map_viz.py`)**:
   - Xuất bản đồ HTML trực quan hóa lộ trình từng xe với màu sắc riêng biệt, thứ tự giao hàng và thông tin đơn hàng.

---

## 🚀 2. HƯỚNG DẪN CHẠY VỚI CONDA `TTUD`

### Bước 1: Kích hoạt môi trường Conda
```bash
conda activate TTUD
```

### Bước 2: Di chuyển vào thư mục dự án
```bash
cd d:\TTUD\shipper_optimizer
```

### Bước 3: Chạy ứng dụng

#### 👉 Cách 1: Chạy Benchmark toàn diện và xuất bản đồ
```bash
python main.py --benchmark
```

#### 👉 Cách 2: Chạy Menu tương tác CLI
```bash
python main.py
```

#### 👉 Cách 3: Tùy chỉnh sức chứa xe (Capacity) hoặc Dataset
```bash
python main.py --benchmark --capacity 150 --dataset data/hanoi_deliveries.csv
```

---

## 🧪 3. CHẠY KIỂM THỬ (UNIT TESTS)

Để chạy toàn bộ bài kiểm tra tính đúng đắn của các thuật toán:
```bash
conda activate TTUD
cd d:\TTUD\shipper_optimizer
pytest tests/ -v
```

---

## 📁 4. CẤU TRÚC THƯ MỤC DỰ ÁN

```
shipper_optimizer/
├── main.py                        # Entry point chính
├── requirements.txt               # Danh sách thư viện
├── README.md                      # Hướng dẫn sử dụng
├── data/
│   └── hanoi_deliveries.csv       # Dataset 30 điểm giao tại Hà Nội + Kho V9
├── output/                        # Thư mục xuất kết quả (tự động tạo)
│   ├── benchmark_results.json     # Kết quả chi tiết dạng JSON
│   ├── hanoi_routes.html          # Bản đồ tương tác Folium
│   └── benchmark_chart.png        # Biểu đồ so sánh hiệu năng
├── src/
│   ├── algorithms/
│   │   ├── dijkstra.py            # Thuật toán 1: Dijkstra
│   │   ├── nearest_neighbor.py    # Thuật toán 2: Nearest Neighbor (TSP)
│   │   ├── clarke_wright.py       # Thuật toán 3a: Clarke-Wright Savings (VRP)
│   │   ├── two_opt.py             # Thuật toán 3b: 2-Opt Local Search
│   │   └── benchmark.py           # Bộ đo đạc & đánh giá
│   ├── models/
│   │   ├── location.py            # Model Tọa độ & Haversine Distance
│   │   └── route.py               # Model Tuyến đường & Nghiệm VRP
│   ├── visualization/
│   │   └── map_viz.py             # Trực quan hóa Folium & Matplotlib
│   └── data/
│       ├── loader.py              # Xử lý và đọc dữ liệu CSV
│       └── hanoi_deliveries.csv
└── tests/
    └── test_algorithms.py         # Bộ kiểm thử Pytest
```
