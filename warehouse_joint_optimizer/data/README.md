# Dữ liệu benchmark của tác giả

Các file trong **raw/** tải trực tiếp từ trang nghiên cứu của tác giả, được giữ nguyên byte. Manifest ghi URL, SHA-256 từng archive và từng file giải nén; script kiểm tra CRC trước khi giải nén. Không gọi các file sinh trong synthetic/ là benchmark tác giả.

| Bộ dữ liệu | File gốc đã giải nén | Đường dẫn |
|---|---:|---|
| Foodmart | 145 | [raw/FoodmartData](raw/FoodmartData/) |
| HappyChic | 279 | [raw/HappyChicData](raw/HappyChicData/) |
| Kris Small, corrected | 243 | [raw/KrisSmallDataCorrected/small](raw/KrisSmallDataCorrected/small/) |
| Kris Large, corrected | 237 | [raw/KrisLargeDataCorrected/large](raw/KrisLargeDataCorrected/large/) |

Tổng: **904 file**, không tính metadata/resource fork macOS. Bản ZIP nguyên gốc vẫn được giữ trong raw/. [Manifest và checksum](raw/manifest.json).

Kho GitHub public chỉ giữ manifest; archive raw và JSON đã chuyển đổi được xem là dữ liệu local tùy chọn. Chỉ tải và commit các bộ benchmark này khi đã xác nhận quyền phân phối; clone mới vẫn chạy demo ngay bằng dữ liệu tổng hợp nhỏ.

Nguồn Foodmart/HappyChic: [Joint order batching and picker routing — trang tác giả](https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/batching/). Nguồn Kris: [Joint batching, routing and sequencing problem — trang tác giả](https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/sequencing/index.html).

“Benchmark của tác giả” chỉ nguồn phân phối. Không khẳng định toàn bộ dữ liệu là log vận hành doanh nghiệp: benchmark gốc có thể do nhóm nghiên cứu xây dựng/sinh. Project này không tự tạo lại đơn, vị trí hay due dates của các file đó.

## Bộ có thể chạy ngay sau khi tải dữ liệu

**Kris Small:** 81 instance 6 đơn, 81 instance 12 đơn, 81 instance 18 đơn. Đã đọc/chuyển 243/243 instance sang JSON trong [processed/kris_small](processed/kris_small/), có [catalog](processed/kris_small/catalog.json).

Ví dụ:

- [File gốc instances_100_1.txt](raw/KrisSmallDataCorrected/small/instances_100_1.txt)
- [JSON tương ứng](processed/kris_small/instances_100_1.json)

Chạy từ thư mục project:

```powershell
python scripts/prepare_kris.py
python -m warehouse_opt solve data/processed/kris_small/instances_100_1.json --method ALNS --seconds 3 --output results/kris_solution.json
python -m warehouse_opt validate data/processed/kris_small/instances_100_1.json results/kris_solution.json
python scripts/benchmark_kris.py
python -m streamlit run demo/app.py
```

Demo mặc định dùng mẫu tổng hợp 10 đơn. Để dùng benchmark, chọn **Kris — benchmark tác giả**, rồi chọn **Bộ dữ liệu Kris**. Số nhân viên, sức chứa và hạn của từng đơn lấy từ file; các điều khiển sinh dữ liệu được ẩn khi chọn Kris.

## Cách chuyển đổi và giới hạn so sánh

[Format Kris của tác giả](https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/sequencing/data/format.txt) có SKU/location/size, order/quantity/due date/tardiness penalty, picker count/capacity, time per distance unit, setup/pick time và đồ thị.

Bộ đọc giữ số lượng, thời hạn và tham số nguồn; không randomize due dates. Hai node depot xuất phát/kết thúc chỉ được gộp khi trùng tọa độ và nối tới cùng một hàng xóm với cùng trọng số, không có hướng cạnh bất thường. Sau đó chỉ chấp nhận graph đối xứng. Đây là cách loại bản sao depot nguồn/đích trong biểu diễn, không di chuyển depot hay thêm lối tắt qua kệ. Test đối chiếu khoảng cách với ma trận shortest-path do tác giả cung cấp.

Khoảng cách/thời gian giữ **đơn vị nguồn**, chưa quy đổi sang mét/phút khi chưa xác nhận hệ số. Thời gian di chuyển = distance × TimeToTravelOneDistanceUnit; setup giữ nguyên; PickTime áp dụng trên từng đơn vị SKU; không cộng thêm thời gian tại vị trí ngoài file. Metadata ghi rõ cách diễn giải này để kiểm tra lại với paper.

**Quan trọng:** bài toán nguồn được mô tả với deadlines cứng, trong khi đề tài hiện tại cho phép trễ và tối ưu tổng có trọng số. Bộ đọc giữ alpha và penalty nguồn trong metadata nhưng không dùng chúng để thay hàm mục tiêu của project. Vì thế dùng được dữ liệu này để nghiên cứu biến thể hạn mềm, nhưng không tuyên bố tái lập nghiệm tối ưu/điểm số JOBPRSP-D của tác giả. [Mô tả bài toán nguồn](https://arxiv.org/abs/2303.17834).

Foodmart, HappyChic và Kris Large đã có **file gốc**. Phiên bản hiện tại chưa chuẩn bị toàn bộ chúng cho demo: Foodmart/HappyChic cần xử lý đúng capacity theo thùng và/hoặc graph có hướng; Kris Large cần kiểm tra và đo thêm ở quy mô lớn. Không tự đơn giản hóa các ràng buộc để ép chạy.

Zalando chưa tải được ở lượt này: yêu cầu tải bổ sung bị hệ thống duyệt tự động chặn do hạn mức. Không có file giả hoặc file rỗng thay thế.

## Dữ liệu tổng hợp cũ

synthetic/ vẫn giữ các instance kiểm thử nhỏ để kiểm tra hồi quy và tính tay. Các báo cáo cũ results/smoke, results/replication và results/demo là kết quả trên dữ liệu tổng hợp, không được đổi nhãn thành kết quả benchmark của tác giả.
