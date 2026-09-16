# Warehouse Joint Optimizer

Ứng dụng thử nghiệm giúp **gom đơn hàng thành từng chuyến, tìm đường lấy hàng và chia lịch cho nhân viên trong kho**. Bạn có thể xem sơ đồ đường đi, lịch làm việc và các đơn bị trễ ngay trên trình duyệt.

**Người dùng lần đầu chỉ cần làm mục 1 và 2.** Các mục sau dành cho chạy bằng lệnh và tìm hiểu thêm.

### Nếu đã có môi trường Conda `TTUD`

Mở **Anaconda Prompt** và chạy:

```powershell
conda activate TTUD
cd <duong-dan-toi>\warehouse_joint_optimizer
python -m pip install -r requirements.txt
python -m streamlit run demo/app.py
```

Nếu dùng `TTUD`, bỏ qua bước tạo `.venv` bên dưới và dùng `python` sau khi activate.

## 1. Cài đặt và mở ứng dụng

### Chuẩn bị

- Cài **Python 3.10 trở lên**; Python 3.12 là lựa chọn phù hợp để bắt đầu. Khi cài trên Windows, chọn **Add Python to PATH**.
- Có kết nối Internet để tải thư viện trong lần cài đầu tiên.
- Các lệnh bên dưới dùng **PowerShell trên Windows**. Chạy lần lượt từng dòng.

### Bước 1 — Mở đúng thư mục

Mở PowerShell và chuyển vào thư mục chứa `requirements.txt` và `demo`:

```powershell
cd <duong-dan-toi>\warehouse_joint_optimizer
```

Nếu bạn lưu dự án ở nơi khác, thay đường dẫn trên bằng đường dẫn của bạn. Trong VS Code, bạn cũng có thể mở thư mục `warehouse_joint_optimizer`, rồi chọn **Terminal → New Terminal**.

Kiểm tra Python:

```powershell
python --version
```

Bạn cần thấy kết quả dạng `Python 3.12.x` (hoặc phiên bản từ 3.10 trở lên). Nếu báo không tìm thấy Python, xem mục **Lỗi thường gặp** bên dưới.

### Bước 2 — Cài thư viện (chỉ cần làm lần đầu)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`.venv` là môi trường Python riêng của dự án. Chờ lệnh cài đặt kết thúc rồi mới chạy bước tiếp theo. Các lệnh dùng trực tiếp Python trong `.venv`, nên **không cần chạy lệnh activate**.

### Bước 3 — Mở giao diện

```powershell
.\.venv\Scripts\python.exe -m streamlit run demo/app.py
```

Trình duyệt thường tự mở. Nếu chưa mở, truy cập **http://localhost:8501** hoặc địa chỉ `Local URL` xuất hiện trong terminal.

**Giữ terminal mở khi sử dụng ứng dụng.** Muốn dừng, quay lại terminal và nhấn `Ctrl+C`.

### Những lần mở sau

Không cần cài lại thư viện. Chỉ chạy:

```powershell
cd <duong-dan-toi>\warehouse_joint_optimizer
.\.venv\Scripts\python.exe -m streamlit run demo/app.py
```

<details>
<summary>Nếu dùng macOS hoặc Linux</summary>

Mở terminal tại thư mục `warehouse_joint_optimizer`, rồi chạy:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m streamlit run demo/app.py
```

Với các ví dụ Windows bên dưới, thay `.\.venv\Scripts\python.exe` bằng `./.venv/bin/python`.

</details>

## 2. Chạy thử lần đầu

Để làm quen mà không cần chuẩn bị dữ liệu:

1. Ứng dụng mở sẵn **Dữ liệu tổng hợp — chỉ kiểm thử**, 10 đơn, 3 nhân viên, sức chứa 20.
2. Bấm **Chạy tối ưu** ở thanh bên hoặc **Chạy với cấu hình này** trong nội dung chính. Trên điện thoại, mở thanh bên bằng nút góc trên trái nếu muốn đổi dữ liệu.
3. Xem ba chỉ số **Đơn trễ**, **Thời gian hoàn tất**, **Quãng đường**. Trong **Phương án đang xem**, chọn `ALNS` hoặc `B0` để đối chiếu.
4. Mở **Tuyến & lịch** để xem một chuyến; mở **Tải kết quả** để tải nghiệm, dữ liệu đầu vào hoặc toàn bộ lần chạy.

Mặc định chỉ chạy B0 + ALNS. Muốn thử VNS hoặc nhiều thuật toán, mở **Nâng cao** trong thanh bên. Khi sửa cấu hình, kết quả cũ được giữ nguyên và có thông báo chưa áp dụng; bấm chạy lại để tạo kết quả mới.

Các khu vực kết quả:

| Khu vực | Bạn có thể xem gì? |
|---|---|
| Tổng quan | Số chuyến, nhân viên được phân công và số đơn đúng hạn |
| Phân tích thuật toán (trong Tổng quan) | Điểm F, bảng đối chứng và biểu đồ hội tụ; đóng mặc định |
| Tuyến & lịch | Mặc định một chuyến, lọc nhân viên/chuyến và xem lịch làm việc |
| Chi tiết | Bảng đơn, bộ lọc đơn trễ và thông tin từng chuyến |
| Tải kết quả | Tải nghiệm, dữ liệu đầu vào hoặc snapshot toàn bộ lần chạy |

**Picker** là nhân viên lấy hàng. **Batch** là nhóm đơn được lấy trong cùng một chuyến. **Instance** là một bộ dữ liệu gồm kho, hàng hóa, đơn hàng và thông số vận hành.

### Đọc kết quả như thế nào?

- **Hàm mục tiêu F:** điểm tổng hợp; thấp hơn là tốt hơn khi so sánh trên cùng dữ liệu và cùng cấu hình trọng số.
- **Quãng đường:** tổng đường đi của tất cả các chuyến.
- **Makespan:** thời điểm nhân viên cuối cùng hoàn thành công việc.
- **Tổng độ trễ:** tổng thời gian trễ hạn của các đơn.
- **Đơn trễ:** số đơn hoàn thành sau hạn.

Ứng dụng dùng **hạn mềm**: nghiệm hợp lệ vẫn có thể có đơn trễ. Một phương án có F thấp hơn cũng không nhất thiết tốt hơn ở mọi chỉ số.

### Chọn dữ liệu khác

| Nguồn dữ liệu | Cách dùng |
|---|---|
| Kris — benchmark tác giả | Chọn một bộ trong **Bộ dữ liệu Kris**, rồi bấm **Chạy tối ưu** |
| JSON tải lên | Chọn nguồn này và tải file đúng [định dạng JSON của dự án](docs/SCHEMA.md) |
| Dữ liệu tổng hợp — chỉ kiểm thử | Nguồn mặc định; tự tạo dữ liệu từ số đơn, số nhân viên, sức chứa và độ nới hạn |

**Số đơn, số nhân viên, sức chứa và độ nới hạn chỉ hiện khi dùng dữ liệu tổng hợp.** Với Kris hoặc JSON tải lên, các giá trị này được lấy từ file. Seed, ngân sách và thuật toán nằm trong **Nâng cao**.

Dữ liệu tổng hợp dùng mét/phút. Kris giữ nguyên đơn vị nguồn, không tự quy đổi sang mét/phút. Kết quả Kris sử dụng mục tiêu hạn mềm của dự án, không phải điểm đối chiếu trực tiếp với bài toán hạn cứng của tác giả.

## 3. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `python` không được nhận diện hoặc mở Microsoft Store | Thử `py --version`. Nếu có Python từ 3.10, dùng `py -m venv .venv` ở bước tạo môi trường. Nếu chưa có, cài Python và mở lại terminal |
| Không tìm thấy `requirements.txt` hoặc `demo/app.py` | Chuyển vào đúng thư mục `warehouse_joint_optimizer` trước khi chạy |
| `No module named streamlit` | Chạy lại `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, rồi mở ứng dụng bằng đúng Python trong `.venv` |
| PowerShell chặn `Activate.ps1` | Không cần activate; dùng nguyên các lệnh `.\.venv\Scripts\python.exe` ở trên |
| Trình duyệt không tự mở | Sao chép địa chỉ `Local URL` từ terminal vào trình duyệt |
| Cổng 8501 đang được sử dụng | Thêm `--server.port 8502` vào cuối lệnh mở Streamlit, rồi truy cập `http://localhost:8502` |
| Chưa có catalog Kris | Chọn **Dữ liệu tổng hợp — chỉ kiểm thử** để chạy ngay; xem [hướng dẫn dữ liệu](data/README.md) để chuẩn bị Kris |
| Không thấy nút mở lần chạy đã lưu | Nút chỉ hiện khi có `results/demo_vns/snapshot.json`; vẫn có thể chạy trực tiếp bình thường |
| Chạy lâu | Thử 10 đơn tổng hợp, giảm ngân sách mỗi search và bỏ chọn chạy thêm thuật toán. Ngân sách áp dụng riêng cho từng search, không phải toàn bộ lần chạy |
| JSON bị từ chối | Kiểm tra [schema](docs/SCHEMA.md): SKU/vị trí phải tồn tại, kho phải liên thông và mỗi đơn phải vừa sức chứa xe |

## 4. Chạy bằng dòng lệnh (tùy chọn)

Các lệnh dưới đây chạy tại thư mục `warehouse_joint_optimizer`, sau bước cài đặt ở mục 1. Không cần mở Streamlit.

### Tạo dữ liệu → tối ưu → kiểm tra kết quả

```powershell
.\.venv\Scripts\python.exe -m warehouse_opt generate --orders 10 --pickers 3 --capacity 20 --seed 42 --output data/synthetic/first_run.json
.\.venv\Scripts\python.exe -m warehouse_opt solve data/synthetic/first_run.json --method ALNS --seconds 3 --output results/first_run.json
.\.venv\Scripts\python.exe -m warehouse_opt validate data/synthetic/first_run.json results/first_run.json
```

Sau khi chạy:

- `data/synthetic/first_run.json` chứa dữ liệu đầu vào.
- `results/first_run.json` chứa tuyến, lịch, các đơn và chỉ số kết quả.
- Lệnh cuối in `VALID: ...` nếu kết quả vượt qua kiểm tra độc lập.

Các thư mục đầu ra được tạo tự động. Chạy lại cùng đường dẫn sẽ ghi đè file đó; đổi tên sau `--output` nếu muốn giữ kết quả cũ.

### Thông số thường dùng

| Thông số | Ý nghĩa |
|---|---|
| `--orders 10` | Số đơn khi tạo dữ liệu tổng hợp |
| `--pickers 3` | Số nhân viên khi tạo dữ liệu tổng hợp |
| `--capacity 20` | Sức chứa mỗi chuyến khi tạo dữ liệu tổng hợp |
| `--method ALNS` | Thuật toán giải; có thể đổi thành `VNS`, `B0` hoặc các tên bên dưới |
| `--seconds 3` | Ngân sách tìm kiếm; thời gian thực tế còn phụ thuộc khởi tạo và thao tác đang chạy |
| `--seed 42` | Seed điều khiển lựa chọn ngẫu nhiên |
| `--seconds 0 --iterations 150` | Dừng theo số vòng, giúp tái lập plan/chỉ số với cùng dữ liệu, seed và phiên bản |
| `--weights 0.2 0.2 0.6` | Trọng số quãng đường, makespan, độ trễ; phải dương và tổng bằng 1 |

Xem đầy đủ tùy chọn:

```powershell
.\.venv\Scripts\python.exe -m warehouse_opt --help
.\.venv\Scripts\python.exe -m warehouse_opt solve --help
```

### Các thuật toán có sẵn

| Tên | Mô tả ngắn |
|---|---|
| B0 | Gom theo thứ tự nhận đơn, đi tới vị trí gần nhất và xếp lịch; làm mốc so sánh |
| B1 | Gom đơn theo phần quãng đường tăng thêm |
| B2 | B1, thêm cải tiến tuyến bằng 2-Opt |
| B3 | B2, thêm cải tiến lịch làm việc |
| LNS | Tháo một phần phương án rồi ghép lại để tìm phương án tốt hơn |
| ALNS | LNS với tần suất sử dụng các thao tác được điều chỉnh theo hiệu quả |
| VNS | Tìm kiếm bằng nhiều kiểu thay đổi đơn, chuyến và lịch |
| ALNS_NO_SCHEDULE | ALNS bỏ bước cải tiến cục bộ trên lịch; bước ghép lại vẫn có thể đổi lịch |
| ALNS_NO_2OPT | ALNS không dùng 2-Opt |
| B-S | Đi theo chính sách S-Shape; cần kho một block có cấu trúc tương thích |

## 5. Kiểm thử và tài liệu thêm

Chạy bộ kiểm thử:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Chạy benchmark mẫu và kiểm tra các kết quả vừa tạo:

```powershell
.\.venv\Scripts\python.exe -m warehouse_opt benchmark --config configs/smoke.json --output results/my_smoke
.\.venv\Scripts\python.exe scripts/check_results.py results/my_smoke
```

Benchmark chạy nhiều bộ dữ liệu/thuật toán nên lâu hơn một lần demo. Kết quả nằm trong `results/my_smoke`, gồm `REPORT.md`, `runs.csv`, `summary.json` và các nghiệm JSON. Tên các bộ dữ liệu trong một benchmark phải khác nhau.

Các tài liệu chi tiết:

- [Định dạng dữ liệu JSON](docs/SCHEMA.md)
- [Nguồn và cách chuẩn bị dữ liệu Kris](data/README.md)
- [Ghi chú kiểm chứng và kết quả thực nghiệm](docs/VALIDATION.md)
- [Thiết kế giao diện](DESIGN.md)
- [Kế hoạch và trạng thái nâng cấp](demo-upgrade-plan.md)
- [Đánh giá tổng quan và khả năng đạt điểm cao](DANH_GIA_TONG_QUAN_DU_AN.md)
- [Quyết định file đưa lên GitHub](GITHUB_UPLOAD_GUIDE.md)

### Các thư mục chính

```text
warehouse_joint_optimizer/
  demo/app.py       Giao diện trình duyệt
  warehouse_opt/    Thuật toán và lệnh xử lý
  data/             Dữ liệu đầu vào
  results/          Kết quả chạy
  configs/          Cấu hình benchmark
  tests/            Bộ kiểm thử
  docs/             Tài liệu chi tiết
```

### Phạm vi mô hình

Mô hình có một điểm xuất phát/trả hàng, nhân viên có cùng năng lực và tất cả đơn sẵn sàng từ đầu. Mỗi đơn nằm trọn trong một chuyến; đơn hoàn thành khi chuyến quay về và bàn giao xong. Chưa mô phỏng tắc nghẽn, tránh va chạm hoặc ca làm việc. Các thuật toán tìm kiếm không bảo đảm tìm được phương án tối ưu tuyệt đối.
