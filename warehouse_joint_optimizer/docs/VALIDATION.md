# Kiểm chứng bản triển khai 0.1.0

Ngày kiểm chứng: 12/09/2026. Interpreter: Python 3.12.14 trên Windows. Toàn bộ mã và output của bản triển khai nằm trong project `warehouse_joint_optimizer`.

## Cập nhật: dữ liệu tác giả đã đưa vào project

Sau lượt kiểm chứng tổng hợp bên dưới, đã tải và kiểm tra CRC/checksum **904 file gốc** từ bốn archive Foodmart, HappyChic, Kris Small corrected và Kris Large corrected. [Nguồn và manifest](../data/README.md).

Adapter đã đọc/chuyển **243/243 Kris Small** (81 instance mỗi kích thước 6/12/18 đơn), giữ nguyên dữ liệu đơn/SKU/due dates và tham số vận hành. Chỉ gộp hai bản sao depot sau khi kiểm tra tọa độ, hướng và trọng số cạnh; khoảng cách nhập được kiểm thử đối chiếu với ma trận shortest-path trong file tác giả.

Kết quả kiểm thử mới nhất: **68 passed**. Có thêm kiểm tra preservation của các giá trị nguồn, từ chối depot không tương đương, chạy sáu method trên dữ liệu tác giả và AppTest với nguồn Kris mặc định.

[Benchmark tích hợp Kris](../results/kris_author/REPORT.md): 18 nghiệm (6 method × 3 instance đại diện 6/12/18 đơn) đã qua validator, seed 42 và giới hạn 1 giây/100 vòng. Đơn vị khoảng cách và thời gian giữ theo nguồn. Project dùng mục tiêu hạn mềm nên không gọi kết quả này là tái lập điểm số của JOBPRSP-D hạn cứng.

Các mục phía dưới ghi lại lượt kiểm chứng **trên dữ liệu tổng hợp trước khi bổ sung adapter**; không đổi nguồn gốc các số liệu lịch sử đó.

## Kiểm thử đã chạy

`python -m pytest -q -p no:cacheprovider`: **58 passed**, gồm test core, CLI, exact oracle và thao tác chạy/chuyển kết quả trong Streamlit AppTest.

Core đã chạy và xuất/kiểm tra nghiệm với `python -S -m warehouse_opt ...`, tức tắt nạp site-packages. Điều này xác nhận đường chạy B0/core không cần NumPy, Pandas, Streamlit hay mã nguồn của project khác.

Đã build wheel thành công bằng pip với `--no-index --no-deps --no-build-isolation`. File cài đặt nằm trong [dist](../dist/warehouse_joint_optimizer-0.1.0-py3-none-any.whl).

## Benchmark đã hoàn thành

| Bộ chạy | Kích thước | Instance | Seed search | Số nghiệm |
|---|---|---:|---:|---:|
| Smoke | 20, 50, 100, 200 đơn | 1 mỗi kích thước | 1 | 28 |
| Replication | 20 đơn | 5 | 10 mỗi method ngẫu nhiên | 265 |

**293/293 nghiệm** từ hai bộ chạy đã được đọc lại từ JSON cùng instance tương ứng và kiểm tra độc lập: coverage đơn, capacity, physical walk, thời gian xử lý, lịch nối tiếp, hoàn thành và độ trễ từng đơn, tổng metrics và công thức F.

- [Báo cáo smoke](../results/smoke/REPORT.md)
- [Báo cáo replication](../results/replication/REPORT.md)
- Mỗi thư mục có config, instance, raw result và manifest để kiểm tra lại.

Đây là thực nghiệm kiểm chứng ban đầu. Ngân sách ngắn (smoke 1 giây; replication 0,3 giây), máy không được cô lập tải và các lượt đầu của hai bộ được chạy đồng thời. Vì vậy, không dùng runtime này để kết luận hiệu năng phần cứng hoặc ưu thế thuật toán tổng quát. Khi đo cho báo cáo nghiên cứu, chạy tuần tự trong môi trường được kiểm soát và dùng cấu hình/tập test đã chốt.

Cấu hình `configs/full.json` đã chuẩn bị nhưng **chưa chạy**; không tính vào số liệu trên. Chưa có kết quả Foodmart/HappyChic/Zalando.

## Ví dụ 30 đơn có thể tái lập theo số vòng

Instance [demo_30.json](../data/synthetic/demo_30.json): seed 42, 3 picker, capacity 20, 5 aisle × 6 vị trí, tightness 0,1. Search dùng 150 vòng, seed 42, không giới hạn thời gian, candidate limit 16; cấu hình đầy đủ lưu trong từng JSON.

| Method | F | Distance (m) | Makespan (min) | Total tardiness (min) | Late orders |
|---|---:|---:|---:|---:|---:|
| B0 | 0,74908 | 1432 | 17,513 | 129,905 | 20 |
| B1 | 0,60200 | 1080 | 15,633 | 83,627 | 16 |
| B2 | 0,58659 | 1048 | 15,293 | 81,274 | 16 |
| B3 | 0,57033 | 1048 | 14,460 | 80,641 | 16 |
| LNS | 0,52105 | 984 | 13,207 | 64,055 | 15 |
| ALNS | 0,54151 | 1000 | 13,773 | 73,431 | 20 |

ALNS cải thiện F và tổng độ trễ so với B0 nhưng không giảm số đơn trễ trong ví dụ này. LNS tốt hơn ALNS trên seed/cấu hình này. Điều đó phù hợp với việc tối ưu tổng có trọng số, không có cam kết luôn thắng mọi heuristic hoặc luôn giảm mọi metric.

Kết quả và ảnh được tạo bằng `python scripts/create_demo_assets.py`:

- [ALNS JSON](../results/demo/ALNS.json)
- [Tuyến của batch đầu tiên](../results/demo/warehouse.png)
- [Gantt picker](../results/demo/schedule.png)
- [Đường hội tụ](../results/demo/convergence.png)

Ảnh tuyến và Gantt đã được mở kiểm tra: tuyến đi trên lối kho, vị trí được đánh số, lịch không chồng lấn trên từng picker. Demo được kiểm tra bằng AppTest; chưa thực hiện vòng kiểm tra thủ công trên nhiều trình duyệt/thiết bị.

## Oracle trên bài toán nhỏ

[tiny_4.json](../data/synthetic/tiny_4.json) có 4 đơn, 2 picker, 4 vị trí SKU. Oracle duyệt **144 trạng thái phân hoạch/phân công/thứ tự**, với routing được vét cạn cho mỗi tập vị trí, kết thúc với `certified_optimal=true`. [Kết quả](../results/demo/tiny_exact.json).

Unit tests còn so nghiệm joint tối ưu với trường hợp tính tay và kiểm tra các heuristic không báo F thấp hơn oracle trên một instance nhỏ cùng hệ số chuẩn hóa.

## Giới hạn tại lượt kiểm chứng tổng hợp ban đầu

- Dữ liệu hiện tại là tổng hợp; adapter benchmark ngoài chưa triển khai.
- Chưa có congestion, nhiều depot, picker không đồng nhất, split order hoặc release times.
- ALNS dùng heuristic route decoder, không chứng minh tối ưu toàn cục.
- Cache chưa giới hạn dung lượng; thời gian giới hạn được kiểm tra giữa các thao tác.
- Ablation `ALNS_NO_SCHEDULE` bỏ local search lịch, nhưng vẫn để repair đặt batch lên lịch; không được diễn giải là đóng băng assignment hoàn toàn.
- Thí nghiệm độ nhạy rộng trên picker/capacity/due dates và kiểm định thống kê nghiên cứu chưa nằm trong các kết quả đã chạy.
