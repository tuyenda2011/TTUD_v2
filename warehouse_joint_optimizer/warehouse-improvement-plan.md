# Kế hoạch cải tiến Warehouse Joint Optimizer

> Lưu trữ kế hoạch ban đầu; checkbox bên dưới không phản ánh trạng thái hiện tại.
> VNS và giao diện mới đã được triển khai. Xem `demo-upgrade-plan.md`,
> `docs/EVIDENCE_UPGRADE.md` và `DANH_GIA_TONG_QUAN_DU_AN.md` để theo dõi hiện trạng.

Mục tiêu: demo warehouse ổn định, cải thiện hiệu năng có đo lường và bổ sung VNS làm đối chứng cho ALNS. Giữ mô hình hiện tại: một depot, picker đồng nhất, đơn sẵn sàng ở t=0, capacity và deadline mềm. Đây là kế hoạch, chưa triển khai thuật toán mới.

## Thuật toán bổ sung: VNS

Variable Neighborhood Search dùng shaking, local search và đổi neighborhood có hệ thống. Áp dụng cho cùng Plan, NN/2-Opt, objective và validator của project. Neighborhood gồm chuyển đơn, hoán đổi đơn, tách/gộp batch khả thi, chuyển batch giữa picker và đổi thứ tự batch. Tăng mức shaking khi không cải thiện; quay về mức đầu khi cải thiện. Giữ best khả thi và trả về khi hết ngân sách. Nguồn: https://www.gerad.ca/en/papers/G-96-49

## Công việc theo thứ tự

- [ ] 1. Chốt bộ đo trước thay đổi: lưu config, fingerprint dữ liệu và phiên bản code; đo tuần tự thời gian khởi tạo, repair, evaluator, routing, số vòng và RAM trên 20/50/100/200 đơn. Kiểm chứng: có kết quả gốc để so trước/sau; không dùng thời gian benchmark cũ chạy đồng thời làm chuẩn.
- [ ] 2. Chuẩn hóa khởi tạo và timing trong solver.py: LNS/ALNS/VNS dùng cùng nghiệm đầu, route decoder, weights và chuẩn B0; công bố chi phí khởi tạo, tiền xử lý và validation. Nếu chọn nghiệm tốt nhất giữa FCFS/Greedy thì áp dụng cho cả ba. Kiểm chứng: cùng initial objective và không trả nghiệm xấu hơn initial.
- [ ] 3. Tối ưu evaluator.py/routing.py theo profile: tái sử dụng thông tin batch, chỉ tính lại hậu tố lịch của picker bị ảnh hưởng; giới hạn cache có cấu hình. Giữ full evaluator và validator làm đối chiếu. Kiểm chứng: delta/full khớp trên chuỗi move ngẫu nhiên, capacity và coverage đúng; báo runtime/RAM trước-sau.
- [ ] 4. Cải tiến search.py: thử shortlist theo vị trí/due date có phần khám phá ngẫu nhiên, giữ khả năng mở batch mới; đo chi phí và lợi ích từng operator. Tuning removal, segment, reaction và cooling trên tập riêng; lưu ALNS cũ làm đối chứng. Kiểm chứng: ablation từng thay đổi; chỉ giữ cải tiến có bằng chứng, không yêu cầu ALNS luôn thắng.
- [ ] 5. Thêm warehouse_opt/vns.py và tích hợp solver/CLI/benchmark: shaking theo mức, local search có giới hạn và neighborhood change; hỗ trợ seed, deadline, trace, bộ đếm đánh giá và best khả thi. Kiểm chứng: tiny exact, seed cố định, timeout giữa thao tác, tách/gộp batch và mọi nghiệm qua validator.
- [ ] 6. Benchmark B0/B2/B3/LNS/ALNS/VNS: synthetic 4 kích thước × 5 instance × 10 seed cho search; Kris lấy mẫu phân tầng 6/12/18 đơn với danh sách chốt trước. Thử ngân sách 1/3/5 giây; chạy tuần tự, cùng máy và cùng giới hạn. Tách tuning/test; B0/B2 xác định chỉ cần một nghiệm mỗi instance. Báo F, distance, makespan, tardiness, late orders, runtime/RAM, mean/std/best và thắng/hòa/thua theo instance; dùng gap chỉ khi exact được chứng nhận. Kiểm chứng: manifest đủ run, fingerprint và validator khớp; không coi seed là instance độc lập.
- [ ] 7. Hoàn thiện demo/app.py: preset nhỏ dễ giải thích, chọn B0/B3/LNS/ALNS/VNS, bảng trước/sau, tuyến theo batch, Gantt, trace chung trục thời gian; hiện rõ deadline mềm và số đơn trễ. Chạy live và xem kết quả lưu sẵn có nhãn riêng; kết quả gắn snapshot cấu hình. Kiểm chứng: đổi cấu hình không trộn kết quả, upload sai báo rõ, export kiểm tra lại được.
- [ ] 8. Kiểm chứng và bàn giao: chạy test core/CLI/AppTest và thao tác trình duyệt thật; diễn tập mở ứng dụng → chọn preset → so sánh → xem route/Gantt → tải JSON. Cập nhật README và báo cáo kết quả. Kiểm chứng: tất cả nghiệm demo hợp lệ, có hướng dẫn chạy offline và giới hạn rõ; đo độ trễ thực tế trước khi cam kết thời gian demo.

## Điều kiện hoàn thành

Demo hoạt động đầu-cuối; VNS giải cùng bài toán và được so sánh công bằng; tối ưu hiệu năng không đổi kết quả đánh giá; mọi kết luận chất lượng có raw results và config tái lập. Chưa đưa congestion, nhiều depot hoặc deadline cứng vào đợt này.
