# Kế hoạch nâng cấp demo Warehouse Joint Optimizer

Ngày lập: 16/09/2026. Trạng thái: **đã triển khai phần kỹ thuật; còn thử nghiệm với 3 người mới**. Thực hiện trên nhánh `feature/warehouse-demo-upgrade`, chạy bằng Conda `TTUD`. Giữ Streamlit và bộ giải hiện tại trong đợt này.

## Tiến độ thực hiện

- [x] 1. Có ảnh trước/sau desktop/mobile và `DESIGN.md` trước khi viết giao diện.
- [x] 2. Tách `demo/app.py`, `demo/components.py`, `demo/state.py`; baseline trước sửa 87 test đạt, bộ mới 92 test đạt.
- [x] 3. Mặc định 10 đơn, B0 + ALNS; form theo nguồn và Nâng cao đóng mặc định.
- [x] 4. Tách nháp/snapshot, báo kết quả cũ, xóa kết quả khi lỗi, nút mở bản lưu chỉ hiện khi file tồn tại.
- [x] 5. Ba KPI chính, ba tab, bảng tiếng Việt, xuất JSON/snapshot, phân tích thuật toán thu gọn.
- [x] 6. Mặc định một nhân viên/một chuyến, số thứ tự điểm lấy, màu thống nhất tuyến/lịch, trạng thái nhân viên rảnh.
- [x] 7. Đo tuần tự 96 nghiệm hợp lệ trên 6 bộ dữ liệu, ngân sách 1/3 giây và 3 seed tìm kiếm; lưu config, fingerprint, source hash, revision và báo cáo. Không thay thuật toán khi chưa có bằng chứng cần tối ưu.
- [ ] 8. Phần tự động đã qua: pytest/AppTest, Edge desktop/mobile, upload sai/đúng, download rồi validate, bộ lọc và bàn phím; bản sao chỉ gồm file đủ điều kiện đưa lên Git cũng đạt. **Chưa thực hiện khảo sát 3 người mới trong 3 phút.**

Chi tiết, lệnh tái lập và giới hạn: [báo cáo nghiệm thu](docs/DEMO_UPGRADE_VALIDATION.md). Các mục bên dưới giữ tiêu chí ban đầu để đối chiếu.

Lượt rà soát tiếp: đã bổ sung kiểm tra metadata/snapshot, nhãn đơn vị tùy chỉnh và bảng thứ tự điểm lấy; bộ test tăng lên **102 test đạt**. Xem [đánh giá tổng quan và khả năng đạt điểm cao](DANH_GIA_TONG_QUAN_DU_AN.md). Khảo sát người dùng thật vẫn chưa thực hiện.

## Vấn đề cần giải quyết

Rà soát từ `demo/app.py` và các test hiện tại; chưa phải đánh giá bằng ảnh chụp trình duyệt:

- Sidebar hiện upload, thông số tổng hợp và tùy chọn thuật toán cùng lúc, kể cả khi chọn Kris; người dùng khó biết trường nào có tác dụng.
- Năm chỉ số, nhiều caption/thông báo và bốn tab cùng cạnh tranh sự chú ý; F đứng đầu nhưng khó hiểu với người mới.
- Bản đồ mặc định vẽ mọi tuyến; bảng xuất thẳng tên trường tiếng Anh; biểu đồ hội tụ xuất hiện ở hai nơi.
- Đổi cấu hình vẫn còn snapshot cũ, cần phân biệt rõ cấu hình đang sửa và lần chạy đang xem. Nút mở demo đã lưu luôn hiện dù hiện tại thiếu `results/demo_vns/snapshot.json`.
- Kế hoạch cũ còn ghi “thêm VNS/cache” dù `vns.py`, cache giới hạn và test đã tồn tại. Đợt này kiểm chứng chất lượng phần đã có, không tính chúng là tính năng mới.

## Luồng và bố cục đích

`Chọn dữ liệu → xem tóm tắt → Chạy tối ưu → đọc kết quả → xem tuyến/lịch → tải kết quả`.

Sidebar chỉ chứa nguồn dữ liệu, trường phù hợp với nguồn đó, phần **Nâng cao** đóng mặc định và một nút chạy chính. Lần đầu dùng preset tổng hợp 10 đơn, 3 nhân viên, sức chứa 20, seed 42; nguồn được ghi rõ. Kris và JSON vẫn được chọn trực tiếp. Mặc định chạy B0 + ALNS; VNS và so sánh nhiều thuật toán nằm trong Nâng cao.

Nội dung chính: tóm tắt bộ dữ liệu/lần chạy → 3 chỉ số **đơn trễ / thời gian hoàn tất / quãng đường** → **Tổng quan | Tuyến & lịch | Chi tiết**. F, bảng thuật toán và thông tin nghiên cứu đặt trong phần mở rộng; tải JSON ngay cạnh tóm tắt kết quả. Nền trung tính, một màu nhấn, ít khung viền; màu cảnh báo chỉ dùng khi có vấn đề cần xử lý.

## Công việc theo thứ tự

| Ưu tiên | Công việc và file dự kiến | Điều kiện nghiệm thu |
|---|---|---|
| P0 · 1 | Chụp hiện trạng ở 1440×900 và 390×844; tạo `DESIGN.md` với wireframe, màu, chữ, khoảng cách, trạng thái rỗng/đang chạy/lỗi/có kết quả. | Mỗi màn hình có một hành động chính; màn đầu không có tùy chọn không liên quan; thiết kế đủ rõ trước khi sửa UI. |
| P0 · 2 | Tách `demo/app.py` thành điều phối, `demo/components.py` cho hiển thị và `demo/state.py` cho cấu hình/snapshot; giữ lời gọi `solve`/validator. | Test cũ vẫn qua trước khi thay bố cục; không nhân bản logic thuật toán trong UI. |
| P0 · 3 | Làm form theo nguồn, preset khởi đầu và Nâng cao; chỉ upload khi chọn JSON; đưa seed, ngân sách, thuật toán vào Nâng cao. | Mở mới → bấm chạy được ngay; chuyển ba nguồn chỉ hiện trường có tác dụng; cập nhật AppTest theo key/nhãn thay vì chỉ số widget. |
| P0 · 4 | Chuẩn hóa trạng thái trong `demo/state.py`: cấu hình nháp, đang chạy, thành công, lỗi; ghi cấu hình của snapshot, đánh dấu khi nháp khác kết quả; kiểm tra file trước khi hiện nút demo lưu. | Đổi nguồn/seed không gắn nhãn mới lên kết quả cũ; lỗi không hiện kết quả như vừa chạy thành công; thiếu snapshot không có nút hỏng; tiến độ ghi rõ thuật toán đang chạy. |
| P1 · 5 | Dựng trang kết quả theo bố cục đích; Việt hóa bảng và đơn vị; chuyển giải thích dài sang trợ giúp; tập trung một biểu đồ hội tụ trong phần nghiên cứu. | Người dùng thấy số đơn trễ và thời gian hoàn tất trước F; chỉ một thông báo trạng thái tổng hợp; B0=0 không chia cho 0 khi tính %; dữ liệu Kris ghi đơn vị nguồn. |
| P1 · 6 | Sửa `warehouse_opt/plots.py` và bộ lọc: mặc định một nhân viên/một chuyến; tùy chọn xem tất cả; tuyến nổi bật, kho nền nhạt, số thứ tự điểm lấy; lịch ở vùng riêng. | Chuyển nhân viên cập nhật chuyến hợp lệ; xử lý nhân viên không có chuyến; không chồng nhãn ở mẫu 10/30 đơn; màu tuyến khớp chú giải/lịch. |
| P1 · 7 | Đo lại B0/B2/ALNS/VNS trên cấu hình cố định: mẫu 10/30/100 đơn và Kris 6/12/18 đơn, seed search 7/42/101, ngân sách 1/3 giây; đo tuần tự khởi tạo/search/tổng thời gian và F. Chỉ tối ưu nút thắt có profile. | Lưu config/fingerprint/code revision, mọi nghiệm qua validator, search không tệ hơn nghiệm đầu; báo trung vị và khoảng thời gian, không mặc định ALNS thắng. Thay bộ giải phải có test hồi quy riêng. |
| P2 · 8 | Nghiệm thu cuối: pytest + AppTest + trình duyệt desktop/mobile; cập nhật README theo UI mới; kiểm tra một bản checkout sạch. | Chạy preset, Kris, JSON đúng/sai, đổi cấu hình, đổi bộ lọc, tải rồi validate JSON đều đạt; không tràn ngang toàn trang ở 390px, bảng có thể cuộn riêng; tab/bàn phím và focus dùng được; 3 người mới chạy và tải kết quả trong 3 phút không cần hướng dẫn miệng. |

Thứ tự phụ thuộc: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Ưu tiên hoàn thành P0 trước. Không đổi framework, thêm tài khoản, nhiều depot hoặc mô phỏng tắc nghẽn trong đợt này. Tiêu chí 3 phút là mục tiêu cần đo, chưa phải kết quả đã đạt.

## Quy tắc đưa lên Git

Đã bổ sung `.gitignore` ở gốc repository và trong project. **Giữ:** code, test, README/kế hoạch, configs, JSON Kris đã chuyển để demo chạy ngay, ví dụ synthetic, manifest nguồn, một file Kris gốc dùng cho test, báo cáo/CSV tổng hợp và bộ demo nhỏ. **Bỏ qua:** môi trường Python, cache, build, file bí mật, cấu hình editor/công cụ cục bộ, ZIP và phần lớn dữ liệu gốc giải nén, profiler, nghiệm benchmark hàng loạt và output phát sinh.

File bị ignore vẫn ở máy. `.gitignore` không bỏ theo dõi file đã commit; không chạy `git rm --cached` hàng loạt. Bản clone mới muốn chạy toàn bộ benchmark nguồn phải tải/giải nén dữ liệu theo `data/README.md`; JSON đã chuyển vẫn phục vụ demo. Raw benchmark bị ignore nên các báo cáo giữ trong Git chỉ là bản tổng hợp, không thay thế kho lưu nghiệm đầy đủ; đợt công bố cần lưu archive kết quả riêng kèm manifest.

## Hoàn thành khi

Toàn bộ 8 mục có bằng chứng kiểm tra; người mới thực hiện trọn luồng mà không hiểu tên thuật toán; xuất kết quả vẫn kiểm chứng được; báo cáo tốc độ/chất lượng dựa trên lần đo mới. Kế hoạch cũ `warehouse-improvement-plan.md` giữ làm lịch sử, kế hoạch này ưu tiên cho đợt nâng cấp tiếp theo.
