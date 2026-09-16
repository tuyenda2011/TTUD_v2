# Nghiệm thu nâng cấp demo — 16/09/2026

## Cập nhật sau lượt rà soát tiếp

Đã thêm 10 test hồi quy (đều tái hiện lỗi trước khi vá) và sửa kiểm tra metadata units/layout, nhãn đơn vị tùy chỉnh và cấu trúc snapshot. Demo có thêm bảng thứ tự điểm lấy để đọc trên màn hình nhỏ; sơ đồ dùng nhãn tọa độ thay vì giả định x/y cùng đơn vị khoảng cách trên cạnh. **Bộ test hiện tại: 102 test đạt trên Conda TTUD.** Các số 92 bên dưới ghi nhận mốc nghiệm thu trước bản sửa này. Không chạy lại benchmark 96 nghiệm sau thay đổi validation; giữ rõ nguồn gốc số liệu cũ.

Xem [đánh giá tổng quan dự án](../DANH_GIA_TONG_QUAN_DU_AN.md) để phân biệt chất lượng kỹ thuật hiện có với những phần còn cần hoàn thiện trước khi nộp/bảo vệ.

## Môi trường và phạm vi

- Conda environment `TTUD`, Python 3.12.14.
- Streamlit 1.62.0, Matplotlib 3.11.1, Pandas 3.0.5, Pytest 9.1.1.
- Nhánh `feature/warehouse-demo-upgrade`; thay đổi đang ở working tree, chưa commit/push.
- Giữ bộ giải, chuẩn hóa B0 và validator; thay luồng trình bày, quản lý trạng thái, đồ thị và công cụ kiểm chứng.
- Dependency demo dùng Streamlit >=1.62 cho API `width`; chấp nhận Pandas 2.x/3.x. Lần này kiểm chứng trên Pandas 3.0.5, chưa chạy ma trận mọi phiên bản tối thiểu.

## Những gì đã kiểm tra

| Hạng mục | Kết quả |
|---|---|
| Baseline trước thay đổi | 87 test đạt trên TTUD |
| Core, CLI, state, AppTest sau thay đổi | 92 test đạt |
| Bộ file đủ điều kiện đưa lên Git | Sao chép sang thư mục mới, chạy test bằng TTUD; 92 test đạt, không cần toàn bộ ZIP/data gốc/cache |
| Kiểm tra tĩnh | Ruff trên các module demo, plots, script mới và test liên quan |
| Trình duyệt | Microsoft Edge headless: 1440×900 và 390×844; không có lỗi JavaScript trong các luồng đã thử |
| Luồng chính | Mẫu 10 đơn, chạy lại 30 đơn, Kris, JSON sai và JSON đúng |
| Tính nhất quán | Đổi cấu hình báo snapshot cũ; JSON lỗi không để kết quả cũ hiện như thành công; nhân viên rảnh không gây lỗi bộ lọc |
| Xuất dữ liệu | Tải nghiệm và toàn bộ snapshot qua trình duyệt, đọc JSON và kiểm tra lại bằng validator |
| Responsive và bàn phím | Không tràn ngang trang/nội dung chính ở 390px; kiểm tra chuyển tab bằng phím mũi tên và Tab |
| Đồ thị | Đã xem ảnh tuyến 10/30 đơn; điểm lấy được đánh số, màu tuyến/lịch thống nhất, lịch tách riêng |

Ảnh gốc và log chạy nằm ở `results/ui_audit/` (bỏ qua bởi Git, tái tạo bằng script). Hai ảnh tổng quan được giữ trong [demo-screenshots](demo-screenshots/) để đối chiếu bản giao diện này. Bản sao sạch là mô phỏng đóng gói từ working tree theo quy tắc Git; không khẳng định thay đổi chưa commit đã có trên remote.

## Benchmark thực đo

Xem [báo cáo 96 nghiệm](../results/demo_upgrade_benchmark/REPORT.md), [cấu hình](../results/demo_upgrade_benchmark/config.json), [tổng hợp](../results/demo_upgrade_benchmark/summary.json) và [manifest](../results/demo_upgrade_benchmark/manifest.json).

- Synthetic: 10/30/100 đơn, seed dữ liệu 42, sức chứa 20. Kris: một bộ mỗi nhóm 6/12/18 đơn, file cụ thể có trong config.
- B0/B2 chạy một lần mỗi bộ/ngân sách; ALNS/VNS chạy seed 7/42/101 ở ngân sách 1/3 giây, tối đa 2.000 vòng.
- 96/96 nghiệm qua validator; mọi search không trả nghiệm xấu hơn nghiệm khởi tạo.
- Tổng thời gian mỗi lần giải: khoảng 0,003–3,009 giây; khởi tạo lớn nhất khoảng 0,109 giây trong mẫu đo này.
- Ví dụ 100 đơn, ngân sách 3 giây: F trung vị B0 0,70026; B2 0,54038; ALNS 0,53501; VNS 0,51564. Đây là một mẫu, không phải kết luận tổng quát VNS luôn tốt hơn.
- Các lần giải chạy tuần tự trên máy đang phát triển, không phải môi trường benchmark phần cứng cô lập. Chưa đo RAM. Không có tuyên bố tăng tốc trước/sau vì bộ giải không thay đổi.
- Manifest ghi revision hiện có, cờ working tree có thay đổi và hash mã nguồn tại lúc đo. Một số file giao diện/đồ thị được chỉnh tiếp sau khi đo; mã giải giữ nguyên. Raw nghiệm và instance benchmark lưu cục bộ, không đưa lên Git; muốn kiểm toán đầy đủ cần chạy lại hoặc lưu riêng cả thư mục kết quả.

## Tái lập bằng TTUD

Chạy từ thư mục `warehouse_joint_optimizer`:

```powershell
conda activate TTUD
python -m pip install -r requirements.txt
python -m pip install ruff playwright
python -m pytest -q
python scripts/check_clean_checkout.py
python scripts/benchmark_demo_upgrade.py
```

Kiểm tra trình duyệt cần Microsoft Edge đã cài. Mở server trong terminal riêng:

```powershell
conda activate TTUD
python -m streamlit run demo/app.py --server.headless true --server.port 8503 --server.address 127.0.0.1
```

Sau đó chạy:

```powershell
python scripts/check_demo_browser.py
```

## Chưa nghiệm thu bằng người thật

Chưa mời 3 người mới thực hiện luồng trong 3 phút. Cần đo riêng thời gian tìm nút chạy, hiểu đơn trễ, tìm tuyến và tải kết quả; ghi lỗi hiểu nhầm thay vì chỉ hỏi cảm nhận. Kiểm tra mobile hiện dùng viewport giả lập của Edge, chưa phải điện thoại thật hoặc kiểm thử đầy đủ với screen reader. Mục 8 trong kế hoạch vẫn mở cho phần này.
