# Instance JSON v1

CLI nhận một file JSON UTF-8. Ví dụ nhỏ có thể nhập thẳng vào demo:

Với adapter Kris, số đo được giữ trong đơn vị gốc và khai báo `metadata.units.distance="source_distance_unit"`, `metadata.units.time="source_time_unit"`. Demo đọc khai báo này để đổi nhãn. Các trường thao tác có hậu tố `minutes` giữ tên API lịch sử, nhưng giá trị phải cùng đơn vị thời gian với due dates; không tự coi giá trị nguồn là phút. File do generator của project sinh vẫn dùng mét/phút.

```json
{
  "schema_version": 1,
  "name": "one-order",
  "directed": false,
  "depot": "D",
  "nodes": [
    {"id": "D", "x": 0, "y": 0},
    {"id": "A", "x": 10, "y": 0}
  ],
  "edges": [{"source": "D", "target": "A", "distance": 10}],
  "products": [{"id": "X", "location": "A", "size": 1, "pick_minutes": 0.5}],
  "orders": [{"id": "O1", "items": {"X": 2}, "due": 4, "rank": 0}],
  "operations": {
    "pickers": 2,
    "capacity": 3,
    "speed": 10,
    "location_minutes": 1,
    "batch_minutes": 1
  },
  "metadata": {"source": "hand-calculated", "units": {"distance": "metre", "time": "minute", "capacity": "item"}}
}
```

Nghiệm một batch: đi 20 m, xử lý 1 + 20/10 + 1 + 2×0,5 = 5 phút, trễ 1 phút. Picker thứ hai không có việc.

## Quy tắc dữ liệu

- ID node/product/order là chuỗi không rỗng, duy nhất trong từng nhóm.
- Cạnh khai báo một lần cho hai chiều. Không khai báo thêm cạnh đảo, self-loop hoặc cạnh trùng.
- x/y phục vụ vẽ; routing dùng `distance` trên cạnh. Khoảng cách có thể bằng 0, không được âm/NaN/Infinity.
- Toàn bộ graph phải liên thông; depot và vị trí SKU phải tồn tại.
- `items` là ánh xạ SKU sang số lượng nguyên dương. Gộp các dòng trùng SKU trước khi nhập.
- `size` dương, cùng đơn vị với capacity; không suy capacity từ số điểm lấy hàng.
- `due` không âm, tính từ t=0. `rank` nguyên không âm; hòa rank được phá theo ID.
- `pickers` nguyên dương; capacity và speed dương; các thời gian thao tác không âm.
- Một đơn vượt capacity bị từ chối; chưa hỗ trợ split.
- Trường top-level không biết bị từ chối để phát hiện gõ sai; không tự hiểu schema Foodmart/Zalando.
- Nếu có `metadata.units` hoặc `metadata.layout`, giá trị phải là object. Nhãn đơn vị phải là chuỗi không rỗng. Đơn vị tùy chỉnh được giữ nguyên trên demo, không tự đổi sang mét/phút; người cung cấp dữ liệu phải đảm bảo speed, due và thời gian thao tác nhất quán.
- `layout.type="single_block"` yêu cầu `aisles` không rỗng; mỗi aisle là danh sách ít nhất hai ID node tồn tại. S-Shape còn kiểm tra topology đầy đủ khi chạy. Metadata vẽ không thay đổi khoảng cách trên cạnh.

## Metadata kho một block cho S-Shape

`metadata.layout` cần `type="single_block"` và `aisles` là danh sách các danh sách node từ đầu trước đến đầu sau, theo thứ tự aisle trái sang phải. Mọi node phải thuộc đúng một aisle; depot là node đầu aisle đầu. Graph phải có đúng các cạnh dọc nối node kế tiếp và cạnh ngang nối hai đầu aisle kế tiếp, không có cross-aisle trung gian.

Chính sách S-Shape: các aisle cần lấy được đi theo thứ tự khai báo, lần lượt từ trước ra sau rồi từ sau ra trước. Nếu số aisle có hàng là lẻ, aisle cuối đi vào đến điểm cần lấy xa nhất rồi quay về cùng đầu trước. Cuối cùng quay về depot. Quy tắc này chỉ là baseline xác định trên topology đã giới hạn.

## Kết quả JSON

`plan[picker][position]` chứa các order ID của batch. `batches` xuất route stops, physical walk, tải, khoảng cách, start/end/duration và tổng độ trễ batch. `orders` có batch/picker/due/completion/tardiness riêng từng đơn.

`objective_config` lưu trọng số và mẫu số; `metrics` lưu số đo không làm tròn để có thể kiểm tra lại. `timing` tách tiền xử lý/reference B0, tối ưu và tổng. `search` chứa seed, cấu hình, thống kê operator và lịch sử best khi áp dụng. `feasible` chỉ được gán true sau validator.

Validator dựng lại tổng quãng đường từ từng cạnh của physical walk, tải từ quantity, thời lượng, lịch nối tiếp và độ trễ từng đơn. Nó kiểm tra công thức F với mẫu số đã lưu; việc chọn đúng baseline để tạo các mẫu số do solver thực hiện thống nhất.
