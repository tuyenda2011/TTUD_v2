# Kiểm tra tích hợp trên dữ liệu tác giả Kris

Đơn, SKU, kho, due dates, capacity, số picker và thời gian lấy từ file tác giả; không sinh đơn hoặc hạn mới. Khoảng cách và thời gian giữ nguyên đơn vị nguồn.

Bộ giải vẫn dùng hàm mục tiêu hạn mềm chuẩn hóa của project. Đây không phải kết quả tái lập JOBPRSP-D hạn cứng, không đối chiếu với best-known của tác giả.

| Instance | Orders | Method | F | Distance (source units) | Makespan (source units) | Tardiness (source units) | Late orders |
|---|---:|---|---:|---:|---:|---:|---:|
| Kris-instances_106_1 | 6 | B0 | 0.666667 | 18936.0 | 49614.0 | 0.0 | 0 |
| Kris-instances_106_1 | 6 | B1 | 0.712306 | 19220.0 | 52854.0 | 16854.0 | 1 |
| Kris-instances_106_1 | 6 | B2 | 0.679285 | 18362.0 | 50568.0 | 14568.0 | 1 |
| Kris-instances_106_1 | 6 | B3 | 0.679285 | 18362.0 | 50568.0 | 14568.0 | 1 |
| Kris-instances_106_1 | 6 | LNS | 0.611135 | 17792.0 | 44346.0 | 0.0 | 0 |
| Kris-instances_106_1 | 6 | ALNS | 0.611135 | 17792.0 | 44346.0 | 0.0 | 0 |
| Kris-instances_103_1 | 12 | B0 | 0.666667 | 26404.0 | 62268.0 | 0.0 | 0 |
| Kris-instances_103_1 | 12 | B1 | 0.613576 | 24608.0 | 56586.0 | 0.0 | 0 |
| Kris-instances_103_1 | 12 | B2 | 0.592866 | 23456.0 | 55434.0 | 0.0 | 0 |
| Kris-instances_103_1 | 12 | B3 | 0.590361 | 23456.0 | 54966.0 | 0.0 | 0 |
| Kris-instances_103_1 | 12 | LNS | 0.546286 | 22224.0 | 49638.0 | 0.0 | 0 |
| Kris-instances_103_1 | 12 | ALNS | 0.545002 | 21990.0 | 49950.0 | 0.0 | 0 |
| Kris-instances_100_1 | 18 | B0 | 0.666667 | 24134.0 | 53478.0 | 0.0 | 0 |
| Kris-instances_100_1 | 18 | B1 | 0.624511 | 19552.0 | 56868.0 | 0.0 | 0 |
| Kris-instances_100_1 | 18 | B2 | 0.615863 | 19286.0 | 56070.0 | 0.0 | 0 |
| Kris-instances_100_1 | 18 | B3 | 0.603312 | 19286.0 | 53106.0 | 17106.0 | 1 |
| Kris-instances_100_1 | 18 | LNS | 0.560016 | 17406.0 | 51276.0 | 0.0 | 0 |
| Kris-instances_100_1 | 18 | ALNS | 0.564461 | 17782.0 | 51156.0 | 0.0 | 0 |

18 nghiệm đã qua validator độc lập. Seed 42, tối đa 100 vòng / 1 giây, một instance mỗi kích thước. Chỉ là kiểm tra tích hợp, chưa phải nghiên cứu thống kê.
