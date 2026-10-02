# Warehouse Joint Optimizer

Hệ thống tối ưu hóa đồng thời **gom đơn hàng, định tuyến và lập lịch lấy hàng cho nhiều nhân viên** trong kho (*Joint Order Batching, Picker Routing and Picker Scheduling — JOBPRSP*).

Dự án được phát triển cho môn **Thuật toán ứng dụng (TTUD)**, cung cấp bộ giải bằng Python, giao diện mô phỏng Streamlit và pipeline thực nghiệm có thể kiểm chứng. Mô hình sử dụng **hạn giao mềm**: đơn hàng được phép trễ, với độ trễ được đưa vào hàm mục tiêu.

**Python ≥ 3.10** · **Streamlit** · **B0–B3 / LNS / ALNS / VNS / Exact**

## Mục lục

- [Cài đặt và khởi chạy](#cài-đặt-và-khởi-chạy)
- [Chức năng chính](#chức-năng-chính)
- [Sử dụng demo](#sử-dụng-demo)
- [Sử dụng CLI](#sử-dụng-cli)
- [Mô hình và thuật toán](#mô-hình-và-thuật-toán)
- [Dữ liệu và kịch bản kho](#dữ-liệu-và-kịch-bản-kho)
- [Thực nghiệm và báo cáo](#thực-nghiệm-và-báo-cáo)
- [Kiểm thử và kiểm chứng](#kiểm-thử-và-kiểm-chứng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Tài liệu và đóng góp](#tài-liệu-và-đóng-góp)

## Cài đặt và khởi chạy

Tải hoặc clone repository, sau đó mở terminal tại thư mục gốc chứa `README.md` và `pyproject.toml`.

### Windows — PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run demo/app.py
```

Các lệnh trên gọi trực tiếp Python trong môi trường ảo. Với những lệnh `python` ở các phần sau, hãy dùng `.\.venv\Scripts\python.exe` hoặc kích hoạt môi trường bằng `.\.venv\Scripts\Activate.ps1`.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run demo/app.py
```

### Môi trường Conda có sẵn

Nếu đã có môi trường `TTUD`, chạy trong Anaconda Prompt hoặc terminal đã cấu hình Conda:

```text
conda activate TTUD
python -m pip install -r requirements.txt
python -m streamlit run demo/app.py
```

Mở [http://localhost:8501](http://localhost:8501) để sử dụng demo. Dữ liệu tổng hợp được sinh trực tiếp, nên có thể chạy thử ngay mà không cần tải benchmark gốc.

Phần thuật toán và CLI chỉ dùng thư viện chuẩn Python. `requirements.txt` bổ sung Streamlit, Matplotlib, pandas và pytest để chạy giao diện, vẽ biểu đồ và kiểm thử. Chi tiết phiên bản nằm trong [requirements.txt](requirements.txt) và [pyproject.toml](pyproject.toml).

## Chức năng chính

- **Tối ưu tích hợp:** quyết định cách gom đơn vào chuyến, tuyến lấy hàng và thứ tự chuyến của từng nhân viên.
- **So sánh thuật toán:** các baseline B0–B3, LNS, ALNS, VNS và bộ giải exact cho bài toán nhỏ.
- **Điều chỉnh mục tiêu:** cân bằng ba tiêu chí hoặc ưu tiên quãng đường, thời gian hoàn tất hay tổng độ trễ.
- **Mô phỏng nghiệm:** phát lại đường đi trên đồ thị kho, điểm lấy hàng và tải trọng; hỗ trợ tua, đổi tốc độ, zoom, pan và lọc nhân viên.
- **Kiểm định độc lập:** kiểm tra phân công đơn, sức chứa, đường đi vật lý, thời gian và các chỉ tiêu của nghiệm xuất ra.
- **Thực nghiệm có truy vết:** lưu nghiệm thô, seed, cấu hình, manifest, bảng so sánh và biểu đồ; kiểm tra lại kết quả từ dữ liệu đã lưu.

## Sử dụng demo

1. **Chọn nguồn dữ liệu** ở thanh bên: dữ liệu tổng hợp, catalog Kris hoặc file instance JSON tải lên.
2. **Thiết lập bài toán:** với dữ liệu tổng hợp, chọn kịch bản kho, số đơn, số nhân viên và sức chứa mỗi chuyến.
3. **Điều chỉnh mục Nâng cao:** chọn seed, độ nới hạn, ngân sách tìm kiếm và ưu tiên tối ưu. Bật so sánh nếu cần chạy đủ `B0/B2/LNS/ALNS/VNS`; mặc định demo chạy B0 và ALNS.
4. **Chọn Chạy tối ưu**, sau đó xem kết quả và tải dữ liệu.

| Tab | Nội dung |
|---|---|
| Mô phỏng động | Phát lại tuyến đi và hoạt động lấy hàng của từng nhân viên. |
| Tổng quan | Quãng đường, thời gian hoàn tất, số đơn trễ, bảng so sánh và hội tụ hàm mục tiêu. |
| Tuyến & lịch | Tuyến từng chuyến và lịch làm việc của các nhân viên. |
| Chi tiết | Thông tin chuyến, đơn hàng và hàng hóa. |

Có thể tải nghiệm JSON, dữ liệu đầu vào hoặc snapshot toàn bộ lần chạy. Khi đổi tham số hay ưu tiên mục tiêu, cần chạy lại để nhận kết quả theo cấu hình mới. Ngân sách tìm kiếm được áp dụng riêng cho từng thuật toán.

### Quy ước đơn vị hiển thị

Dữ liệu tổng hợp khai báo khoảng cách bằng mét và thời gian bằng phút. Với Kris, demo áp dụng quy ước dự án **10 đơn vị khoảng cách = 1 m** và **30 đơn vị thời gian = 1 giây**, được ghi trên giao diện; hệ số này chưa được tác giả benchmark xác nhận là quy đổi vật lý.

JSON tải lên được hiển thị theo đơn vị đã khai báo; đơn vị thời gian chưa biết giữ nguyên giá trị và nhãn. Số sản phẩm tính theo quantity, còn tải trọng tính theo `size × quantity`. Thời gian chạy thuật toán được báo riêng bằng giây. Quy đổi hiển thị giữ nguyên dữ liệu xuất JSON, điểm mục tiêu, số đơn trễ và kết quả benchmark.

## Sử dụng CLI

Chạy các lệnh dưới đây từ thư mục gốc bằng Python của môi trường đã cài đặt.

### Sinh dữ liệu, giải và kiểm tra nghiệm

```text
python -m src generate --scenario double_block --orders 20 --pickers 4 --capacity 30 --seed 42 --output data/synthetic/my_run.json
python -m src solve data/synthetic/my_run.json --method ALNS --seconds 5 --iterations 100000 --seed 42 --output results/my_solution.json
python -m src validate data/synthetic/my_run.json results/my_solution.json
```

Lệnh `validate` tính lại các ràng buộc và chỉ tiêu từ nghiệm đã lưu. Vì bài toán dùng hạn mềm, một nghiệm hợp lệ vẫn có thể chứa đơn trễ.

### Chọn ưu tiên tối ưu

```text
python -m src solve data/synthetic/my_run.json --method VNS --profile tardiness --seconds 3 --iterations 100000 --output results/tardiness.json
```

| Profile | Ý nghĩa | Trọng số: quãng đường / makespan / tổng trễ |
|---|---|---|
| `balanced` | Cân bằng, mặc định | 1/3 · 1/3 · 1/3 |
| `distance` | Ưu tiên giảm quãng đường | 0.6 · 0.2 · 0.2 |
| `makespan` | Ưu tiên hoàn tất sớm | 0.2 · 0.6 · 0.2 |
| `tardiness` | Ưu tiên giảm tổng độ trễ | 0.2 · 0.2 · 0.6 |

Có thể thay `--profile` bằng `--weights 0.5 0.3 0.2`. Ba trọng số phải dương, hữu hạn và có tổng bằng 1. Tìm kiếm dừng khi đạt giới hạn thời gian hoặc số vòng; `solve` mặc định có trần 200 vòng nếu không truyền `--iterations`.

### Giải exact cho instance nhỏ

```text
python -m src exact data/synthetic/tiny_4.json --profile balanced --output results/tiny_exact.json
```

Bộ giải joint exact giới hạn **tối đa 6 đơn và 8 vị trí SKU ngoài depot**. Chỉ diễn giải optimality gap khi `certified_optimal=true` và hai nghiệm dùng cùng instance, trọng số và chuẩn hóa mục tiêu.

Tra cứu đầy đủ tham số:

```text
python -m src --help
python -m src solve --help
```

## Mô hình và thuật toán

Mỗi đơn được đưa vào đúng một chuyến; tải của chuyến không vượt sức chứa. Mỗi chuyến bắt đầu và kết thúc tại depot, đi trên đồ thị kho vô hướng có trọng số không âm. Các đơn cùng chuyến hoàn thành khi nhân viên trở về depot.

Hàm mục tiêu là tổng có trọng số của ba chỉ tiêu đã chuẩn hóa:

$$
\min F = w_D\frac{D}{D_{ref}} + w_C\frac{C_{max}}{C_{ref}} + w_T\frac{T}{T_{ref}}
$$

Trong đó `D` là tổng quãng đường, `C_max` là thời gian hoàn tất toàn bộ công việc và `T` là tổng độ trễ của các đơn. Các chuẩn tham chiếu lấy từ B0: `D_ref = max(D_B0, 1)`, `C_ref = max(C_B0, 1)`, `T_ref = n × C_ref`, với `n` là số đơn.

| Phương pháp | Cách tiếp cận |
|---|---|
| B0 | Gom đơn theo thứ tự rank, định tuyến nearest neighbor và phân công chuyến theo thời điểm nhân viên rảnh. |
| B1 | Gom đơn greedy theo khoảng cách tăng thêm, kết hợp nearest neighbor. |
| B2 | Gom đơn greedy và cải thiện tuyến bằng 2-opt. |
| B3 | Khởi tạo như B2, bổ sung tìm kiếm cục bộ để cải thiện nghiệm và lịch. |
| LNS | Phá hủy một phần nghiệm và tái chèn đơn bằng các toán tử repair. |
| ALNS | Khung LNS với xác suất chọn toán tử được điều chỉnh theo hiệu quả tìm kiếm. |
| VNS | Thay đổi cấu trúc lân cận để tìm kiếm trên cách gom đơn và lịch nhân viên. |
| Exact | Liệt kê phân hoạch đơn, phân công nhân viên và thứ tự chuyến; dùng tuyến exact cho mỗi chuyến. |

CLI còn hỗ trợ baseline S-Shape (`B-S`) và các biến thể ablation `ALNS_NO_SCHEDULE`, `ALNS_NO_2OPT`.

**Phạm vi mô hình:** mọi đơn có sẵn tại thời điểm 0, nhân viên đồng nhất; chưa mô hình hóa đơn phát sinh động, xung đột lối đi hay ca nghỉ. Số đơn trễ là chỉ tiêu báo cáo riêng, không phải thành phần trực tiếp của `F`. Giảm tổng trễ không bảo đảm giảm số đơn trễ; chỉ so điểm `F` khi dùng cùng instance và trọng số.

Đọc [ghi chú thuật toán](ALGORITHM_NOTES.md) để xem bất biến, độ phức tạp, điều kiện chứng nhận exact và ví dụ tính tay.

## Dữ liệu và kịch bản kho

### Dữ liệu tổng hợp

Năm kịch bản dùng trong demo được định nghĩa tại [src/generator.py](src/generator.py). Bảng sau ghi cấu hình mặc định; số đơn, số nhân viên và sức chứa có thể điều chỉnh.

| Kịch bản | Bố trí | Số đơn | Nhân viên | Sức chứa/chuyến |
|---|---|---:|---:|---:|
| `single_block` | 5 dãy × 6 hàng, một khối | 10 | 3 | 20 |
| `double_block` | 6 dãy × 8 hàng, một lối ngang giữa kho | 30 | 3 | 25 |
| `mega_hub` | 10 dãy × 16 hàng, hai lối ngang giữa kho | 40 | 5 | 30 |
| `rush_hour` | 6 dãy × 8 hàng, hạn giao gấp (`tightness=0.06`) | 25 | 4 | 20 |
| `abc_zonal` | 6 dãy × 10 hàng, nhu cầu tập trung gần depot | 35 | 4 | 25 |

`rush_hour` là instance tĩnh với deadline chặt. `abc_zonal` giả định khoảng 20% SKU gần depot chiếm 70% lượt chọn hàng, với độ gần tính trên đồ thị. Các kịch bản này phục vụ kiểm thử và nghiên cứu trên dữ liệu sinh nhân tạo.

### Benchmark Kris

Catalog của đồ án gồm **18 instance Kris Small**, với 6 file cho mỗi nhóm 6, 12 và 18 đơn. Danh sách cố định và quy tắc chọn được lưu trong [kris_selection.json](data/processed/kris_selection.json); demo và benchmark đọc [catalog.json](data/processed/kris_small/catalog.json).

Bộ chuyển đổi giữ số lượng, thời hạn và tham số nguồn. Tuy nhiên, dự án nghiên cứu biến thể hạn mềm với hàm mục tiêu riêng, nên kết quả không được xem là tái lập điểm số hay nghiệm tối ưu của bài toán nguồn JOBPRSP-D.

Xem [tài liệu dữ liệu](data/README.md) để tra cứu nguồn, định dạng, checksum và giới hạn chuyển đổi. Archive gốc trong `data/raw/` được giữ local; để tạo lại JSON từ dữ liệu gốc đã có, chạy `python scripts/prepare_kris.py`.

## Thực nghiệm và báo cáo

Mỗi đợt chạy cần một thư mục kết quả mới để giữ nguyên bằng chứng. Benchmark tổng quát chấp nhận thư mục mới hoặc rỗng; các runner map và Kris yêu cầu đường dẫn chưa tồn tại.

### Kiểm tra nhanh pipeline

```text
python -m src benchmark --config configs/smoke.json --output results/benchmark_smoke_run
python scripts/build_comparison_report.py --benchmark results/benchmark_smoke_run --output results/benchmark_smoke_report
```

Smoke dùng để kiểm tra pipeline và tạo bảng, biểu đồ mẫu. Số liệu nghiên cứu phải lấy từ cấu hình thực nghiệm tương ứng.

### Benchmark năm kịch bản demo

```text
python scripts/benchmark_maps.py --seconds 1.0 --search-seeds 1 --output results/map_quick_run
```

Để chạy cấu hình đầy đủ, bỏ `--seconds` và `--search-seeds`, đồng thời chọn output mới. [Cấu hình mặc định](configs/map_scenarios_benchmark.json) dùng seed dữ liệu 42 và 10 search seed: B0/B2 chạy một lần, LNS/ALNS/VNS chạy theo từng seed, tổng cộng **160 lượt chạy**.

### Benchmark Kris

```text
python scripts/benchmark_kris.py --limit-per-size 1 --seconds 1.0 --output results/kris_quick_run
```

Để chạy toàn bộ catalog, bỏ `--limit-per-size` và chọn output mới. Với 18 instance, năm phương pháp và ba search seed mặc định, runner tạo **198 lượt chạy**.

Cả hai runner tự xuất báo cáo và biểu đồ vào `<output>_report/`. Những tệp chính gồm:

| Tệp | Nội dung |
|---|---|
| `REPORT.md` | Phạm vi dữ liệu, số lượt chạy và thông tin kiểm chứng. |
| `comparison.csv` | Thắng/hòa/thua và mức cải thiện giữa các phương pháp. |
| `comparison_pairs.csv` | So sánh từng cặp phương pháp trên từng instance. |
| `per_instance.csv` | Thống kê theo instance và thuật toán. |
| `raw_metrics.csv` | Chỉ tiêu từng lượt chạy sau kiểm định. |
| `charts/` | Biểu đồ mục tiêu, thắng/hòa/thua và lịch nhân viên. |

### Nghiên cứu chất lượng chương trình

```text
python scripts/run_research.py all --protocol configs/coursework_quality.json --output results/quality_new/study
python scripts/analyze_quality.py --study results/quality_new/study --output results/quality_new/diagnostics
```

[Protocol chất lượng](configs/coursework_quality.json) tách seed tuning/holdout, kiểm tra 30/100/300 đơn trên hai layout và hai mức deadline, đồng thời có ablation, độ nhạy trọng số và exact nhỏ. Pipeline khóa dữ liệu và mã nguồn trước khi chạy; preset được chọn trên tuning rồi khóa trước holdout.

Đợt nghiên cứu ngày 01/10/2026 ghi nhận **704 nghiệm nghiên cứu và 39 nghiệm diagnostics**. Trên tập holdout đã chạy, ALNS cải thiện `F` trung bình khoảng **26,41% so với B0** và **3,66% so với B2**; VNS đạt `F` tốt hơn ALNS. Xem [QUALITY_RESULTS.md](QUALITY_RESULTS.md) để đọc phương pháp thống kê, bằng chứng và giới hạn diễn giải.

Ba kích thước dùng chung seed nhu cầu; suy luận thống kê dựa trên 12 nhóm seed trong bốn điều kiện. Các instance và search seed không được coi là những quan sát độc lập. Số đo bộ nhớ bằng `tracemalloc` chỉ phản ánh phần cấp phát Python được theo dõi.

[research_completion.json](configs/research_completion.json) là protocol nghiên cứu riêng với 10 search seed. Có thể chạy bằng cùng lệnh `run_research.py all`, thay đường dẫn protocol và dùng output mới. Kết quả mỗi đợt gắn với phiên bản nguồn trong manifest.

## Kiểm thử và kiểm chứng

### Chạy test suite

```text
python -m pytest -q
```

Các test bao phủ đồ thị và định tuyến, toán tử tìm kiếm, ràng buộc nghiệm, mục tiêu, adapter dữ liệu, pipeline thực nghiệm, trạng thái demo, đơn vị hiển thị và timeline mô phỏng.

[Hồ sơ chất lượng](QUALITY_RESULTS.md) ghi nhận **229 test đạt, không skip** trong lần kiểm tra ngày 02/10/2026. Đây là kết quả của lần kiểm tra được ghi lại; số test có thể thay đổi khi mã nguồn được cập nhật.

### Kiểm lại bằng chứng đã lưu

Nếu workspace có đợt thực nghiệm tương ứng:

```text
python scripts/run_research.py verify --output results/coursework_quality_20261001/study
python scripts/analyze_quality.py --verify --study results/coursework_quality_20261001/study --output results/coursework_quality_20261001/diagnostics
```

Chế độ audit kiểm snapshot nguồn lịch sử, dữ liệu và nghiệm thô, rồi tái tính bảng kết quả. Các lệnh kiểm chứng trên chỉ đọc bằng chứng. Muốn chạy tiếp một nghiên cứu, toàn bộ source phải khớp lock; khi source thay đổi, tạo đợt mới.

Với gói nộp đã giải nén và cài dependencies:

```text
python scripts/verify_submission.py .
python -m pytest -q
python -m streamlit run demo/app.py
```

Validator và checksum xác nhận nghiệm phù hợp mô hình và tính toàn vẹn của tệp. Chứng nhận tối ưu chỉ có khi bộ giải exact duyệt hoàn tất không gian tìm kiếm.

## Cấu trúc dự án

```text
TTUD_v2/
├── demo/                    # Giao diện Streamlit và mô phỏng Canvas
│   ├── app.py               # Điểm khởi chạy
│   ├── components.py        # Điều khiển, bảng và biểu đồ
│   ├── simulation.py        # Phát lại tuyến đi và hoạt động lấy hàng
│   └── state.py             # Trạng thái và luồng chạy demo
├── src/                     # Thuật toán, CLI và kiểm định
│   ├── models.py            # Mô hình dữ liệu và đọc/ghi JSON
│   ├── generator.py         # Sinh dữ liệu và kịch bản kho
│   ├── graph.py             # Đồ thị và đường đi ngắn nhất
│   ├── routing.py           # NN, 2-opt, S-Shape và tuyến exact
│   ├── heuristics.py        # Gom đơn và phân công chuyến cơ sở
│   ├── search.py            # LNS và ALNS
│   ├── vns.py               # Variable Neighborhood Search
│   ├── exact.py             # Joint exact cho instance nhỏ
│   ├── evaluator.py         # Tính lịch và hàm mục tiêu
│   ├── validator.py         # Kiểm định nghiệm độc lập
│   ├── benchmark.py         # Chạy và tổng hợp thực nghiệm
│   └── cli.py               # Giao diện dòng lệnh
├── configs/                 # Cấu hình benchmark và protocol
├── data/                    # Instance tổng hợp, Kris và metadata
├── scripts/                 # Runner, báo cáo và đóng gói bằng chứng
├── tests/                   # Test suite và kiểm thử hồi quy
├── results/                 # Kết quả sinh khi chạy, được Git bỏ qua
├── ALGORITHM_NOTES.md       # Mô hình, thuật toán và bất biến
├── QUALITY_RESULTS.md       # Kết quả kiểm chứng và giới hạn
├── pyproject.toml           # Metadata package và cấu hình công cụ
└── requirements.txt         # Thư viện cho demo và kiểm thử
```

## Tài liệu và đóng góp

- [Ghi chú mô hình và thuật toán](ALGORITHM_NOTES.md).
- [Kết quả chất lượng và hướng dẫn kiểm chứng](QUALITY_RESULTS.md).
- [Nguồn dữ liệu và giới hạn benchmark](data/README.md).
- [Cấu hình nghiên cứu chất lượng](configs/coursework_quality.json).

Khi đóng góp, mô tả thay đổi, bổ sung kiểm thử phù hợp và chạy test suite trước khi gửi pull request. Với thay đổi thuật toán hoặc cách tính chỉ tiêu, cập nhật tài liệu và tạo đợt thực nghiệm mới để có bằng chứng cho phiên bản mới.

Dự án phục vụ học tập và nghiên cứu. Repository hiện chưa có tệp `LICENSE`; quyền sử dụng và phân phối dữ liệu benchmark cần được xem xét theo điều kiện của nguồn dữ liệu.
