# Kế hoạch cải thiện và đánh giá bài toán

## Mục tiêu

Hoàn thiện đồ án **Multi-Picker Joint Order Batching, Routing and Scheduling with Due Dates**, làm rõ đóng góp của thiết kế ALNS cho bài toán tích hợp và tạo đủ bằng chứng để bảo vệ kết quả mà không phóng đại kết luận.

## Triển khai ngày 19/09/2026

- Đã bổ sung telemetry khởi tạo/search, số vòng hoàn thành, trạng thái dừng và số
  vòng thực sự dùng trọng số thích nghi; giữ ngân sách chung gồm khởi tạo + search.
- Đã bổ sung cấu hình pool destroy/repair để ablation từng operator. Biến thể bỏ
  local search lịch không tự chuyển lượt đó thành lượt order move bổ sung.
- Đã có script chạy tuần tự, khóa dữ liệu và cấu hình, tuning/holdout riêng,
  sensitivity, exact gap và so decoder trên cùng plan.
- Kiểm thử sau thay đổi: **112 passed**; Ruff đạt trên các file Python thay đổi.
- Đợt nghiên cứu đang chạy; chưa đánh dấu tiêu chí thực nghiệm hoàn thành trước
  khi có báo cáo và kiểm tra lại toàn bộ nghiệm.
- P2.1 cần ba người tham gia thật; đã chuẩn bị [phiếu thao tác và ghi nhận](warehouse_joint_optimizer/docs/USER_STUDY.md), chưa có số liệu người dùng.

Quy trình: [RESEARCH_PROTOCOL.md](warehouse_joint_optimizer/docs/RESEARCH_PROTOCOL.md).
Kết quả đợt đo: [REPORT.md](warehouse_joint_optimizer/results/research_20260919/REPORT.md).

## Đánh giá hiện trạng

### Điểm mạnh đã có

- Mô hình hóa đúng mối liên hệ giữa gom đơn, định tuyến, phân công picker, thứ tự batch và hạn hoàn thành.
- Ràng buộc được mô tả rõ: mỗi đơn xuất hiện đúng một lần, không vượt sức chứa, batch không rỗng, lịch của cùng picker không chồng lấn.
- Thời gian batch có đủ quãng đường, tốc độ, thao tác tại vị trí và thời gian lấy theo số lượng.
- Tuyến được tính trên đồ thị lối đi bằng shortest path; validator độc lập tính lại physical walk và thời gian.
- Có đối chứng nhiều mức: B0, B2, B3, LNS, ALNS, VNS; có thêm ablation cho 2-Opt và schedule.
- Có oracle vét cạn cho bài nhỏ và đã kiểm thử toàn bộ hiện tại: **106 test đạt**.
- Tài liệu đã nêu giới hạn, phân biệt hạn mềm với hạn giao hàng thực tế và không gọi benchmark Kris là tái lập bài toán hạn cứng.

### Điểm yếu cụ thể cần cải thiện

| Mức | Điểm yếu | Bằng chứng hiện tại | Hướng xử lý |
|---|---|---|---|
| P0 | Một số lần chạy ALNS không thực hiện được vòng search | Cả 9 run ALNS 100 đơn trong `results/evidence_test/raw` có `iterations_completed = 0`; ngân sách hết trong khởi tạo hoặc trước khi vòng đầu hoàn tất | Giữ ngân sách khởi tạo + search công bằng, tăng ngân sách đánh giá; báo cáo số vòng, số vòng dùng trọng số thích nghi và trạng thái dừng |
| P0 | Chưa chứng minh ALNS hơn phương pháp đơn giản hơn | ALNS so B3 chỉ thắng 4/9, hòa 2/9, thua 3/9; `ALNS_NO_SCHEDULE` còn nhỉnh hơn ALNS trong bộ 0,5 giây | Đối chứng ALNS/B3/LNS/VNS với cùng ngân sách, nhiều seed và báo cáo thắng-hòa-thua cùng độ lệch |
| P0 | Chưa có tuning/test độc lập | `docs/EVIDENCE_UPGRADE.md` ghi rõ chưa tuning, chưa sensitivity và chưa holdout | Chia tập tuning và test; khóa trọng số/cấu hình trước khi chạy test |
| P1 | Hàm F có thể che khuất số đơn trễ | F giảm không luôn làm số đơn trễ giảm; mục tiêu hiện tại dùng ba trọng số bằng nhau | Thêm sensitivity theo trọng số; báo cáo Pareto và chọn rõ ưu tiên nghiệp vụ |
| P1 | Đóng góp routing cần diễn đạt chính xác | Tuyến được decode bằng NN + 2-Opt, không phải biến tuyến được search tự do | Ghi rõ “ALNS tích hợp với bộ giải mã tuyến heuristic”; thêm so sánh NN/S-Shape/2-Opt khi layout phù hợp |
| P1 | Exact gap còn quá hẹp | Exact chỉ giới hạn bài nhỏ và chưa có gap cho tập benchmark chính | Tạo tập nhỏ theo nhiều cấu hình; báo cáo `certified_optimal`, gap và số trạng thái |
| P2 | Khả năng tổng quát ngoài mô hình tĩnh còn hạn chế | Chưa có release time, congestion, picker không đồng nhất, nhiều depot hoặc split order | Giữ trong phạm vi luận văn hiện tại; nêu rõ đây là hướng mở rộng, không thêm vào khi chưa có dữ liệu |
| P2 | Chưa có thử người dùng thực | Phiếu thử trong `MODEL_AND_DEFENSE.md` vẫn để “chưa thực hiện” | Cho 3 người dùng chạy demo theo kịch bản cố định, ghi thời gian, lỗi hiểu và số lần trợ giúp |

## Kế hoạch thực hiện

### P0 — Bảo đảm thực nghiệm trả lời đúng câu hỏi nghiên cứu

- [ ] **P0.1 — Sửa đo ngân sách ALNS.** Ghi riêng `initialization_seconds`, `optimization_seconds`, `iterations_completed`, `stop_reason`; chạy lại bộ 10/30/100 đơn với ngân sách đủ để 100 đơn có ít nhất một số vòng search.  
  **Xác nhận:** không dùng kết quả có `iterations_completed = 0` để kết luận ALNS; mọi dòng benchmark có thời gian và trạng thái dừng.

- [x] **P0.2 — Khóa cấu hình trước khi test.** Chọn tập tuning riêng để chọn `temperature`, `cooling`, `candidate_limit`, `removal_fraction`; chốt trước ngân sách và trọng số mục tiêu, lưu config và checksum trước khi chạy test. Trọng số là ưu tiên nghiệp vụ, không chọn bằng cách so F giữa các trọng số khác nhau.  
  **Xác nhận:** báo cáo test không thay đổi tham số sau khi xem kết quả.

- [ ] **P0.3 — Chạy đối chứng công bằng.** So sánh B0, B2, B3, LNS, ALNS, VNS trên cùng instance, cùng search seed, cùng giới hạn thời gian thực và ít nhất 10 seed; giữ một bộ test chưa xem.  
  **Xác nhận:** xuất bảng F, distance, makespan, tardiness, late orders, runtime; có mean, std, median và thắng-hòa-thua.

- [ ] **P0.4 — Kiểm tra đóng góp ALNS.** Chạy ablation theo từng thành phần: adaptive weights, destroy/repair, schedule neighborhood, 2-Opt; không gộp nhiều thay đổi vào một ablation.  
  **Xác nhận:** mỗi ablation có mô tả chính xác thành phần bị tắt và tránh gọi `ALNS_NO_SCHEDULE` là đóng băng hoàn toàn lịch.

### P1 — Củng cố mô hình và kết luận

- [ ] **P1.1 — Phân tích mục tiêu.** Chạy sensitivity với các bộ trọng số ưu tiên distance, makespan và tardiness; bổ sung số đơn trễ và tỷ lệ đúng hạn vào bảng chính.  
  **Xác nhận:** kết luận nêu rõ trường hợp F tốt hơn nhưng late orders xấu hơn.

- [ ] **P1.2 — Đo chất lượng tuyến.** Trên bài nhỏ, so NN, NN+2-Opt và tuyến exact; trên layout aisle phù hợp, so thêm S-Shape.  
  **Xác nhận:** tách được tác động của batching/scheduling khỏi tác động của route decoder.

- [ ] **P1.3 — Mở rộng exact benchmark nhỏ.** Sinh các instance 4–6 đơn với nhiều số picker, capacity và due-date tightness; chạy `solve_exact` đến khi `certified_optimal=true`.  
  **Xác nhận:** báo cáo gap của từng heuristic so với exact và không ghi “tối ưu” nếu chưa certified.

### P2 — Hoàn thiện khả năng trình bày và phạm vi

- [ ] **P2.1 — Kiểm thử giao diện có người dùng.** Thực hiện kịch bản mở demo, chạy ALNS/B0, tìm đơn trễ, xem tuyến và tải JSON với 3 người chưa xem app.  
  **Xác nhận:** điền đầy đủ bảng thời gian, lỗi hiểu nhầm và đề xuất sửa trong `docs/MODEL_AND_DEFENSE.md`.

- [x] **P2.2 — Chốt thông điệp bảo vệ.** Dùng phát biểu: “Đề tài đề xuất cách áp dụng ALNS tích hợp với bộ giải mã tuyến heuristic cho bài toán này”; không tuyên bố phát minh ALNS hoặc tối ưu toàn cục.  
  **Xác nhận:** README, báo cáo tự sinh và kịch bản bảo vệ dùng cùng một cách gọi. Chưa có file slide độc lập trong phạm vi lần triển khai này.

## Tiêu chí hoàn thành

- [ ] Bộ test mới đạt toàn bộ test hiện có và validator độc lập xác nhận mọi nghiệm benchmark.
- [ ] Không còn kết quả ALNS được dùng để kết luận khi `iterations_completed = 0`.
- [ ] Có một test set khóa trước, báo cáo rõ seed, cấu hình, ngân sách và checksum dữ liệu.
- [ ] Có bảng so sánh ALNS với B3/LNS/VNS và ít nhất một phân tích ablation đáng tin cậy.
- [ ] Có sensitivity trọng số, exact gap trên bài nhỏ và nêu rõ các giới hạn mô hình.
- [ ] Kết luận phân biệt được: cải thiện so B0, ưu thế so heuristic mạnh, và đóng góp thiết kế của đề tài.

## Lệnh kiểm tra cuối

```powershell
cd D:\TTUD_v2\warehouse_joint_optimizer
& 'D:/Miniconda/envs/TTUD/python.exe' -m pytest -q -p no:cacheprovider
& 'D:/Miniconda/envs/TTUD/python.exe' scripts/run_research.py verify --output results/research_20260919
& 'D:/Miniconda/envs/TTUD/python.exe' scripts/check_results.py results/research_20260919/holdout
& 'D:/Miniconda/envs/TTUD/python.exe' scripts/check_clean_checkout.py
```

Nếu dùng môi trường khác, thay đường dẫn Python nhưng giữ nguyên ba bước: test, validator benchmark và kiểm tra checkout sạch.
