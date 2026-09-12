# 🚚 SHIPPER ROUTE OPTIMIZER
## Kế Hoạch Chi Tiết Triển Khai

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1 Mô tả
- **Tên dự án**: Shipper Route Optimizer - Tối ưu lộ trình giao hàng cho shipper
- **Địa bàn**: Hà Nội, Việt Nam
- **Mục tiêu**: Tối ưu hóa lộ trình giao hàng để giảm chi phí nhiên liệu, thời gian

### 1.2 Dataset
- **30 điểm giao** trên địa bàn Hà Nội (quận Cầu Giấy, Thanh Xuân, Đống Đa, Hoàn Kiếm)
- **1 kho trung tâm** (kho V9 Hoàng Mai hoặc tương đương)
- **1 xe tải** hoặc **3 xe tải** (tùy bài toán TSP hoặc VRP)

---

## 2. CẤU TRÚC THUẬT TOÁN

### 📌 ALGORITHM 1: DIJKSTRA - Đường Đi Ngắn Nhất

#### Mục đích
- Tính khoảng cách ngắn nhất giữa 2 điểm bất kỳ
- Xây dựng ma trận khoảng cách cho các thuật toán tiếp theo

#### Input/Output
```
Input:  Graph G = (V, E) với trọng số w(u,v) = khoảng cách Haversine
Output: Khoảng cách ngắn nhất từ đỉnh nguồn đến mọi đỉnh khác
```

#### Độ phức tạp
- **Time**: O((V + E) log V) với Min-Heap
- **Space**: O(V)

#### Cài đặt chi tiết
```python
# src/algorithms/dijkstra.py

class Dijkstra:
    def __init__(self, graph: Dict[str, Location]):
        self.graph = graph
        self.locations = list(graph.keys())
    
    def build_distance_matrix(self) -> np.ndarray:
        """Xây dựng ma trận khoảng cách n x n"""
        n = len(self.locations)
        matrix = np.zeros((n, n))
        
        for i, loc_i in enumerate(self.locations):
            for j, loc_j in enumerate(self.locations):
                if i != j:
                    matrix[i][j] = self.graph[loc_i].distance_to(
                        self.graph[loc_j]
                    )
        return matrix
    
    def shortest_path(self, source: str, target: str) -> Tuple[float, List[str]]:
        """Tìm đường đi ngắn nhất từ source đến target"""
        # Priority queue: (distance, node)
        dist = {loc: float('inf') for loc in self.locations}
        prev = {loc: None for loc in self.locations}
        dist[source] = 0
        
        pq = [(0, source)]
        visited = set()
        
        while pq:
            d, u = heapq.heappop(pq)
            
            if u in visited:
                continue
            visited.add(u)
            
            if u == target:
                break
            
            for v in self.locations:
                if v != u and v not in visited:
                    alt = dist[u] + self.graph[u].distance_to(self.graph[v])
                    if alt < dist[v]:
                        dist[v] = alt
                        prev[v] = u
                        heapq.heappush(pq, (alt, v))
        
        # Reconstruct path
        path = []
        current = target
        while current:
            path.append(current)
            current = prev[current]
        path.reverse()
        
        return dist[target], path
```

#### Ứng dụng trong đồ án
```
1. Tính khoảng cách từ kho đến 30 điểm giao
2. Tính khoảng cách giữa các cặp điểm giao
3. Xây dựng ma trận khoảng cách 31 x 31
```

---

### 📌 ALGORITHM 2: NEAREST NEIGHBOR - Heuristic Xây Dựng Lộ Trình TSP

#### Mục đích
- Giải bài toán TSP (Traveling Salesman Problem)
- Xây dựng lộ trình giao hàng nhanh cho tất cả các điểm

#### Bài toán TSP
```
Cho N điểm, tìm lộ trình ngắn nhất:
- Bắt đầu từ kho
- Đi qua tất cả N điểm giao, mỗi điểm đúng 1 lần
- Quay về kho
```

#### Thuật toán
```
1. Bắt đầu từ kho
2. Chọn điểm chưa thăm gần nhất với điểm hiện tại
3. Lặp lại cho đến khi thăm hết tất cả điểm
4. Quay về kho
```

#### Độ phức tạp
- **Time**: O(n²) - nhanh, phù hợp cho n lớn
- **Space**: O(n)

#### Cài đặt chi tiết
```python
# src/algorithms/nearest_neighbor.py

class NearestNeighbor:
    """TSP heuristic: Greedy construction"""
    
    def __init__(self, distance_matrix: np.ndarray, depot_idx: int = 0):
        self.dist = distance_matrix
        self.n = len(distance_matrix)
        self.depot_idx = depot_idx
    
    def solve(self) -> Tuple[List[int], float]:
        """
        Tìm lộ trình TSP
        
        Returns:
            route: Danh sách các đỉnh theo thứ tự thăm
            total_distance: Tổng khoảng cách
        """
        unvisited = set(range(self.n))
        route = [self.depot_idx]
        current = self.depot_idx
        unvisited.remove(current)
        
        while unvisited:
            # Tìm điểm gần nhất chưa thăm
            nearest = min(
                unvisited,
                key=lambda v: self.dist[current][v]
            )
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        # Quay về depot
        route.append(self.depot_idx)
        
        # Tính tổng khoảng cách
        total_dist = sum(
            self.dist[route[i]][route[i+1]]
            for i in range(len(route) - 1)
        )
        
        return route, total_dist
    
    def evaluate_route(self, route: List[int]) -> float:
        """Tính tổng khoảng cách của một lộ trình"""
        return sum(
            self.dist[route[i]][route[i+1]]
            for i in range(len(route) - 1)
        )
```

#### Đặc điểm
- **Ưu điểm**: Nhanh O(n²), dễ cài đặt
- **Nhược điểm**: Không đảm bảo tối ưu toàn cục
- **Quality**: Thường cho kết quả trong khoảng 15-25% so với optimal

---

### 📌 ALGORITHM 3 (TỐI ƯU): HYBRID ALGORITHM - Clarke-Wright Savings + 2-Opt

#### Mục đích
- Giải bài toán VRP (Vehicle Routing Problem) với nhiều xe
- Tối ưu hóa lộ trình sau khi xây dựng bằng heuristic

#### Bài toán VRP
```
Cho:
- 1 kho + N điểm giao
- M xe tải, mỗi xe sức chứa C
- Mỗi điểm có nhu cầu w_i

Tìm: Các lộ trình cho từng xe sao cho:
- Mỗi điểm được thăm đúng 1 lần
- Tổng nhu cầu trên mỗi xe ≤ C
- Tổng khoảng cách nhỏ nhất
```

#### THUẬT TOÁN CHÍNH: Clarke-Wright Savings Algorithm

##### Ý tưởng
```
Thay vì đi riêng từng cặp (i → kho → j),
Ghép lại thành 1 lộ trình (i → j) nếu tiết kiệm được khoảng cách

Savings(i,j) = dist(i, kho) + dist(kho, j) - dist(i, j)
```

##### Các bước
```
1. Tính savings cho tất cả cặp điểm (i, j)
2. Sắp xếp savings giảm dần
3. Ghép các cặp có savings cao nhất thành lộ trình
4. Lặp lại cho đến khi không thể ghép thêm
```

##### Cài đặt chi tiết
```python
# src/algorithms/clarke_wright.py

class ClarkeWrightSavings:
    """VRP heuristic: Clarke-Wright Savings Algorithm"""
    
    def __init__(self, distance_matrix: np.ndarray, 
                 demands: List[float], 
                 capacity: float,
                 depot_idx: int = 0):
        self.dist = distance_matrix
        self.demands = demands
        self.capacity = capacity
        self.depot_idx = depot_idx
        self.n = len(distance_matrix)
    
    def compute_savings(self) -> List[Tuple[float, int, int]]:
        """Tính savings cho tất cả cặp điểm"""
        savings = []
        
        for i in range(self.n):
            if i == self.depot_idx:
                continue
            for j in range(self.n):
                if j == self.depot_idx or i >= j:
                    continue
                
                # Savings = d(i,kho) + d(kho,j) - d(i,j)
                s = (self.dist[i][self.depot_idx] + 
                     self.dist[self.depot_idx][j] - 
                     self.dist[i][j])
                savings.append((s, i, j))
        
        # Sắp xếp giảm dần theo savings
        savings.sort(reverse=True, key=lambda x: x[0])
        return savings
    
    def solve(self) -> List[List[int]]:
        """
        Giải VRP bằng Clarke-Wright Savings
        
        Returns:
            routes: Danh sách các lộ trình, mỗi lộ trình cho 1 xe
        """
        # Mỗi điểm bắt đầu là 1 lộ trình riêng: depot → i → depot
        routes = [[self.depot_idx, i, self.depot_idx] for i in range(self.n) 
                  if i != self.depot_idx]
        
        # Route lookup: điểm i thuộc route nào
        route_of = {i: idx for idx, route in enumerate(routes) 
                    for i in route if i != self.depot_idx}
        
        # Kiểm tra 2 điểm có thể ghép được không
        def can_merge(route1_idx: int, route2_idx: int, 
                      point1: int, point2: int) -> bool:
            # point1 phải ở cuối route1 (trước depot)
            # point2 phải ở đầu route2 (sau depot)
            if route1_idx == route2_idx:
                return False
            
            r1, r2 = routes[route1_idx], routes[route2_idx]
            if r1[-2] != point1 or r2[1] != point2:
                return False
            
            # Kiểm tra sức chứa
            total_demand = sum(self.demands[i] for i in r1[:-1] if i != self.depot_idx) + \
                          sum(self.demands[i] for i in r2[:-1] if i != self.depot_idx)
            
            return total_demand <= self.capacity
        
        # Ghép các cặp có savings cao
        savings = self.compute_savings()
        
        for s, i, j in savings:
            if i not in route_of or j not in route_of:
                continue
            
            ri, rj = route_of[i], route_of[j]
            
            if can_merge(ri, rj, i, j):
                # Ghép route: depot - ... - i - depot - j - ... - depot
                # Trở thành: depot - ... - i - j - ... - depot
                routes[ri] = routes[ri][:-1] + routes[rj][1:]
                
                # Cập nhật route_of
                for p in routes[ri]:
                    if p != self.depot_idx:
                        route_of[p] = ri
                
                # Xóa route rj
                del routes[rj]
                route_of[j] = None  # j không còn là cuối route
        
        return routes
```

#### THUẬT TOÁN CẢI TIẾN: 2-Opt Local Search

##### Ý tưởng
```
Sau khi có lộ trình ban đầu từ Clarke-Wright,
Cải thiện bằng cách đảo ngược các cạnh nếu tổng khoảng cách giảm

Trước: ... → u → v → ... → x → y → ...
Sau:   ... → u → x → ... → v → y → ...

Điều kiện: dist(u,v) + dist(x,y) > dist(u,x) + dist(v,y)
```

##### Cài đặt
```python
# src/algorithms/two_opt.py

class TwoOpt:
    """Local search improvement cho TSP/VRP"""
    
    def __init__(self, distance_matrix: np.ndarray):
        self.dist = distance_matrix
        self.n = len(distance_matrix)
    
    def improve(self, route: List[int], 
                max_iterations: int = 1000) -> Tuple[List[int], float]:
        """
        Cải thiện lộ trình bằng 2-opt
        
        Args:
            route: Lộ trình ban đầu (không có depot ở cuối)
            max_iterations: Số lần lặp tối đa
        
        Returns:
            improved_route: Lộ trình đã cải thiện
            total_distance: Tổng khoảng cách mới
        """
        improved = True
        iterations = 0
        best_route = route.copy()
        best_distance = self._route_distance(best_route)
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            for i in range(1, len(best_route) - 2):
                for j in range(i + 1, len(best_route)):
                    if j - i == 1:
                        continue
                    
                    # Tính delta: thay đổi khoảng cách nếu đảo đoạn [i, j]
                    new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                    new_distance = self._route_distance(new_route)
                    
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
                        break
                
                if improved:
                    break
        
        return best_route, best_distance
    
    def _route_distance(self, route: List[int]) -> float:
        """Tính tổng khoảng cách của lộ trình"""
        return sum(self.dist[route[i]][route[i+1]] 
                   for i in range(len(route) - 1))
    
    def improve_routes(self, routes: List[List[int]], 
                       depot_idx: int) -> List[List[int]]:
        """Cải thiện tất cả các lộ trình trong VRP"""
        improved_routes = []
        
        for route in routes:
            # Loại bỏ depot, chỉ giữ các điểm giao
            points = [p for p in route if p != depot_idx]
            
            if len(points) > 2:
                improved_points, _ = self.improve(points)
                improved_route = [depot_idx] + improved_points + [depot_idx]
            else:
                improved_route = route
            
            improved_routes.append(improved_route)
        
        return improved_routes
```

---

## 3. SO SÁNH 3 THUẬT TOÁN

### Bảng tổng hợp

| Thuật toán | Loại | Time | Space | Chất lượng | Áp dụng |
|------------|------|------|-------|------------|---------|
| **Dijkstra** | Exact | O(n² log n) | O(n²) | ✅ Optimal | Tính khoảng cách |
| **Nearest Neighbor** | Heuristic | O(n²) | O(n) | ~75-85% | TSP nhanh |
| **Clarke-Wright + 2-Opt** | Hybrid | O(n² log n) | O(n²) | ~90-95% | VRP thực tế |

### Benchmark Expected Results

```
Dataset: 30 điểm Hà Nội

┌────────────────────────────────────────────────────────────┐
│ ALGORITHM              │ TOTAL KM │ TIME   │ vs OPTIMAL   │
├────────────────────────────────────────────────────────────┤
│ Nearest Neighbor       │  85.2 km │ 0.01s  │  78%         │
│ Clarke-Wright (alone)  │  72.1 km │ 0.03s  │  88%         │
│ Clarke-Wright + 2-Opt  │  68.5 km │ 0.15s  │  92%         │
│ Brute Force (optimal)  │  63.0 km │ >1hour │  100%        │
└────────────────────────────────────────────────────────────┘
```

---

## 4. CẤU TRÚC PROJECT

```
shipper_optimizer/
├── src/
│   ├── __init__.py
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── dijkstra.py          # Algorithm 1
│   │   ├── nearest_neighbor.py   # Algorithm 2
│   │   ├── clarke_wright.py      # Algorithm 3a
│   │   ├── two_opt.py            # Algorithm 3b
│   │   └── benchmark.py          # So sánh thuật toán
│   ├── models/
│   │   ├── __init__.py
│   │   ├── location.py           # Location, Delivery, Depot
│   │   └── route.py              # Route data model
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── map_viz.py            # Folium map generator
│   ├── data/
│   │   ├── hanoi_deliveries.csv  # Dataset 30 điểm
│   │   └── loader.py             # Data loader
│   └── main.py                   # CLI interface
├── data/
│   ├── hanoi_deliveries.csv
│   └── sample_results/
├── tests/
│   └── test_algorithms.py
├── requirements.txt
├── README.md
└── KE_HOACH_CHI_TIET.md          # File này
```

---

## 5. DATASET: HÀ NỘI 30 ĐIỂM

### Format CSV
```csv
id,name,lat,lng,demand_kg
D0,Kho V9 Hoàng Mai,20.9821,105.7913,0
D1,123 Cầu Giấy,21.0382,105.7797,5.2
D2,45 Hoàng Quốc Việt,21.0471,105.7876,3.1
D3,78 Láng Hạ,21.0324,105.8101,7.5
D4,56 Trần Duy Hưng,21.0056,105.7856,4.3
...
```

### 30 Điểm giao (Quận Cầu Giấy, Thanh Xuân, Đống Đa, Hoàn Kiếm)

| STT | Tên | Quận | Lat | Lng |
|-----|-----|------|-----|-----|
| D0 | Kho V9 Hoàng Mai | Hoàng Mai | 20.9821 | 105.7913 |
| D1 | Văn Quán | Thanh Xuân | 21.0012 | 105.7823 |
| D2 | Ngã Tư Sở | Đống Đa | 21.0056 | 105.7856 |
| D3 | Cầu Giấy | Cầu Giấy | 21.0285 | 105.7891 |
| D4 | Trung Hoà | Cầu Giấy | 21.0228 | 105.7956 |
| D5 | Dịch Vọng | Cầu Giấy | 21.0382 | 105.7797 |
| D6 | Trung Kính | Cầu Giấy | 21.0345 | 105.7921 |
| D7 | Yên Hoà | Cầu Giấy | 21.0412 | 105.7856 |
| D8 | Quan Hoa | Cầu Giấy | 21.0289 | 105.7982 |
| D9 | Hoàng Đạo Thúy | Thanh Xuân | 21.0123 | 105.7845 |
| D10 | Khương Trung | Thanh Xuân | 21.0089 | 105.7756 |
| D11 | Thanh Xuân Bắc | Thanh Xuân | 21.0156 | 105.7823 |
| D12 | Phương Liệt | Thanh Xuân | 21.0023 | 105.7721 |
| D13 | Hạ Đình | Thanh Xuân | 21.0067 | 105.7656 |
| D14 | Kim Giang | Thanh Xuân | 20.9989 | 105.7691 |
| D15 | Chùa Bộc | Đống Đa | 21.0123 | 105.8201 |
| D16 | Thái Hà | Đống Đa | 21.0189 | 105.8156 |
| D17 | Tôn Đức Thắng | Đống Đa | 21.0223 | 105.8234 |
| D18 | Láng Hạ | Đống Đa | 21.0324 | 105.8101 |
| D19 | Thái Thịnh | Đống Đa | 21.0256 | 105.8189 |
| D20 | Nguyễn Lương Bằng | Đống Đa | 21.0289 | 105.8234 |
| D21 | Láng Trung | Đống Đa | 21.0189 | 105.8012 |
| D22 | Khâm Thiên | Đống Đa | 21.0123 | 105.8089 |
| D23 | Trung Phụng | Đống Đa | 21.0156 | 105.8123 |
| D24 | Ô Chợ Dừa | Đống Đa | 21.0223 | 105.8167 |
| D25 | Hàng Bột | Đống Đa | 21.0256 | 105.8234 |
| D26 | Lò Đúc | Hai Bà Trưng | 21.0123 | 105.8456 |
| D27 | Trần Khát Chân | Hai Bà Trưng | 21.0089,105.8512 | |
| D28 | Bạch Đằng | Hai Bà Trưng | 21.0156 | 105.8578 |
| D29 | Minh Khai | Hai Bà Trưng | 21.0223 | 105.8656 |
| D30 | Vĩnh Tuy | Hai Bà Trưng | 21.0089 | 105.8712 |

---

## 6. OUTPUT MẪU

### 6.1 Kết quả chạy thuật toán

```
╔══════════════════════════════════════════════════════════════════╗
║           🚚 SHIPPER ROUTE OPTIMIZER - RESULTS                  ║
╚══════════════════════════════════════════════════════════════════╝

📦 Dataset: 30 điểm giao hàng tại Hà Nội
🏭 Depot: Kho V9 Hoàng Mai (20.9821, 105.7913)
🚗 Vehicle: 1 xe tải, sức chứa 500kg

──────────────────────────────────────────────────────────────────────

🛣️ ALGORITHM 1: DIJKSTRA - Khoảng cách ngắn nhất
   ✓ Ma trận khoảng cách: 31 x 31
   ✓ Khoảng cách trung bình: 8.5 km
   ✓ Khoảng cách xa nhất: 23.7 km (D0 ↔ D30)

──────────────────────────────────────────────────────────────────────

🛣️ ALGORITHM 2: NEAREST NEIGHBOR - TSP Heuristic
   Route: D0 → D1 → D2 → D3 → D4 → D5 → D6 → D7 → D8 → D9 → D10 
          → D11 → D12 → D13 → D14 → D15 → D16 → D17 → D18 → D19 
          → D20 → D21 → D22 → D23 → D24 → D25 → D26 → D27 → D28 
          → D29 → D30 → D0
   Total Distance: 85.2 km
   Estimated Time: 2h 45m (30 phút giao hàng + di chuyển)

──────────────────────────────────────────────────────────────────────

🛣️ ALGORITHM 3: CLARKE-WRIGHT SAVINGS + 2-OPT (OPTIMAL)
   ✓ Lộ trình tối ưu:
   
   ROUTE 1:
   D0 → D1 → D10 → D11 → D9 → D12 → D13 → D14 → D0
   Distance: 28.5 km | Deliveries: 9 | Demand: 125 kg

   ROUTE 2:
   D0 → D2 → D3 → D4 → D5 → D6 → D7 → D8 → D0
   Distance: 25.3 km | Deliveries: 8 | Demand: 98 kg

   ROUTE 3:
   D0 → D15 → D16 → D17 → D18 → D19 → D20 → D21 → D22 → D23 → D0
   Distance: 18.7 km | Deliveries: 13 | Demand: 145 kg

──────────────────────────────────────────────────────────────────────

📊 SUMMARY:
┌────────────────────┬───────────┬────────────┬──────────────┐
│ Algorithm          │ Total KM  │ Time (s)   │ vs Optimal   │
├────────────────────┼───────────┼────────────┼──────────────┤
│ Nearest Neighbor   │  85.2 km  │  0.01s     │    78.3%     │
│ Clarke-Wright      │  72.1 km  │  0.03s     │    88.2%     │
│ Clarke-Wright+2Opt │  68.5 km  │  0.15s     │    92.1%     │
└────────────────────┴───────────┴────────────┴──────────────┘

💰 COST SAVINGS (vs Nearest Neighbor):
   Distance saved: 16.7 km (19.6%)
   Fuel saved: ~18,000 VND/trip
   Annual savings: ~6.5M VND (365 trips/year)

──────────────────────────────────────────────────────────────────────

🗺️ MAP: Duolưu vào output/hanoi_routes.html
```

### 6.2 Benchmark Chart

```
Benchmark: 30 điểm Hà Nội
─────────────────────────────────────────
Nearest Neighbor:     ████████████████░░░░░░░░░░  85.2 km
Clarke-Wright:       ██████████████░░░░░░░░░░░░  72.1 km  
Clarke-Wright+2Opt:  █████████████░░░░░░░░░░░░░  68.5 km
─────────────────────────────────────────
Best Possible (est):  ████████████░░░░░░░░░░░░░  63.0 km
```

---

## 7. TRỰC QUAN HÓA

### 7.1 Folium Map Output

```python
# Tạo bản đồ interactive
m = folium.Map(location=[21.0285, 105.7891], zoom_start=12)

# Thêm depot (màu xanh)
folium.Marker(
    [20.9821, 105.7913],
    popup="Kho V9 Hoàng Mai",
    icon=folium.Icon(color='green', icon='home')
).add_to(m)

# Thêm các điểm giao (màu đỏ)
for delivery in deliveries:
    folium.Marker(
        [delivery.lat, delivery.lng],
        popup=f"{delivery.id}: {delivery.name}",
        icon=folium.Icon(color='red')
    ).add_to(m)

# Vẽ lộ trình tối ưu
folium.PolyLine(
    locations=[[d.lat, d.lng] for d in optimized_route],
    color='blue',
    weight=3,
    opacity=0.8
).add_to(m)

# Lưu
m.save('output/hanoi_routes.html')
```

### 7.3 Visualization mẫu

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    🗺️ HÀ NỘI                               │
│                                                             │
│         ●D15                                                  │
│        ╱   ╲      ●D18    ●D19                             │
│   ●D13 ●D12  ╲  ╱    ╲   ╱                                 │
│        ╲      ●D11 ●D10 ╱                                   │
│   ●D14 ●──────●D9    ╱                                     │
│        ╲   ●D8  ╱   ╱                                      │
│         ●D7    ╲ ╱                                        │
│        ╱│╲      ●D3                                       │
│   ●D5  ●D6      │   ●D4                                    │
│        │        │   │                                      │
│        ●──────────────●                                    │
│        D0 (Kho)                                             │
│                                                             │
│  🟢 Depot   🔴 Delivery   🔵 Route                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. GIAO DIỆN CLI

### 8.1 Menu chính

```
╔══════════════════════════════════════════════════════════════════╗
║              🚚 SHIPPER ROUTE OPTIMIZER                          ║
║              Tối ưu lộ trình giao hàng Hà Nội                   ║
╚══════════════════════════════════════════════════════════════════╝

Chọn chức năng:
  [1] Chạy tất cả thuật toán + Benchmark
  [2] Chạy Dijkstra (ma trận khoảng cách)
  [3] Chạy Nearest Neighbor (TSP)
  [4] Chạy Clarke-Wright + 2-Opt (VRP tối ưu)
  [5] Xem kết quả trên bản đồ
  [6] Xuất báo cáo
  [0] Thoát

Nhập lựa chọn: _
```

### 8.2 Chạy benchmark

```
$ python main.py --benchmark --dataset hanoi_deliveries.csv

Running benchmark on: 30 điểm Hà Nội
Loading data: hanoi_deliveries.csv ✓
Building graph: 31 nodes, 465 edges ✓

[1/3] Dijkstra: Computing shortest paths... Done (0.01s)
[2/3] Nearest Neighbor: Building TSP route... Done (0.01s)
[3/3] Clarke-Wright + 2-Opt: Optimizing VRP... Done (0.15s)

Results saved to: output/benchmark_results.json
Map saved to: output/hanoi_routes.html
```

---

## 9. BÁO CÁO KỸ THUẬT

### Nội dung báo cáo

```
1. Giới thiệu
   1.1 Bài toán VRP trong thực tế
   1.2 Mục tiêu đồ án

2. Cơ sở lý thuyết
   2.1 Bài toán đường đi ngắn nhất (Dijkstra)
   2.2 Bài toán người du lịch (TSP)
   2.3 Bài toán giao hàng (VRP)

3. Thuật toán đề xuất
   3.1 Clarke-Wright Savings Algorithm
   3.2 2-Opt Local Search
   3.3 Phân tích độ phức tạp

4. Cài đặt
   4.1 Cấu trúc dữ liệu
   4.2 Code chính
   4.3 Dataset

5. Kết quả thực nghiệm
   5.1 Benchmark trên dataset Hà Nội
   5.2 So sánh 3 thuật toán
   5.3 Phân tích kết quả

6. Kết luận và hướng phát triển
```

---

## 10. CHECKLIST TRIỂN KHAI

- [ ] Tạo cấu trúc folder
- [ ] Cài đặt requirements.txt
- [ ] Cài đặt models (Location, Delivery, Depot)
- [ ] Tạo dataset hanoi_deliveries.csv
- [ ] Cài đặt Dijkstra
- [ ] Cài đặt Nearest Neighbor
- [ ] Cài đặt Clarke-Wright Savings
- [ ] Cài đặt 2-Opt
- [ ] Cài đặt benchmark
- [ ] Cài đặt Folium visualization
- [ ] Cài đặt CLI interface
- [ ] Viết báo cáo kỹ thuật
- [ ] Test toàn bộ hệ thống

---

## 11. THỜI GIAN ƯỚC TÍNH

| Giai đoạn | Thời gian | Công việc |
|-----------|-----------|-----------|
| Phase 1 | 2-3 giờ | Setup + Models + Dataset |
| Phase 2 | 3-4 giờ | Dijkstra + Nearest Neighbor |
| Phase 3 | 4-5 giờ | Clarke-Wright + 2-Opt |
| Phase 4 | 2-3 giờ | Visualization + CLI |
| Phase 5 | 3-4 giờ | Benchmark + Báo cáo |
| **Tổng** | **14-19 giờ** | **Hoàn thành đồ án** |

---

## 12. CÁC BƯỚC TIẾP THEO

1. ✅ Xác nhận kế hoạch
2. ⬜ Tạo cấu trúc folder
3. ⬜ Code từng thuật toán
4. ⬜ Test và benchmark
5. ⬜ Hoàn thiện báo cáo

---

**Lưu ý**: File này là kế hoạch chi tiết. Code sẽ được viết theo cấu trúc trên.
