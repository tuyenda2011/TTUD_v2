# Bổ sung bằng chứng thực nghiệm — 17/09/2026

> Ghi chú rà soát 19/09: cả 9 run ALNS 100 đơn của đợt này có
> `iterations_completed=0`. Kết quả ở nhóm đó phản ánh khởi tạo, không chứng minh
> lợi ích search hoặc thích nghi. Không loại các run này khỏi báo cáo lịch sử.
> Quy trình đánh giá tiếp theo có khóa tuning/holdout và telemetry đầy đủ tại
> [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md).

## Phạm vi và quy trình

Cấu hình cố định trong `configs/evidence_test.json`: 9 instance tổng hợp,
10/30/100 đơn × seed dữ liệu 901/902/903; search seed 7/42/101.
B0/B2 chạy một lần, B3/LNS/ALNS/VNS và hai ablation mỗi phương pháp ba lần:
tổng 180 nghiệm. Ngân sách 0,5 giây gồm khởi tạo, tối đa 2.000 vòng.
Mọi phương pháp dùng cùng trọng số và chuẩn B0 trên mỗi instance.

Đây là tập đánh giá bổ sung với cấu hình cố định, không phải một quy trình
tuning/test hoàn chỉnh. Chưa chọn tham số qua tuning độc lập, chưa đo độ nhạy
trọng số, chưa mở rộng benchmark tác giả hoặc chứng nhận exact cho tập này.
Không chỉnh cấu hình dựa trên kết quả rồi gọi lần chạy sau là holdout chưa xem.

Seed được tổng hợp trong từng instance trước. Bảng thắng/hòa/thua so với
B0/B2/B3 cho mỗi instance đúng một phiếu; phần trăm cải thiện tính theo từng
cặp rồi mới lấy trung bình. F tuyệt đối không được gộp giữa các instance để
suy ra một mức chi phí kho chung. Đây là thống kê mô tả, không phải kiểm định.

## Tái lập và đóng gói

Kiểm chứng bằng Conda TTUD: **106 test đạt** trên thư mục làm việc;
bản sao theo danh sách file Git đạt **96 test, 10 test bỏ qua** vì không kèm
benchmark tác giả tùy chọn. Ruff đạt trên module so sánh, script đóng gói và
test mới. Test mới bao gồm số seed không đều giữa instance, tham chiếu bằng
0, từ chối nghiệm không khả thi và từ chối archive khi số liệu bị sửa sai.

Chạy từ thư mục dự án, trong Anaconda Prompt:

```powershell
conda activate TTUD
python -m warehouse_opt benchmark --config configs/evidence_test.json --output results/evidence_test
python scripts/package_evidence.py results/evidence_test results/submission/evidence_test.zip
python scripts/check_clean_checkout.py
```

Archive chứa instance, nghiệm từng run, manifest mã nguồn, CSV và báo cáo.
Script kiểm tra fingerprint và validator trước khi nén, tạo SHA-256 bên cạnh.
Archive được giữ local theo `.gitignore`; bản này chỉ dùng synthetic nên không
kèm dữ liệu benchmark tác giả. Checksum kiểm tra tính toàn vẹn, không chứng minh
kết quả là tối ưu. Lưu archive này cùng bản code tương ứng khi nộp.

Báo cáo: [REPORT](../results/evidence_test/REPORT.md),
[summary](../results/evidence_test/summary.json),
[so sánh từng cặp](../results/evidence_test/comparison.json).

## Giới hạn diễn giải

### Kết quả thực chạy

180/180 nghiệm đã được validator kiểm tra lại trước khi đóng gói.

| So sánh | Thắng | Hòa | Thua | Cải thiện F trung bình theo instance |
|---|---:|---:|---:|---:|
| ALNS so B2 | 6 | 3 | 0 | 6,584% |
| ALNS so B3 | 4 | 2 | 3 | 5,842% |
| VNS so B2 | 8 | 1 | 0 | 7,396% |
| VNS so B3 | 7 | 1 | 1 | 6,669% |

ALNS hòa B2 trên cả ba instance 100 đơn ở ngân sách này. Tăng thời gian là
giả thuyết cần đo tiếp, không phải kết quả đã chứng minh. ALNS_NO_SCHEDULE
có cải thiện trung bình so B2 là 6,636%, hơi cao hơn ALNS đầy đủ 6,584%:
chưa có bằng chứng thành phần cải tiến lịch cục bộ luôn có lợi với nửa giây.
ALNS_NO_2OPT thua B2 ở 4/9 instance; việc bỏ 2-Opt không chỉ đổi tốc độ
mà còn đổi khởi tạo/tuyến, nên chưa thể quy nguyên nhân cho một yếu tố đơn lẻ.

SHA-256 archive đợt đo:
`df51d3158702fda38dfdfb79728b7c87f1455d31c64f285d78d56fc2a9013973`.

Ngân sách nửa giây phản ánh demo ngắn; không đủ để kết luận chất lượng khi chạy
lâu hơn. Khởi tạo, số vòng và thao tác không thể ngắt giữa chừng làm thời gian
thực tế khác nhau. Chạy tuần tự trên máy phát triển, không cô lập hệ điều hành.
Các lần test được kết thúc trước lượt benchmark cuối; lượt chạy thử đồng thời
với pytest đã được thay bằng lượt chạy riêng, không dùng số liệu cũ để kết luận.

ALNS_NO_SCHEDULE vẫn có thể đổi lịch qua repair. ALNS_NO_2OPT ảnh hưởng cả
khởi tạo và giải mã tuyến. Không quy mọi chênh lệch cho riêng một thao tác.

Thử người dùng thật, sensitivity, tuning độc lập và exact gap vẫn là công việc
tiếp theo; phiếu và kịch bản bảo vệ trong [MODEL_AND_DEFENSE](MODEL_AND_DEFENSE.md).
