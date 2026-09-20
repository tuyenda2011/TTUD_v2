# 🏭 Warehouse Joint Optimizer (JOBPRSP)

> **Hệ thống Tối ưu hóa Đồng thời Gom đơn, Định tuyến và Lập lịch lấy hàng trong Kho hàng (Joint Order Batching, Picker Routing, and Picker Scheduling)**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-1.62%2B-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-127%20Collected-brightgreen.svg)](tests/)
[![Algorithms](https://img.shields.io/badge/Algorithms-ALNS%20%7C%20VNS%20%7C%20LNS%20%7C%20Exact-orange.svg)](src/)

---

## 🌟 Điểm nổi bật của dự án

- **🎯 Tối ưu hóa đa mục tiêu (Joint Optimization):** Giải quyết bài toán tích hợp gom đơn, định tuyến trên đồ thị kho (NN, 2-Opt, Exact, S-Shape) và lập lịch cho nhiều nhân viên.
- **🎮 Mô phỏng phát lại nghiệm:** HTML5 Canvas hiển thị picker, tuyến `walk`, điểm lấy hàng và tải trọng theo timeline của nghiệm đã kiểm chứng. Tốc độ khung hình chưa được benchmark như một cam kết 60fps.
- **🗺️ 5 kịch bản kho tổng hợp:** Hỗ trợ `single_block`, `double_block`, `mega_hub`, `rush_hour` và `abc_zonal`; đây là dữ liệu sinh nhân tạo để kiểm thử, không phải xác nhận vận hành tại kho thực tế.
- **📊 Adapter benchmark tác giả:** Có thể đọc bộ Kris khi dữ liệu được chuẩn bị; catalog local gồm 243 instance Kris Small. Kết quả không tự động là benchmark toàn bộ catalog và đơn vị nguồn được giữ nguyên nếu chưa có hệ số xác nhận.
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
   - **Nguồn dữ liệu:** Chọn **Dữ liệu tổng hợp** (5 kịch bản), **Kris — benchmark tác giả** (catalog local tùy chọn), hoặc **JSON tải lên**.
   - **Cấu hình:** Số lượng đơn hàng, số nhân viên lấy hàng (3–6+ nhân viên), sức chứa của xe đẩy (capacity).
   - **Mục nâng cao:** Tinh chỉnh độ nới hạn (`tightness`), seed ngẫu nhiên, ngân sách tìm kiếm (giây) và bật so sánh thuật toán (`VNS`, `LNS`, `B0-B3`).
2. **Tab 1 — 🎮 Mô phỏng động:**
   - Xem picker phát lại `walk` dọc lối đi, bốc dỡ hàng hóa và cập nhật dung lượng giỏ hàng theo nghiệm.
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

## 🗺️ 5 Kịch bản kho tổng hợp (Map Scenarios)

| Kịch bản | Tên kỹ thuật | Mô tả kịch bản | Đặc điểm cấu trúc |
| :--- | :--- | :--- | :--- |
| **Kho 1 khối** | `single_block` | Kho tiêu chuẩn vừa và nhỏ (shop thời trang, nhà thuốc). | 4 dãy kệ song song, 1 khối liền mạch, 3 nhân viên. |
| **Kho 2 khối** | `double_block` | Kho phân phối có lối đi cắt ngang ở giữa để quay đầu xe. | 10 khối kệ, có 1 lối đi giữa (`cross_aisle`), 3 nhân viên. |
| **Trung tâm phân phối lớn** | `mega_hub` | Trung tâm chia chọn TMĐT lớn (Fulfillment Center). | 10 dãy kệ dài, 2 lối đi giữa chia làm 3 khối, 5 nhân viên. |
| **Giờ cao điểm giả lập** | `rush_hour` | Sinh instance tĩnh với deadline chặt để kiểm tra thành phần scheduling. | Không có release time hoặc đơn phát sinh khi solver đang chạy (`tightness=0.06`). |
| **Phân vùng ABC** | `abc_zonal` | Mẫu tổng hợp: 20% SKU gần depot chiếm khoảng 70% lượt chọn hàng. | Độ gần tính theo khoảng cách trên đồ thị; đây là giả định của generator. |

---

## 💻 Chạy bằng Dòng lệnh CLI (Command Line)

Bạn có thể chạy độc lập các module sinh dữ liệu, giải thuật toán và kiểm tra tính hợp lệ mà không cần mở giao diện Web:

```bash
# 1. Tự sinh dữ liệu kho theo kịch bản
python -m src generate --orders 20 --pickers 4 --capacity 30 --scenario double_block --output data/synthetic/my_run.json

# 2. Chạy thuật toán giải (ALNS, VNS, LNS, B0)
python -m src solve data/synthetic/my_run.json --method ALNS --seconds 5 --output results/my_solution.json

# 3. Kiểm định độc lập nghiệm (Tải trọng, Tuyến đi, Thời hạn giao)
python -m src validate data/synthetic/my_run.json results/my_solution.json
```

---

## 🧠 Tổng quan Thuật toán Metaheuristic

Bài toán giải quyết hàm mục tiêu tổng hợp $F$:

$$\min F = w_1 \frac{D}{D_{ref}} + w_2 \frac{C_{max}}{C_{ref}} + w_3 \frac{T}{T_{ref}}$$

Hệ thống cung cấp đầy đủ các thuật toán từ cơ sở đến nâng cao:
* **B0 – B3 (Constructive Baselines):** Gom chuyến tuần tự / theo khoảng cách tăng thêm, kết hợp cải tiến cục bộ 2-Opt và hoán vị lịch.
* **LNS (Large Neighborhood Search):** Phá hủy một phần nghiệm (Shaw removal, Worst removal, Random removal) và tái thiết kế nghiệm (Greedy repair, Regret repair).
* **ALNS (Adaptive LNS):** Tự động điều chỉnh xác suất chọn toán tử phá hủy và tái thiết dựa trên lịch sử cải thiện hàm mục tiêu qua cơ chế Roulette Wheel.
* **VNS (Variable Neighborhood Search):** Khám phá không gian nghiệm bằng cách chuyển đổi tuần tự giữa các cấu trúc lân cận khác nhau (Shift đơn, Swap chuyến, Đổi nhân viên).

---

## 🧪 Kiểm thử và Đảm bảo chất lượng

Dự án sở hữu bộ kiểm thử tự động với **137 test được thu thập bằng `pytest`** (một số test tùy chọn có thể skip khi thiếu dữ liệu/phụ thuộc):
- Tính hợp lệ của cấu trúc đồ thị kho và thuật toán tìm đường Dijkstra.
- Các toán tử phá hủy / tái thiết trong ALNS và lân cận VNS.
- Ràng buộc tải trọng xe, tính đơn trễ và thời gian hoàn tất.
- Timeline mô phỏng phát lại `walk`, xử lý depot service và hiển thị đơn vị đã khai báo.

Chạy toàn bộ test suite:
```bash
pytest -q
```

---

## 📁 Cấu trúc thư mục dự án

```text
TTUD_v2/
├── demo/                       # Ứng dụng Web Streamlit & mô phỏng phát lại nghiệm
│   ├── app.py                  # Entrypoint chính của giao diện
│   ├── components.py           # Các thẻ chỉ số, bảng kết quả, biểu đồ
│   ├── simulation.py           # Trình mô phỏng HTML5 Canvas phát lại nghiệm
│   └── state.py                # Quản lý trạng thái và luồng thực thi
├── src/                       # Package thuật toán cốt lõi
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
├── tests/                      # 137 test tự động với pytest
└── docs/                       # Tài liệu thiết kế, mô hình toán & hướng dẫn bảo vệ
```

---

## Thực nghiệm và báo cáo hoàn tất

Kết quả và giới hạn của đợt hoàn tất cải tiến được ghi ở
[Báo cáo hoàn tất](docs/BAO_CAO_HOAN_TAT_CAI_TIEN.md).
Để chạy lại nghiên cứu có tuning/holdout tách biệt, 10 search seed, ablation,
độ nhạy trọng số và exact nhỏ:

```powershell
python scripts/run_research.py all --protocol configs/research_completion.json --output results/study_moi
```

Đọc [protocol](docs/RESEARCH_PROTOCOL.md) trước khi diễn giải số liệu.
`incremental_validation` và toán tử `delay_chain` là tùy chọn thử nghiệm;
chưa đạt tiêu chí giữ trên tập phát triển nên không bật mặc định.
ALNS là khung thuật toán có sẵn; không tuyên bố luôn thắng LNS/VNS hay đạt tối ưu toàn cục.

## 📜 Giấy phép & Thông tin liên hệ

Dự án phục vụ mục đích học tập, nghiên cứu và báo cáo đồ án môn học **Thuật toán ứng dụng (TTUD)**. Mọi đóng góp và thắc mắc vui lòng liên hệ tác giả qua repository này.
