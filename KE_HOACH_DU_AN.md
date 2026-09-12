# 📋 KẾ HOẠCH DỰ ÁN: TỐI ƯU HÓA LỘ TRÌNH GIAO HÀNG (VRP)

---

## 1. TÊN ĐỀ TÀI

**"Nghiên cứu và ứng dụng thuật toán tối ưu hóa lộ trình giao hàng cho doanh nghiệp vừa và nhỏ"**

*(Research and Application of Optimization Algorithms for Delivery Route Planning)*

---

## 2. MỤC TIÊU DỰ ÁN

### 2.1 Mục tiêu chính
- Nghiên cứu các thuật toán tối ưu hóa lộ trình (VRP - Vehicle Routing Problem)
- Cài đặt và so sánh hiệu quả của các thuật toán
- Xây dựng ứng dụng thực tế có thể sử dụng được

### 2.2 Mục tiêu cụ thể
| STT | Mục tiêu | Chỉ tiêu đo lường |
|-----|----------|-------------------|
| 1 | Nghiên cứu lý thuyết VRP | Tài liệu 10-15 trang |
| 2 | Cài đặt ≥3 thuật toán | Code chạy được, có test |
| 3 | So sánh hiệu năng | Biểu đồ, bảng số liệu |
| 4 | Demo visualization | Giao diện trực quan |
| 5 | Docker đóng gói | Chạy được bằng docker |

---

## 3. PHẠM VI NGHIÊN CỨU

### 3.1 Bài toán cơ bản (CVRP - Capacitated VRP)
```
- Có 1 kho hàng trung tâm
- Có N điểm giao hàng với nhu cầu khác nhau
- Có K xe tải với sức chứa giới hạn
- Tìm lộ trình tối ưu: tổng quãng đường ngắn nhất
```

### 3.2 Các biến thể mở rộng (nếu thời gian cho phép)
- **VRPTW**: Thêm ràng buộc thời gian giao hàng
- **VRPPD**: Pickup and Delivery (lấy và giao)
- **MDVRP**: Nhiều kho hàng

---

## 4. CÁC THUẬT TOÁN NGHIÊN CỨU

### 4.1 Thuật toán cổ điển (Exact Algorithms)
| Thuật toán | Độ phức tạp | Ưu điểm | Nhược điểm |
|------------|-------------|---------|------------|
| Brute Force | O(n!) | Chính xác 100% | Chỉ dùng cho n < 10 |
| Branch and Bound | O(2^n) | Chính xác, nhanh hơn | Tốn bộ nhớ |

### 4.2 Thuật toán heuristics (Tìm kiếm xấp xỉ)
| Thuật toán | Độ phức tạp | Ưu điểm | Nhược điểm |
|------------|-------------|---------|------------|
| Nearest Neighbor | O(n²) | Đơn giản, nhanh | Chất lượng trung bình |
| 2-Opt | O(n²) | Cải thiện lộ trình hiện tại | Phụ thuộc lộ trình ban đầu |
| Clarke-Wright Savings | O(n²) | Hiệu quả cho CVRP | Không tối ưu lắm |

### 4.3 Thuật toán metaheuristics (Tìm kiếm meta)
| Thuật toán | Độ phức tạp | Ưu điểm | Nhược điểm |
|------------|-------------|---------|------------|
| Genetic Algorithm (GA) | O(gen × pop × n) | Linh hoạt, mạnh mẽ | Cần tuning tham số |
| Ant Colony Optimization | O(iter × ant × n²) | Tự nhiên, song song | Hội tụ chậm |

### 4.4 Chọn thuật toán cài đặt (tối thiểu 3)
1. ✅ **Clarke-Wright Savings Algorithm** - heuristics cổ điển
2. ✅ **2-Opt Local Search** - cải thiện lộ trình
3. ✅ **Genetic Algorithm** - metaheuristics phổ biến
4. ⬜ **Ant Colony Optimization** - (nếu thời gian)

---

## 5. CẤU TRÚC DỰ ÁN

```
d:\TTUD\
├── 📄 BAO_CAO/
│   ├── main.tex              (LaTeX source)
│   ├── main.pdf              (File nộp)
│   ├── chapters/
│   │   ├── 1_gioi_thieu.tex
│   │   ├── 2_co_so_ly_thuyet.tex
│   │   ├── 3_thuat_toan.tex
│   │   ├── 4_cait_dat.tex
│   │   ├── 5_thuc_nghiem.tex
│   │   └── 6_ket_luan.tex
│   └── references.bib
│
├── 🐍 SOURCE/
│   ├── main.py               (Entry point)
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── brute_force.py
│   │   ├── nearest_neighbor.py
│   │   ├── clarke_wright.py
│   │   ├── two_opt.py
│   │   ├── genetic_algorithm.py
│   │   └── ant_colony.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── plot_routes.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_loader.py
│   │   └── metrics.py
│   ├── data/
│   │   ├── sample_10.json     (10 điểm)
│   │   ├── sample_25.json     (25 điểm)
│   │   └── sample_50.json     (50 điểm)
│   └── requirements.txt
│
├── 🐳 DOCKER/
│   ├── Dockerfile            (Multi-stage build)
│   └── docker-compose.yml
│
├── 📊 BENCHMARK/
│   └── benchmark_results.csv
│
├── 📝 README.md
├── 📋 KE_HOACH_DU_AN.md      (File này)
└── 📜 LICENSE
```

---

## 6. NỘI DUNG BÁO CÁO

### Chương 1: Giới thiệu (2 trang)
- 1.1 Bối cảnh và lý do chọn đề tài
- 1.2 Mục tiêu nghiên cứu
- 1.3 Phạm vi nghiên cứu
- 1.4 Cấu trúc báo cáo

### Chương 2: Cơ sở lý thuyết (4 trang)
- 2.1 Bài toán người đi du lịch (TSP)
- 2.2 Bài toán giao hàng (VRP)
- 2.3 Các biến thể của VRP
- 2.4 Ứng dụng thực tế

### Chương 3: Thuật toán đề xuất (4 trang)
- 3.1 Clarke-Wright Savings
- 3.2 2-Opt Local Search
- 3.3 Genetic Algorithm
- 3.4 So sánh các thuật toán

### Chương 4: Cài đặt (3 trang)
- 4.1 Môi trường phát triển
- 4.2 Cấu trúc chương trình
- 4.3 Các module chính

### Chương 5: Kết quả thực nghiệm (4 trang)
- 5.1 Dữ liệu thử nghiệm
- 5.2 Kết quả so sánh thuật toán
- 5.3 Visualization lộ trình
- 5.4 Phân tích và nhận xét

### Chương 6: Kết luận (2 trang)
- 6.1 Tổng kết kết quả
- 6.2 Hạn chế
- 6.3 Hướng phát triển

---

## 7. HƯỚNG DẪN SỬ DỤNG

### 7.1 Chạy trực tiếp (không Docker)
```bash
# Cài đặt dependencies
pip install -r SOURCE/requirements.txt

# Chạy demo
cd SOURCE
python main.py --algorithm ga --points 25
```

### 7.2 Chạy với Docker
```bash
# Build image
docker build -t vrp-optimizer .

# Chạy với docker-compose
docker-compose up

# Hoặc chạy trực tiếp
docker run -v $(pwd)/SOURCE/data:/app/data vrp-optimizer python main.py --algorithm ga
```

---

## 8. TIÊU CHÍ ĐÁNH GIÁ

| Tiêu chí | Trọng số | Mô tả |
|----------|----------|-------|
| Nội dung lý thuyết | 30% | Đầy đủ, chính xác, có trích dẫn |
| Cài đặt thuật toán | 25% | Code sạch, có comment, chạy được |
| Kết quả thực nghiệm | 20% | Có số liệu, biểu đồ, so sánh |
| Ứng dụng thực tế | 15% | Demo được, có ý nghĩa thực tiễn |
| Trình bày & Docker | 10% | Báo cáo đẹp, đóng gói tốt |

---

## 9. DEADLINE & MILESTONES

| Tuần | Deadline | Công việc |
|------|----------|-----------|
| Tuần 1 | ✅ | Hoàn thành kế hoạch này |
| Tuần 2 | 📅 | Nộp Chương 1-2: Lý thuyết |
| Tuần 3 | 📅 | Nộp Chương 3: Code thuật toán |
| Tuần 4 | 📅 | Nộp Chương 4-5: Demo + Benchmark |
| Tuần 5 | 📅 | Nộp báo cáo hoàn chỉnh + Docker |
| Tuần 6 | 📅 | Bảo vệ |

---

## 10. TÀI LIỆU THAM KHẢO

1. Dantzig, G. B., & Ramser, J. H. (1959). The Truck Dispatching Problem.
2. Clarke, G., & Wright, J. W. (1964). Scheduling of Vehicles from a Central Depot.
3. Holland, J. H. (1975). Adaptation in Natural and Artificial Systems.
4. Dorigo, M., & Stützle, T. (2004). Ant Colony Optimization.
5. Golden, B. L., & Assad, A. A. (1988). Vehicle Routing: Methods and Studies.

---

## 11. CÔNG CỤ SỬ DỤNG

| Công cụ | Mục đích |
|---------|----------|
| Python 3.10+ | Ngôn ngữ lập trình |
| NumPy, Pandas | Xử lý số liệu |
| Matplotlib, Plotly | Visualization |
| NetworkX | Xử lý đồ thị |
| LaTeX (Overleaf) | Viết báo cáo |
| Docker, Docker Compose | Đóng gói |
| VS Code | IDE |

---

## ✅ XÁC NHẬN

Nếu bạn đồng ý với kế hoạch này, tôi sẽ bắt đầu tạo:

1. ✅ Cấu trúc thư mục
2. ✅ Báo cáo LaTeX (Chương 1-6)
3. ✅ Source code Python đầy đủ
4. ✅ Dockerfile + docker-compose.yml
5. ✅ Dữ liệu test + README

**Gõ "Bắt đầu" để tôi triển khai ngay!**
