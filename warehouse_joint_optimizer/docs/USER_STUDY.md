# Phiếu thử demo với ba người dùng thật

Trạng thái: **chưa thực hiện**. Không có dữ liệu người tham gia tại thời điểm lập
phiếu. Người thực hiện dự án cần mời ba người chưa dùng ứng dụng; dùng mã U1/U2/U3,
không cần ghi tên hoặc thông tin cá nhân.

## Chuẩn bị chung

Mở ứng dụng tại cùng địa chỉ local trên cùng máy. Chọn dữ liệu tổng hợp 10 đơn,
3 picker, capacity 20, seed 42, ngân sách 3 giây; dùng B0 và ALNS. Chuẩn bị đồng hồ
và ghi lại phiên bản code/cấu hình. Mỗi người bắt đầu từ cùng màn hình đầu vào.
Nếu dùng môi trường khác, ghi rõ cấu hình; không trộn thời gian với nhau mà không
giải thích. Không gọi thời gian sử dụng app là runtime thuật toán.

## Nhiệm vụ và cách chấm

| Bước | Đọc yêu cầu cho người tham gia | Điều kiện hoàn thành |
|---|---|---|
| 1 | Chạy tối ưu bộ dữ liệu được chuẩn bị | Có kết quả mới, nhận biết thuật toán đang xem |
| 2 | Tìm số đơn trễ của ALNS và so với B0 | Đọc đúng hai giá trị; phân biệt số đơn trễ với tổng phút trễ |
| 3 | Xem tuyến một chuyến và nhân viên thực hiện | Chọn đúng chuyến, chỉ ra depot và picker |
| 4 | Tìm thời điểm bắt đầu/kết thúc chuyến trên lịch | Đọc đúng thời gian tương ứng với chuyến ở bước 3 |
| 5 | Tải kết quả JSON | Tải đúng nghiệm đang xem và tìm được file |
| 6 | Giải thích F thấp hơn có chắc ít đơn trễ hơn không | Hiểu rằng mục tiêu cho phép đánh đổi; ghi câu trả lời nguyên văn |

Bấm giờ từng bước. Nếu người dùng hỏi, ghi câu hỏi và nội dung trợ giúp trước khi
giải thích. Nếu sau 2 phút chưa hoàn thành một bước, đánh dấu “cần trợ giúp” rồi
cho tiếp tục; không sửa thời gian thành một lần làm thành công không hỗ trợ.

## Phiếu ghi nhận

| Người | B1 (s) | B2 (s) | B3 (s) | B4 (s) | B5 (s) | B6 đúng? | Số lần trợ giúp | Kết quả |
|---|---:|---:|---:|---:|---:|---|---:|---|
| U1 | Chưa đo | | | | | | | Chưa thực hiện |
| U2 | Chưa đo | | | | | | | Chưa thực hiện |
| U3 | Chưa đo | | | | | | | Chưa thực hiện |

| Người/bước | Quan sát hoặc câu hỏi nguyên văn | Trợ giúp đã cung cấp | Vấn đề hiểu/điều khiển | Sửa đề xuất |
|---|---|---|---|---|
| Chưa có | | | | |

Ghi ngày thử, cấu hình và phiên bản code tại đây: **chưa có**.

## Sau thử

Tổng hợp số người hoàn thành mỗi bước, median thời gian và số lần cần trợ giúp;
không suy rộng tỷ lệ của ba người thành tỷ lệ toàn bộ người dùng. Ưu tiên sửa lỗi
khiến người dùng đọc sai đơn trễ/F hoặc tải nhầm nghiệm. Nếu sửa UI, kiểm tra lại
đúng bước đã lỗi và ghi đây là lần thử sau sửa. Chỉ đánh dấu P2.1 hoàn thành khi
có dữ liệu quan sát thực của cả ba người.
