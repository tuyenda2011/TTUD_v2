# 🏭 Warehouse Joint Optimizer (JOBPRSP)

> **Hệ thống Tối ưu hóa Đồng thời Gom đơn, Định tuyến và Lập lịch lấy hàng trong Kho hàng (Joint Order Batching, Picker Routing, and Picker Scheduling)**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-123%20Passed-brightgreen.svg)](tests/)
[![Algorithms](https://img.shields.io/badge/Algorithms-ALNS%20%7C%20VNS%20%7C%20LNS%20%7C%20Exact-orange.svg)](warehouse_opt/)

---

## 🌟 Điểm nổi bật của dự án

- **🎯 Tối ưu hóa đa mục tiêu (Joint Optimization):** Giải quyết bài toán tích hợp 3 giai đoạn: Gom đơn hàng vào chuyến (Batching), Tìm đường đi ngắn nhất trong lối đi (Routing - S-Shape, Return, 2-Opt), và Phân công lập lịch cho nhiều nhân viên (Scheduling).
- **🎮 Mô phỏng động 60fps (Digital Twin Warehouse):** Trình diễn trực quan xe lấy hàng (Picker) chuyển động mượt mà dọc theo các lối đi, rẽ lối đi giữa, bốc dỡ hàng hóa và cập nhật tải trọng theo thời gian thực ngay trên trình duyệt (HTML5 Canvas).
- **🗺️ 5 Kịch bản kho thực tế:** Hỗ trợ từ kho nhỏ 1 khối (`single_block`), kho 2 khối có lối đi cắt ngang (`double_block`), trung tâm phân phối lớn (`mega_hub`), giờ cao điểm Flash Sale (`rush_hour`), đến kho áp dụng nguyên tắc Pareto 80/20 (`abc_zonal`).
- **📊 Đối chuẩn với Benchmark quốc tế:** Tích hợp và đối soát trực tiếp trên **243 bộ dữ liệu chuẩn của tác giả Kris Braekers**, quy đổi thông minh hiển thị giờ/phút và km trực quan.
- **⚡ Thuật toán Metaheuristic mạnh mẽ:** So sánh đối chuẩn giữa các phương pháp: Cơ sở (`B0`, `B1`, `B2`, `B3`), `LNS`, `ALNS` (Adaptive Large Neighborhood Search), và `VNS` (Variable Neighborhood Search).

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy nhanh

### Cách 1: Sử dụng môi trường Conda có sẵn (`TTUD`)

Mở **Anaconda Prompt** và chạy:

```powershell
conda activate TTUD
cd /d d:\TTUD_v2
pip install -r requirements.txt
streamlit run demo/app.py
```

---

### Cách 2: Cài đặt từ đầu bằng Python tiêu chuẩn

#### Bước 1: Mở Terminal tại thư mục dự án
```bash
cd /d d:\TTUD_v2
```

#### Bước 2: Tạo môi trường ảo và cài đặt thư viện
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Bước 3: Khởi chạy ứng dụng Web
```bash
streamlit run demo/app.py
```
Ứng dụng sẽ tự động mở tại địa chỉ: **http://localhost:8501**

---

## 🎮 Hướng dẫn sử dụng Giao diện Demo

Giao diện Web Streamlit được chia thành 4 khu vực làm việc chính:

1. **Thanh bên điều khiển (Sidebar):**
   - **Nguồn dữ liệu:** Chọn **Dữ liệu tổng hợp** (5 kịch bản kho thực tế), **Kris — benchmark tác giả** (243 bộ dữ liệu chuẩn), hoặc **JSON tải lên**.
   - **Cấu hình:** Số lượng đơn hàng, số nhân viên lấy hàng (3–6+ nhân viên), sức chứa của xe đẩy (capacity).
   - **Mục nâng cao:** Tinh chỉnh độ nới hạn (`tightness`), seed ngẫu nhiên, ngân sách tìm kiếm (giây) và bật so sánh thuật toán (`VNS`, `LNS`, `B0-B3`).
2. **Tab 1 — 🎮 Mô phỏng động (Digital Twin):**
   - Xem picker di chuyển 60fps dọc lối đi kho, rẽ lối giữa, bốc dỡ hàng hóa và cập nhật dung lượng giỏ hàng.
   - Bộ điều khiển tiện ích: Play / Pause / Tua lại ca làm việc (`↺ Xem lại`).
   - Tùy chỉnh tốc độ phát (`0.5x`, `1x`, `2x`, `5x`).
   - Hỗ trợ **Phóng to / Thu nhỏ / Kéo bản đồ (Zoom & Pan)** bằng chuột hoặc phím bấm `🔍+`, `🔍-`, `⛶`.
   - Lọc góc nhìn theo từng nhân viên (`P1`, `P2`, ...).
3. **Tab 2 — Tổng quan kết quả:**
   - Đánh giá 3 chỉ số cốt lõi: **Đơn trễ**, **Thời gian hoàn tất (Makespan)**, **Quãng đường**.
   - Biểu đồ hội tụ điểm mục tiêu $F$ và bảng so sánh trực quan giữa ALNS, VNS và baseline B0.
4. **Tab 3 & 4 — Tuyến & Lịch trình / Bảng chi tiết:**
   - Xem lộ trình chi tiết từng chuyến (Batch) và danh sách mặt hàng nhặt tại từng ô kệ.
   - Tải kết quả nghiệm JSON, dữ liệu đầu vào hoặc snapshot toàn bộ phiên chạy.

---

## 🗺️ 5 Kịch bản kho hàng thực tế (Map Scenarios)

| Kịch bản | Tên kỹ thuật | Mô tả thực tế | Đặc điểm cấu trúc |
| :--- | :--- | :--- | :--- |
| **Kho 1 khối** | `single_block` | Kho tiêu chuẩn vừa và nhỏ (shop thời trang, nhà thuốc). | 4 dãy kệ song song, 1 khối liền mạch, 3 nhân viên. |
| **Kho 2 khối** | `double_block` | Kho phân phối có lối đi cắt ngang ở giữa để quay đầu xe. | 10 khối kệ, có 1 lối đi giữa (`cross_aisle`), 3 nhân viên. |
| **Trung tâm phân phối lớn** | `mega_hub` | Trung tâm chia chọn TMĐT lớn (Fulfillment Center). | 10 dãy kệ dài, 2 lối đi giữa chia làm 3 khối, 5 nhân viên. |
| **Giờ cao điểm Flash Sale** | `rush_hour` | Mô phỏng áp lực đơn dồn dập (ngày hội 11/11, 12/12). | Đơn hàng phát sinh liên tục, hạn chót cực gấp (`tightness=0.3`). |
| **Phân vùng ABC** | `abc_zonal` | Kho ứng dụng nguyên tắc Pareto 80/20 của ngành Logistics. | 20% mặt hàng bán chạy nhất (Nhóm A) xếp sát Depot. |

---

## 💻 Chạy bằng Dòng lệnh CLI (Command Line)

Bạn có thể chạy độc lập các module sinh dữ liệu, giải thuật toán và kiểm tra tính hợp lệ mà không cần mở giao diện Web:

```bash
# 1. Tự sinh dữ liệu kho theo kịch bản
python -m warehouse_opt generate --orders 20 --pickers 4 --capacity 30 --scenario double_block --output data/synthetic/my_run.json

# 2. Chạy thuật toán giải (ALNS, VNS, LNS, B0)
python -m warehouse_opt solve data/synthetic/my_run.json --method ALNS --seconds 5 --output results/my_solution.json

# 3. Kiểm định độc lập nghiệm (Tải trọng, Tuyến đi, Thời hạn giao)
python -m warehouse_opt validate data/synthetic/my_run.json results/my_solution.json
```

---

## 🧠 Tổng quan Thuật toán Metaheuristic

Bài toán giải quyết hàm mục tiêu tổng hợp $F$:

$$\min F = w_1 \cdot \text{Distance} + w_2 \cdot \text{Makespan} + w_3 \cdot \text{Tardiness}$$

Hệ thống cung cấp đầy đủ các thuật toán từ cơ sở đến nâng cao:
* **B0 – B3 (Constructive Baselines):** Gom chuyến tuần tự / theo khoảng cách tăng thêm, kết hợp cải tiến cục bộ 2-Opt và hoán vị lịch.
* **LNS (Large Neighborhood Search):** Phá hủy một phần nghiệm (Shaw removal, Worst removal, Random removal) và tái thiết kế nghiệm (Greedy repair, Regret repair).
* **ALNS (Adaptive LNS):** Tự động điều chỉnh xác suất chọn toán tử phá hủy và tái thiết dựa trên lịch sử cải thiện hàm mục tiêu qua cơ chế Roulette Wheel.
* **VNS (Variable Neighborhood Search):** Khám phá không gian nghiệm bằng cách chuyển đổi tuần tự giữa các cấu trúc lân cận khác nhau (Shift đơn, Swap chuyến, Đổi nhân viên).

---

## 🧪 Kiểm thử và Đảm bảo chất lượng

Dự án sở hữu bộ kiểm thử tự động toàn diện với **123 bài kiểm tra `pytest`** bao phủ:
- Tính hợp lệ của cấu trúc đồ thị kho và thuật toán tìm đường Dijkstra.
- Các toán tử phá hủy / tái thiết trong ALNS và lân cận VNS.
- Ràng buộc tải trọng xe, tính đơn trễ và thời gian hoàn tất.
- Trình dựng mô phỏng động 60fps và xử lý chuẩn hóa đơn vị đo lường.

Chạy toàn bộ test suite:
```bash
pytest -q
```

---

## 📁 Cấu trúc thư mục dự án

```text
TTUD_v2/
├── demo/                       # Ứng dụng Web Streamlit & Mô phỏng Digital Twin
│   ├── app.py                  # Entrypoint chính của giao diện
│   ├── components.py           # Các thẻ chỉ số, bảng kết quả, biểu đồ
│   ├── simulation.py           # Trình mô phỏng HTML5 Canvas 60fps
│   └── state.py                # Quản lý trạng thái và luồng thực thi
├── warehouse_opt/              # Package thuật toán cốt lõi
│   ├── generator.py            # 5 kịch bản kho & sinh dữ liệu ABC
│   ├── models.py               # Cấu trúc dữ liệu: Instance, Order, Batch...
│   ├── graph.py                # Đồ thị kho, tìm đường ngắn nhất
│   ├── routing.py              # Định tuyến S-Shape, Return, 2-Opt
│   ├── search.py               # Thuật toán ALNS & LNS
│   ├── vns.py                  # Thuật toán VNS
│   ├── heuristics.py           # Các thuật toán cơ sở B0, B1, B2, B3
│   ├── validator.py            # Bộ kiểm định nghiệm độc lập
│   └── units.py                # Chuẩn hóa đơn vị đo lường
├── data/                       # Dữ liệu mẫu (Synthetic) & Kris Benchmark
├── results/                    # Kết quả chạy thực nghiệm và báo cáo
├── tests/                      # 123 bài kiểm thử tự động với pytest
└── docs/                       # Tài liệu thiết kế, mô hình toán & hướng dẫn bảo vệ
```

---

## 📜 Giấy phép & Thông tin liên hệ

Dự án phục vụ mục đích học tập, nghiên cứu và báo cáo đồ án môn học **Thuật toán ứng dụng (TTUD)**. Mọi đóng góp và thắc mắc vui lòng liên hệ tác giả qua repository này.
