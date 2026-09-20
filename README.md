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
- **📊 Adapter benchmark tác giả:** Catalog local gồm 18 instance Kris Small, 6 file mỗi nhóm 6/12/18 đơn. Đây là tập con phục vụ đồ án, không phải toàn bộ benchmark tác giả.
- **⚡ Thuật toán Metaheuristic mạnh mẽ:** So sánh đối chuẩn giữa các phương pháp: Cơ sở (`B0`, `B1`, `B2`, `B3`), `LNS`, `ALNS` (Adaptive Large Neighborhood Search), và `VNS` (Variable Neighborhood Search).

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy nhanh

### Cách 1: Sử dụng môi trường Conda có sẵn (`TTUD`)

Mở **Anaconda Prompt** hoặc **VS Code Terminal (CMD)** và chạy:

```cmd
conda activate TTUD
cd /d d:\TTUD_v2
pip install -r requirements.txt
streamlit run demo/app.py
```

---

### Cách 2: Cài đặt từ đầu bằng Python tiêu chuẩn

#### Bước 1: Mở Terminal tại thư mục dự án
```cmd
cd /d d:\TTUD_v2
```

#### Bước 2: Tạo môi trường ảo và cài đặt thư viện
```cmd
:: Windows CMD
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### Bước 3: Khởi chạy ứng dụng Web
```cmd
streamlit run demo/app.py
```
Ứng dụng sẽ tự động mở tại địa chỉ: **http://localhost:8501**

---

## 🎮 Hướng dẫn sử dụng Giao diện Demo

Demo hiển thị Kris bằng mét và phút/giây theo **quy ước dự án chưa được nguồn xác nhận**:
10 đơn vị khoảng cách gốc = 1 m; 30 đơn vị thời gian gốc = 1 giây.
Quy đổi áp dụng cho bản hiển thị của số đo, deadline, độ trễ, lịch và mô phỏng;
không thay đổi F hoặc số đơn trễ. JSON tải xuống và benchmark vẫn giữ dữ liệu gốc.
Không coi số đo đã quy đổi là số đo vật lý được tác giả chứng nhận.

Giao diện Web Streamlit được chia thành 4 khu vực làm việc chính:

1. **Thanh bên điều khiển (Sidebar):**
   - **Nguồn dữ liệu:** Chọn **Dữ liệu tổng hợp** (5 kịch bản), **Kris — benchmark tác giả** (catalog local tùy chọn), hoặc **JSON tải lên**.
   - **Cấu hình:** Số lượng đơn hàng, số nhân viên lấy hàng (3–6+ nhân viên), sức chứa của xe đẩy (capacity).
   - **Mục nâng cao:** Tinh chỉnh độ nới hạn (`tightness`), seed ngẫu nhiên, ngân sách tìm kiếm (giây) và bật so sánh 5 thuật toán `B0/B2/LNS/ALNS/VNS`.
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

Bạn có thể chạy độc lập các module sinh dữ liệu, giải thuật toán và kiểm tra tính hợp lệ mà không cần mở giao diện Web trên terminal CMD:

```cmd
:: 1. Tự sinh dữ liệu kho theo kịch bản
python -m src generate --orders 20 --pickers 4 --capacity 30 --scenario double_block --output data/synthetic/my_run.json

:: 2. Chạy thuật toán giải (ALNS, VNS, LNS, B0)
python -m src solve data/synthetic/my_run.json --method ALNS --seconds 5 --output results/my_solution.json

:: 3. Kiểm định độc lập nghiệm (Tải trọng, Tuyến đi, Thời hạn giao)
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

Chạy toàn bộ test suite trên CMD:
```cmd
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

```cmd
python scripts/run_research.py all --protocol configs/research_completion.json --output results/study_run_01
```

Đọc [protocol](docs/RESEARCH_PROTOCOL.md) trước khi diễn giải số liệu.
`incremental_validation` và toán tử `delay_chain` là tùy chọn thử nghiệm;
chưa đạt tiêu chí giữ trên tập phát triển nên không bật mặc định.
ALNS là khung thuật toán có sẵn; không tuyên bố luôn thắng LNS/VNS hay đạt tối ưu toàn cục.

### Chạy benchmark và xuất dữ liệu cho báo cáo

Chạy các lệnh sau trực tiếp trên **terminal CMD của VS Code**. Mỗi lần chạy phải dùng một thư mục kết quả mới vì pipeline không ghi đè dữ liệu cũ:

```cmd
:: 1. Chạy nghiên cứu đầy đủ (tuning, holdout, ablation, sensitivity, exact):
python scripts/run_research.py all --protocol configs/research_completion.json --output results/study_run_01

:: 2. Kiểm tra holdout và xuất bảng/biểu đồ dùng trong báo cáo:
python scripts/build_comparison_report.py --benchmark results/study_run_01/holdout --output results/study_run_01/holdout_report
```

Các tệp dùng để viết báo cáo nằm trong `results/study_run_01/holdout_report/`:

- `REPORT.md`: mô tả bộ dữ liệu, số run và các tệp đã kiểm tra.
- `comparison.csv`: bảng thắng/hòa/thua và mức cải thiện trung bình.
- `comparison_pairs.csv`: kết quả từng instance cho từng cặp thuật toán.
- `per_instance.csv`: trung bình, độ lệch chuẩn và chẩn đoán theo instance/thuật toán.
- `raw_metrics.csv`: từng lần chạy sau khi qua validator.
- `charts/objective_by_instance.*`, `charts/win_tie_loss.*`, `charts/schedule_by_picker.svg`: hình đưa vào báo cáo.

Báo cáo tổng hợp toàn bộ thí nghiệm nằm ở `results/study_run_01/REPORT.md`; nghiệm thô và manifest được giữ trong `results/study_run_01/holdout/` để truy vết.

Nếu chỉ cần kiểm tra pipeline hoặc lấy nhanh bảng và biểu đồ mẫu, dùng cấu hình smoke (chạy trên terminal CMD):

```cmd
python -m src benchmark --config configs/smoke.json --output results/benchmark_smoke_run
python scripts/build_comparison_report.py --benchmark results/benchmark_smoke_run --output results/benchmark_smoke_report
```

Kết quả smoke chỉ dùng để kiểm tra và minh họa. Số liệu chính thức phải lấy từ pipeline phù hợp: `run_research.py all` cho protocol nghiên cứu, `map_scenarios_benchmark.json` cho năm map của Demo, hoặc `benchmark_kris.py` cho bộ dữ liệu tác giả.

### Benchmark đúng 5 kịch bản map trong Demo

Nguồn **Dữ liệu tổng hợp — chỉ kiểm thử** của Demo dùng năm map trong `MAP_SCENARIOS`. Để benchmark đúng cùng các map đó, dùng cấu hình riêng trong terminal CMD:

```cmd
:: 1. Chạy nhanh (khuyên dùng khi kiểm thử): 1 seed, 1.0 giây/lần chạy (tự động xuất biểu đồ)
python scripts/benchmark_maps.py --seconds 1.0 --search-seeds 1 --output results/map_quick_run

:: 2. Chạy đầy đủ 10 seeds (chuẩn báo cáo đầy đủ 160 run - tự động xuất biểu đồ)
python scripts/benchmark_maps.py --output results/map_run_01
```

Cấu hình này chạy `single_block`, `double_block`, `mega_hub`, `rush_hour` và `abc_zonal` với seed map 42, cùng 5 phương pháp `B0/B2/LNS/ALNS/VNS`. B0/B2 chạy một lần; LNS/ALNS/VNS chạy 10 search seed, tổng cộng 160 run. Đây là bộ số liệu dùng khi báo cáo kết quả theo năm kịch bản Demo; pipeline `run_research.py all` vẫn là bộ synthetic nghiên cứu độc lập.

### Benchmark bộ dữ liệu tác giả Kris

Để chạy benchmark trên bộ 18 instance Kris Small (6 file mỗi nhóm 6/12/18 đơn) và so sánh 5 thuật toán `B0/B2/LNS/ALNS/VNS` trên terminal CMD (tự động xuất đầy đủ bảng số liệu và biểu đồ vào `<output>_report` chỉ với 1 dòng lệnh):

```cmd
:: 1. Chạy nhanh (khuyên dùng khi kiểm thử): 1 file mỗi nhóm số lượng đơn, 1.0 giây/lần chạy (tự động xuất biểu đồ)
python scripts/benchmark_kris.py --limit-per-size 1 --seconds 1.0 --output results/kris_quick_run

:: 2. Chạy bộ 18 instance của đồ án (tự động xuất biểu đồ)
python scripts/benchmark_kris.py --output results/kris_18_run
```

> **Lưu ý:** Thư mục `--output` phải là thư mục mới (chưa tồn tại), runner từ chối ghi đè để bảo vệ tính toàn vẹn của kết quả benchmark.

## 📜 Giấy phép & Thông tin liên hệ

Dự án phục vụ mục đích học tập, nghiên cứu và báo cáo đồ án môn học **Thuật toán ứng dụng (TTUD)**. Mọi đóng góp và thắc mắc vui lòng liên hệ tác giả qua repository này.

Bộ Kris của đồ án là tập con 18 instance, không phải toàn bộ benchmark tác giả. Danh sách cố định và quy tắc chọn nằm trong `data/processed/kris_selection.json`; ưu tiên các file kiểm thử/demo đang dùng, sau đó lấy theo tên file cho đủ 6 file mỗi nhóm. Mặc định 3 search seed: 198 lượt chạy cho 5 thuật toán. Kết quả cũ trên 243 instance là đợt riêng, không dùng nhãn 18 instance cho số liệu đó.
