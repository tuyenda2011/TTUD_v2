# Quy trình đánh giá ALNS đã triển khai

## Câu hỏi cần trả lời

1. Thiết kế ALNS có cải thiện so với B0/B2/B3 trong cùng ngân sách không?
2. Cơ chế thích nghi có cải thiện so với LNS, và ALNS so với VNS như thế nào?
3. Từng destroy/repair operator, local search lịch và decoder tuyến đóng góp gì?
4. Đổi trọng số ảnh hưởng distance, makespan, tổng trễ và số đơn trễ ra sao?
5. Trên bài nhỏ có chứng nhận tối ưu, các heuristic cách tối ưu bao nhiêu?

## Cấu hình chốt trước

[research_protocol.json](../configs/research_protocol.json) là đầu vào đầy đủ.

| Phần | Dữ liệu | Seed search | Ngân sách khởi tạo + search |
|---|---|---|---|
| Tuning | 10/30/100 đơn; seed 7301 | 31, 32 | 2 giây; 3 cấu hình ứng viên |
| Holdout | 10/30/100 đơn; seed 8401, 8402 | 1–10 | 2 giây; B0/B2/B3/LNS/ALNS/VNS |
| Ablation | 30 đơn; seed 9501, 9502 | 1–10 | 1 giây; 10 biến thể |
| Sensitivity | 10/30/100 đơn; seed 8601 | 11–13 | 2 giây; 4 bộ trọng số |
| Exact + routing | 6 instance 4–6 đơn, 1–2 picker, 4 vị trí SKU | 42 cho heuristic | Heuristic 2 giây; oracle tối đa 60 giây/2 triệu trạng thái |

B0/B2 xác định nên mỗi instance chỉ chạy một lần; không nhân bản thành 10
“quan sát” giống nhau. Trần 100.000 vòng là điều kiện dừng phụ; số vòng không
đồng nghĩa lượng công việc ngang nhau giữa ALNS, B3 và VNS.

Trọng số chính bằng nhau được giữ làm lựa chọn mục tiêu công khai trước đo.
Không chọn trọng số theo “F nhỏ nhất” giữa các bộ trọng số vì các F đó đo những
mục tiêu khác nhau. Sensitivity so sánh trực tiếp chỉ số vật lý, và tập phương án
không bị phương án khác tốt hơn đồng thời ở mọi chỉ số (Pareto quan sát).

## Khóa dữ liệu và tránh dùng lại test để tuning

`scripts/run_research.py prepare` tạo tất cả dữ liệu, lưu SHA-256 từng instance,
cấu hình và hash mã nguồn vào `protocol.lock.json`, kèm checksum. Bản sao mã
nguồn dùng trong lần chạy nằm trong `source/`. Dữ liệu các phần có seed rời nhau.

Tuning chỉ chạy trên tập 7301. Cấu hình thắng theo trung bình F trong từng instance
rồi trung bình các instance; hòa thì chọn tên preset theo thứ tự chữ. Đây là tiêu
chí lựa chọn trên các điểm đã chuẩn hóa, không coi F là một chi phí kho tuyệt đối.
Kết quả chọn được khóa trong `selection.lock.json` trước khi giải holdout.

Nếu mã nguồn hoặc dữ liệu không khớp hash, lệnh theo giai đoạn từ chối chạy.
Không ghi đè thư mục nghiên cứu có sẵn. Nếu phát hiện lỗi triển khai sau khi xem
holdout, phải ghi rõ lỗi, giữ kết quả cũ và dùng tập test mới để xác nhận bản sửa;
không gọi tập đã xem là holdout mới. Checksum là kiểm tra toàn vẹn local, không
phải chứng thực thời gian từ bên thứ ba.

## Cách chạy

Trong thư mục `warehouse_joint_optimizer`, với Python đã cài dependencies:

```powershell
python scripts/run_research.py all --output results/research_run_moi
```

`all` thực hiện prepare → tune → holdout → ablation → sensitivity → exact →
report → verify → package. Chạy tuần tự, không chạy test hay benchmark khác cùng
lúc nếu muốn dùng số đo thời gian. Thời lượng phụ thuộc máy, thường nhiều phút.

Cũng có thể chạy từng stage theo thứ tự trên với cùng `--output`. Không chạy lại
stage tạo nghiệm vào thư mục đã tồn tại. Khi một stage bị ngắt, giữ nguyên bằng
chứng đã có; không tự gộp các lần chạy khác cấu hình vào một báo cáo.

```powershell
python scripts/run_research.py verify --output results/research_20260919
python scripts/check_results.py results/research_20260919/holdout
```

Nghiệm từng run, dữ liệu, manifest, bảng CSV, summary, bản sao code và checksum
được nén trong `results/<ten_nghien_cuu>.zip`. Các file raw/archive lưu local;
báo cáo gọn, protocol và script có thể đưa lên Git. Kết quả theo thời gian có thể
khác giữa các lần chạy dù cùng seed; cần `seconds=0` và số vòng cố định nếu muốn
kiểm tra tái lập thuật toán theo số vòng.

## Diễn giải ablation

| Biến thể | Thay đổi so với ALNS đầy đủ | Giới hạn kết luận |
|---|---|---|
| uniform | Tắt cập nhật thích nghi; tương đương LNS | Cùng seed không bảo đảm cùng chuỗi move sau khi trọng số thay đổi |
| without_random/related/late/batch | Bỏ đúng một destroy operator | Ngân sách cố định nên số vòng hoàn thành có thể đổi |
| greedy_only/regret_only | Bỏ một repair operator | Đo hiệu quả cả chất lượng move và tốc độ của pool còn lại |
| no_schedule_local | Bỏ lượt local search lịch, không thay bằng lượt order move bổ sung | Repair vẫn được đổi lịch; không phải đóng băng assignment |
| no_2opt_compound | Dùng NN trong cả khởi tạo và search | Là ablation kết hợp, không thể quy hết cho một bước 2-Opt |
| Fixed-plan routing | Giữ nguyên batch/picker/thứ tự B2, thay NN/2-Opt/S-Shape/exact | Chỉ đo decoder và tác động thời gian do tuyến; không search lại batching/lịch |

## Đọc bằng chứng

- Mọi nghiệm phải qua validator độc lập; manifest liên kết đúng fingerprint instance.
- `zero_iteration_runs` phải được công bố. Giữ những ca đó trong bảng tổng để
  tránh loại mẫu bất lợi, nhưng không dùng chúng để chứng minh lợi ích search.
- `adapted_iterations > 0` nghĩa là có vòng hoàn thành sau cập nhật trọng số;
  chỉ có `operator_weights` khác 1 sau khi kết thúc chưa đủ chứng minh đã thích nghi.
- Summary có mean, std, median, best, tỷ lệ đúng hạn; bảng chính báo cáo từng
  instance. So sánh thắng/hòa/thua cho mỗi instance một phiếu sau trung bình seed.
- Chỉ tính gap khi oracle `certified_optimal=true` và dùng cùng trọng số/chuẩn B0.
- Kết quả hiện tại là thống kê mô tả. Chưa có khẳng định ý nghĩa thống kê hay
  khả năng áp dụng cho mọi kho. Các ca thua và F tốt hơn nhưng nhiều đơn trễ hơn
  phải được đưa vào phần kết luận.
