# Mô hình và diễn tập bảo vệ

## Phát biểu đóng góp thống nhất

“Đề tài đề xuất cách áp dụng ALNS tích hợp với bộ giải mã tuyến heuristic cho
bài toán kết hợp gom đơn, phân công, định tuyến và lập lịch nhiều nhân viên có
xét hạn hoàn thành.” ALNS là khung có sẵn; đóng góp cần bảo vệ là cách thiết kế
và kết quả đánh giá trong phạm vi mô hình này.

Khi trình bày ưu thế, dùng [báo cáo nghiên cứu 19/09](../results/research_20260919/REPORT.md)
và nêu rõ đối chứng, số instance, số seed, ngân sách và ca thua. Điểm F thấp hơn
không bảo đảm ít đơn trễ hơn. Kiểm tra `iterations_completed` và
`adapted_iterations` trước khi quy cải thiện cho search hoặc tính thích nghi.

## Biểu diễn quyết định trong code

`Plan` là danh sách nhân viên → thứ tự chuyến → các mã đơn trong chuyến.
Vị trí SKU được ánh xạ lên đồ thị hai chiều. Dijkstra tính khoảng cách qua lối đi;
NN chọn thứ tự ghé, 2-Opt cải thiện thứ tự đó. Tuyến không phải biến độc lập
được search tự do: được giải mã lại từ thành phần chuyến.

Mỗi đơn xuất hiện đúng một lần. Mọi chuyến không rỗng, tổng size × quantity
không vượt capacity. Số chuỗi lịch bằng số nhân viên; nhân viên rảnh được phép
có chuỗi rỗng. Mỗi chuyến bắt đầu sau khi chuyến trước của cùng nhân viên kết thúc.
Hạn giao là hạn mềm; trễ không làm nghiệm mất tính khả thi.

Thời lượng chuyến = batch_minutes + distance / speed
+ location_minutes × số vị trí lấy khác nhau + tổng pick_minutes × quantity.
Mọi đơn cùng chuyến hoàn thành tại thời điểm chuyến quay về và bàn giao xong.
Không có thời gian chờ chủ động hoặc đơn đến động trong mô hình.

## Ví dụ tính tay

Một nhân viên có hai chuyến, mỗi chuyến một đơn. Quãng đường lần lượt 10 và 6;
speed = 2, batch_minutes = 1, location_minutes = 0, tổng thời gian lấy hàng
mỗi chuyến = 2. Thời lượng là 8 và 6; hoàn thành ở 8 và 14.
Due dates tương ứng 7 và 12: tổng trễ = 1 + 2 = 3, số đơn trễ = 2,
distance = 16, makespan = 14.

Nếu đây là B0, Dref = 16, Cref = 14, Tref = 2 × 14 = 28.
Với ba trọng số bằng nhau, F = (16/16 + 14/14 + 3/28)/3 = 0,702381.
Đổi thứ tự chuyến: hoàn thành ở 6 và 14, tổng trễ = 0 + 7 = 7.
Distance và makespan không đổi nhưng F tăng lên 0,75.
Ví dụ cho thấy chỉ kiểm tra tổng quãng đường sẽ bỏ sót tác động của lịch.

## Đối chứng và ablation

- B0: gom theo FCFS, tuyến NN; list scheduling dùng thứ tự EDD của chuyến.
- B2: gom greedy, tuyến 2-Opt; B3 thêm cải tiến lịch cục bộ.
- LNS và ALNS dùng destroy/repair; ALNS thích nghi trọng số operator.
- VNS đổi neighborhood, shaking và descent có giới hạn lấy mẫu.
- ALNS_NO_SCHEDULE tắt cải tiến lịch cục bộ, nhưng repair vẫn có thể đổi
  phân công/thứ tự chuyến. Không gọi đây là loại bỏ toàn bộ quyết định lịch.
- ALNS_NO_2OPT dùng NN, ảnh hưởng cả khởi tạo lẫn đánh giá trong search.
  Chênh lệch không phải riêng chi phí một lần gọi 2-Opt.

## Kịch bản trình bày 7 phút

1. Một phút: bài toán, ba quyết định liên quan, capacity và hạn mềm.
2. Một phút: ví dụ tính tay phía trên; giải thích tại sao F có ba thành phần.
3. Hai phút: chạy demo nhỏ, so B0 với ALNS/VNS, xem tuyến và lịch, chỉ một đơn trễ.
4. Một phút: xuất JSON rồi chạy validator, giải thích kiểm chứng độc lập.
5. Một phút: bảng so sánh theo instance; trình bày cả ca thắng và ca thua.
6. Một phút: đóng góp, giới hạn và phần chưa được kiểm chứng.

Không gọi điểm F giữa hai instance là chi phí tuyệt đối cùng thang đo.
Không coi các seed trên cùng dữ liệu là các bài toán độc lập.
Chỉ báo gap tối ưu khi exact đã duyệt hết và certified_optimal=true.

## Phiếu thử người dùng thật — chưa thực hiện

Kịch bản thao tác, tiêu chí đạt và phiếu chi tiết: [USER_STUDY.md](USER_STUDY.md).

Mời ba người chưa xem app: mở demo, chạy mẫu, tìm đơn trễ, tìm tuyến một chuyến,
tải JSON. Ghi thời gian từng bước, số lần cần trợ giúp và lỗi hiểu nhầm.
Không tự điền kết quả hoặc lấy browser automation thay cho người dùng thật.

| Người | Tổng thời gian | Bước cần trợ giúp | Lỗi hiểu nhầm | Sửa đề xuất |
|---|---|---|---|---|
| 1 | Chưa đo | | | |
| 2 | Chưa đo | | | |
| 3 | Chưa đo | | | |
