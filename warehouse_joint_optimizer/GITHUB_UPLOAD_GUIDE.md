# Quyết định file đưa lên GitHub

Tài liệu này chốt phạm vi public cho dự án `warehouse_joint_optimizer`. Mục tiêu là một clone mới có thể cài đặt, chạy demo tổng hợp và đọc được cách đánh giá; dữ liệu benchmark lớn hoặc dữ liệu tác giả vẫn nằm ở máy local.

## Nên đưa lên GitHub

- Mã nguồn: `warehouse_opt/`, `demo/`, `tests/`, `scripts/`, `configs/`.
- Tài liệu: `README.md`, `DESIGN.md`, `demo-upgrade-plan.md`, `DANH_GIA_TONG_QUAN_DU_AN.md`, `docs/`, `data/README.md`.
- Cấu hình và môi trường: `pyproject.toml`, `requirements.txt`, `.gitignore`, `.streamlit/config.toml`.
- Dữ liệu nhỏ do dự án tự tạo: `data/synthetic/tiny_4.json`, `data/synthetic/demo_30.json`.
- Báo cáo có thể tái kiểm tra: `results/demo_upgrade_benchmark/REPORT.md`, `summary.json`, `config.json`; các report/summary/config/runs.csv nhỏ trong `results/smoke/`, `results/replication/`, `results/vns_comparison/` và `results/kris_author/` là phần minh chứng tùy chọn. Có thể thêm `results/demo/` nếu muốn minh họa output.
- `data/raw/manifest.json` nếu muốn công khai nguồn tải và checksum. File này không chứa dữ liệu benchmark.

## Không nên đưa lên GitHub

- Toàn bộ archive và dữ liệu benchmark tác giả trong `data/raw/`.
- Toàn bộ dữ liệu chuyển đổi trong `data/processed/`, trừ khi đã xác nhận quyền phân phối.
- Output thô, profile, log, screenshot audit và file tải xuống trong `results/**/raw/`, `results/**/profile*/`, `results/ui_audit/`.
- Các file cá nhân hoặc sinh tự động như `.env`, secret, cache, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `build/`, `dist/`.
- `results/**/manifest.json` nếu còn đường dẫn máy local, tên môi trường hoặc trạng thái working tree; Git đang ignore các file này, chỉ dùng `git add -f` sau khi đã làm sạch nếu thật sự cần công khai.
- `warehouse-improvement-plan.md` hiện là kế hoạch cũ, còn checkbox chưa cập nhật; chỉ đưa lên sau khi đã đồng bộ với trạng thái thực tế.

`.gitignore` của project đã bỏ qua raw/processed data theo chính sách trên. Việc bỏ qua không xóa file local và không ảnh hưởng việc chạy benchmark trên máy đã có dữ liệu.

Nên đặt `warehouse_joint_optimizer` là root của repository GitHub. Nếu vẫn dùng repository cha, không stage `shipper_optimizer/`, `.agents/` hoặc các tài liệu legacy nằm ngoài thư mục project.

## Cách stage an toàn

Chạy từ thư mục workspace và chỉ stage thư mục dự án; không dùng `git add .` ở repository cha vì repository này còn có nội dung cũ ngoài phạm vi dự án.

```powershell
# Chỉ cần nếu GitHub repo là repository cha:
git add .gitignore
git add warehouse_joint_optimizer/.gitignore
git add warehouse_joint_optimizer/warehouse_opt warehouse_joint_optimizer/demo
git add warehouse_joint_optimizer/tests warehouse_joint_optimizer/scripts warehouse_joint_optimizer/configs
git add warehouse_joint_optimizer/README.md warehouse_joint_optimizer/DESIGN.md
git add warehouse_joint_optimizer/demo-upgrade-plan.md warehouse_joint_optimizer/DANH_GIA_TONG_QUAN_DU_AN.md
git add warehouse_joint_optimizer/docs warehouse_joint_optimizer/data/README.md
git add warehouse_joint_optimizer/pyproject.toml warehouse_joint_optimizer/requirements.txt
git add warehouse_joint_optimizer/.streamlit/config.toml
git add warehouse_joint_optimizer/data/synthetic/tiny_4.json warehouse_joint_optimizer/data/synthetic/demo_30.json
git add warehouse_joint_optimizer/results/demo_upgrade_benchmark/REPORT.md
git add warehouse_joint_optimizer/results/demo_upgrade_benchmark/summary.json
git add warehouse_joint_optimizer/results/demo_upgrade_benchmark/config.json
git add warehouse_joint_optimizer/docs/demo-screenshots
git status --short
git diff --cached --stat
```

Trước khi commit, kiểm tra danh sách staged và quét chuỗi nhạy cảm:

```powershell
git diff --cached --name-only
rg -n 'D:\\Miniconda|password|token|secret|api[_-]?key' --hidden --glob '!*.png' --glob '!*.prof' warehouse_joint_optimizer
```

Nếu cần chia sẻ benchmark tác giả cho giảng viên, gửi riêng archive hoặc dùng kho private; không đưa chúng vào kho public chỉ để làm dropdown demo. Demo public mặc định dùng dữ liệu tổng hợp nhỏ.
