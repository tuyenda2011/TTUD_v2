---
name: Warehouse Workspace
colors:
  primary: "#176B5B"
  surface: "#FFFFFF"
  neutral: "#F5F7F6"
  on-surface: "#1C302B"
  muted: "#53665F"
  border: "#DCE5E0"
  error: "#B42318"
  warning: "#8A5210"
typography:
  headline-lg: {fontFamily: "Segoe UI, sans-serif", fontSize: 32px, fontWeight: 650, lineHeight: 1.2}
  headline-md: {fontFamily: "Segoe UI, sans-serif", fontSize: 24px, fontWeight: 600, lineHeight: 1.3}
  body-md: {fontFamily: "Segoe UI, sans-serif", fontSize: 16px, fontWeight: 400, lineHeight: 1.6}
  body-sm: {fontFamily: "Segoe UI, sans-serif", fontSize: 14px, fontWeight: 400, lineHeight: 1.5}
  label-md: {fontFamily: "Segoe UI, sans-serif", fontSize: 14px, fontWeight: 600, lineHeight: 1.4}
rounded: {sm: 4px, md: 8px}
spacing: {xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px}
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    height: 44px
---

# Warehouse Workspace

## Overview
Giao diện thao tác kho dành cho người mới. Giữ Streamlit, phân cấp bằng khoảng trắng và nội dung ngắn. Tham khảo cách tổ chức token và phân cấp trung tính của [Cal.com design analysis](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/cal/DESIGN.md); bảng màu và bố cục ở đây dành riêng cho demo kho.

## Colors
Một màu xanh đậm cho hành động chính; nền trắng và nền sidebar trung tính. Chỉ dùng cảnh báo cho dữ liệu lỗi hoặc cấu hình chưa chạy. Màu nhân viên được chia sẻ giữa tuyến và lịch; luôn kèm nhãn chữ.

## Typography
Font hệ thống hỗ trợ tiếng Việt, không tải font từ Internet. H1 32px, tiêu đề vùng 24px, nội dung 16px. Đơn vị nằm trong nhãn hoặc cạnh giá trị; không viết tắt thuật ngữ khó hiểu ở luồng chính.

## Layout
Desktop: sidebar khoảng 300px; nội dung tối đa 1120px. Mobile: sidebar thu gọn bằng nút gốc của Streamlit, chỉ số xếp dọc, bảng cuộn trong vùng riêng. Không khóa chiều cao viewport.

```text
SIDEBAR                       NỘI DUNG
Chuẩn bị dữ liệu              Tối ưu lấy hàng
Nguồn + trường phù hợp        Tóm tắt dữ liệu / trạng thái lần chạy
[Nâng cao ▸]                  Chọn phương án · Tải kết quả
[Chạy tối ưu]                 Đơn trễ | Hoàn tất | Quãng đường
                              Tổng quan | Tuyến & lịch | Chi tiết
                              Nội dung đang chọn
                              [Phân tích thuật toán ▸]
```

## Elevation & Depth
Không shadow hoặc card bao quanh mọi vùng. Dùng divider và nền sidebar nhẹ. Chỉ một thông báo tổng hợp khi cần; văn bản giải thích nằm trong help/expander.

## Shapes
Bo góc 8px cho input/nút. Giữ control native để hỗ trợ bàn phím và focus.

## Components
- Sidebar chỉ hiện input thuộc nguồn đang dùng. Nâng cao chứa seed, ngân sách, thêm VNS và nhóm đối chứng.
- Chưa chạy: tóm tắt bộ dữ liệu và ba bước hướng dẫn ngắn; có nút chạy ở nội dung để mobile không cần mở sidebar.
- Đang chạy: vô hiệu hóa nút chạy, tiến độ theo thuật toán. Hoàn tất lưu snapshot nguyên vẹn.
- Thay cấu hình: kết quả giữ tên/cấu hình cũ, một thông báo yêu cầu chạy lại. Không đổi nhãn theo nháp.
- Lỗi: thông báo rõ và bỏ snapshot cũ khỏi vùng kết quả.
- Thành công: chỉ ba KPI chính; F, tổng độ trễ, bảng đối chứng, trace trong phân tích.
- Bản đồ mặc định một chuyến, nhãn điểm đánh số; có bộ lọc nhân viên và chuyến, tùy chọn tất cả. Lịch tách vùng riêng, nhân viên rảnh có trạng thái rõ.
- Xuất: kết quả, dữ liệu đầu vào và snapshot chứa toàn bộ lần chạy.

## Do's and Don'ts
Không dùng màu làm dấu hiệu duy nhất, không mặc định mọi thuật toán cùng chạy, không gán đơn vị mét/phút cho Kris. Không hứa tối ưu tuyệt đối. Tránh CSS tác động vào DOM sâu; kiểm tra lại responsive sau mỗi thay đổi Streamlit.
