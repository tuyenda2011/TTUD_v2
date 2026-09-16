# Đánh giá tổng quan và khả năng đạt điểm cao

**Dự án:** Warehouse Joint Optimizer — tối ưu gom đơn, tuyến lấy hàng và lịch nhiều nhân viên trong kho.  
**Ngày đánh giá:** 16/09/2026.  
**Cơ sở:** mã nguồn, test thực chạy bằng Conda `TTUD`, demo, cấu hình và kết quả thực nghiệm đang có. Người dùng chưa có rubric hoặc hạn nộp cụ thể; đây là đánh giá kỹ thuật có điều kiện, không phải dự đoán điểm của giảng viên.

## 1. Kết luận thẳng

**Có, đề tài phù hợp và khả thi để hướng tới điểm cao trong một đồ án thuật toán ứng dụng/tối ưu tổ hợp.** Dự án đã vượt mức “chạy một thuật toán rồi vẽ hình”: có mô hình kết hợp nhiều quyết định, baseline, hai hướng tìm kiếm, kiểm chứng nghiệm độc lập, oracle cho bài toán nhỏ, dữ liệu benchmark và ứng dụng chạy được.

**Tuy nhiên, chưa nên coi là đã chắc chắn đạt mức xuất sắc.** Những thiếu hụt chính hiện nay là bằng chứng thực nghiệm đủ rộng, báo cáo học thuật thống nhất với code, phân tích vì sao phương pháp tốt/xấu và khả năng tự giải thích khi bảo vệ. Giao diện đẹp hơn giúp trình bày, nhưng không thay thế các phần này.

Nếu môn học thiên về **ứng dụng thuật toán**, nền tảng hiện tại khá tốt. Nếu môn học đòi hỏi **đóng góp thuật toán mới hoặc nghiên cứu có tính công bố**, mức hiện tại chưa đủ: dự án chủ yếu cài đặt, tích hợp và đánh giá các phương pháp đã biết. Không có rubric nên không gán điểm số giả định hoặc khẳng định một mức điểm chắc chắn.

## 2. Dự án thực sự giải quyết điều gì?

Một đơn có nhiều SKU và số lượng. Hệ thống quyết định đơn nào đi chung một chuyến, nhân viên nào nhận chuyến, tuyến qua các vị trí lấy hàng và thứ tự chuyến trên từng nhân viên. Mỗi thay đổi gom đơn có thể làm thay đổi tuyến, thời gian hoàn thành và độ trễ của các chuyến sau.

Phạm vi đã triển khai:

- Một depot, đồ thị kho hai chiều, nhân viên đồng nhất; tất cả đơn có từ thời điểm bắt đầu.
- Không chia một đơn sang nhiều chuyến; tổng tải mỗi chuyến không vượt sức chứa.
- Một SKU có một vị trí; giả định đủ tồn kho.
- Đơn hoàn thành khi chuyến quay lại depot và kết thúc thao tác bàn giao.
- Hạn mềm: trễ bị phạt nhưng vẫn có thể là nghiệm khả thi.
- Không mô phỏng tắc nghẽn, tránh va chạm, ca làm việc, đơn mới đến hoặc công suất bàn giao dùng chung.

Hàm mục tiêu hiện dùng:

\[
F=w_D\frac{D}{D_{ref}}+w_C\frac{C_{max}}{C_{ref}}+w_T\frac{\sum_i\max(0,C_i-d_i)}{T_{ref}}.
\]

Trong đó `Dref=max(D_B0,1)`, `Cref=max(Cmax_B0,1)`, `Tref=n*Cref`; trọng số mặc định bằng nhau và mọi phương pháp trên cùng instance dùng cùng chuẩn B0. Các mẫu số là lựa chọn thiết kế cần giải thích, không phải một chuẩn bắt buộc cho mọi kho.

**Không gọi đây là phần mềm điều hành kho sản xuất hoàn chỉnh hoặc bài toán giao hàng ngoài đường.** Các file kế hoạch VRP/giao hàng cũ ở thư mục cha khác phạm vi đề tài kho hiện tại; không đưa nguyên chúng vào hồ sơ nộp như đặc tả hiện hành.

## 3. Những phần đã có bằng chứng

| Nội dung | Hiện trạng và bằng chứng | Ý nghĩa đối với đồ án |
|---|---|---|
| Mô hình và đầu vào | `models.py`, `docs/SCHEMA.md`; kiểm tra tải, SKU, đồ thị, số lượng, thời hạn và metadata dùng cho hiển thị | Có điều kiện khả thi rõ, không chỉ sinh dữ liệu rồi chạy |
| Đồ thị và tuyến | Dijkstra trên lối đi thật; NN, 2-Opt, S-Shape với điều kiện topology | Giải thích được đường đi và khoảng cách, không đi xuyên kệ |
| Baseline | B0/B1/B2/B3 với vai trò từng bước khác nhau | Có mốc đối chiếu thay vì chỉ báo một nghiệm “tốt” |
| Tìm kiếm | LNS, ALNS và VNS; seed, ngân sách, best khả thi, trace | Có nội dung thuật toán đủ chiều sâu để trình bày |
| Đánh giá nghiệm | Evaluator và validator độc lập về cách tính lại tuyến/lịch từ kết quả xuất | Tăng độ tin cậy; không chỉ tự báo `feasible=true` |
| Bài toán nhỏ | `exact.py` duyệt phân hoạch/phân công/thứ tự/tuyến trong giới hạn nhỏ | Có oracle đối chiếu; chỉ chứng nhận khi duyệt hết |
| Kiểm thử | Sau lượt sửa tiếp: **102 test đạt** trên TTUD; gồm core, CLI, state, metadata và AppTest | Bằng chứng thực thi, không phải cam kết không còn lỗi |
| Demo | Mẫu mặc định 10 đơn, cấu hình theo nguồn, ba KPI, tuyến/lịch, xuất JSON và snapshot | Có thể trình diễn trọn luồng mà không cần giải thích toàn bộ thuật toán trước |
| Dữ liệu và tái lập | Kris đã chuyển đổi, dữ liệu tổng hợp có seed, config/manifest/hash | Phân biệt được nguồn dữ liệu và cấu hình thí nghiệm |

Số lượng test không tương đương số lượng yêu cầu độc lập và cũng không phải điểm số học thuật. Giá trị nằm ở việc test bắt được tính sai, lỗi dữ liệu và các trường hợp biên có ý nghĩa.

## 4. Điểm mạnh đáng đưa vào báo cáo/bảo vệ

1. **Sự liên kết giữa các quyết định.** Trình bày một ví dụ đổi thành phần chuyến làm thay đổi tuyến và kéo theo độ trễ phía sau; đây là phần thể hiện bản chất tối ưu đồng thời.
2. **Đối chiếu có kiểm soát.** B0 → B2 → B3 → search giúp giải thích lợi ích đến từ tuyến, lịch hay thay đổi gom đơn.
3. **Kiểm chứng độc lập.** Có thể xuất JSON, sửa một giá trị rồi cho validator phát hiện sai; thuyết phục hơn chỉ mở biểu đồ đẹp.
4. **Oracle nhỏ.** Cho thấy heuristic không được tuyên bố tốt hơn tối ưu đã chứng nhận khi cùng mô hình và objective.
5. **Minh bạch giới hạn.** Dữ liệu Kris giữ đơn vị nguồn; mục tiêu hạn mềm khác bài toán hạn cứng của nguồn. Dự án không giả vờ đã tái lập best-known gốc.

Đóng góp phù hợp để nhận là: **thiết kế và hiện thực một hệ thống tối ưu kết hợp, có kiểm chứng và đánh giá thực nghiệm trên mô hình đã xác định**. Không nhận ALNS, VNS, Dijkstra hay 2-Opt là thuật toán do nhóm sáng tạo.

## 5. Phần còn yếu có thể làm mất điểm

| Vấn đề | Vì sao quan trọng | Hành động cần làm |
|---|---|---|
| Đánh giá mới còn ít instance | 96 lần chạy không phải 96 bài toán độc lập; nhiều lần chỉ đổi seed trên cùng dữ liệu | Mở rộng số instance mỗi nhóm; tổng hợp trước theo instance, rồi mới kết luận chung |
| Chưa có phân tích đóng góp đủ rõ | Thắng B0 chưa cho biết thành phần nào tạo lợi ích | So với B2/B3; ablation phải mô tả đúng phần đã tắt và phần vẫn hoạt động |
| Chuẩn hóa và trọng số cần biện luận | F giảm có thể đi kèm tăng đơn trễ hoặc quãng đường | Báo từng chỉ số gốc, giải thích trade-off; kiểm tra vài cấu hình trọng số |
| Chưa có tuning/test tách biệt rõ cho kết luận cuối | Chọn cấu hình nhìn từ tập báo cáo có thể làm kết quả thiên lệch | Chốt tập tuning, giữ tập test riêng; ghi lịch sử chọn tham số |
| Báo cáo và tài liệu cũ có thể mâu thuẫn | Có tài liệu giao hàng VRP và kế hoạch thêm VNS dù VNS đã có | Nộp một bộ tài liệu warehouse thống nhất; tài liệu cũ ghi lịch sử hoặc loại khỏi gói nộp |
| Chưa có đánh giá người dùng thật | Chạy được trên browser không chứng minh người mới hiểu nhanh | Thực hiện mục thử 3 người mới; ghi thời gian và lỗi hiểu nhầm |
| Raw benchmark chưa nằm trong Git | Một bảng tổng hợp khó được kiểm toán lại nếu thiếu dữ liệu từng run | Đính kèm archive kết quả đầy đủ và checksum trong gói nộp, không cần đưa hàng nghìn file vào Git |
| Độ mới nghiên cứu còn hạn chế | Tích hợp phương pháp có sẵn không tự trở thành thuật toán mới | Trình bày đóng góp thực tế; chỉ nhận cải tiến mới khi có mô tả và ablation chứng minh |

Ngoài ra, route decoder hiện quyết định tuyến bằng NN/2-Opt theo thành phần batch; search không duy trì một không gian các tuyến thay thế hoàn toàn độc lập. VNS là tìm kiếm với descent lấy mẫu có giới hạn, không phải chứng minh đã đạt tối ưu cục bộ đầy đủ. Hai điểm này nên được viết đúng trong báo cáo.

## 6. Số liệu hiện có nói được gì?

Đợt benchmark demo trước lượt siết metadata có **96/96 nghiệm hợp lệ**, trên 6 instance: synthetic 10/30/100 đơn và một Kris mỗi nhóm 6/12/18 đơn. Search chạy seed 7/42/101 với ngân sách 1/3 giây. Kết quả này đủ kiểm tra hoạt động và tạo mốc ban đầu, chưa đủ cho một kết luận tổng quát về ưu thế thuật toán.

Ví dụ synthetic 100 đơn, ngân sách 3 giây, F trung vị:

| Phương pháp | F |
|---|---:|
| B0 | 0,70026 |
| B2 | 0,54038 |
| ALNS | 0,53501 |
| VNS | 0,51564 |

Trong mẫu này VNS tốt nhất trong bốn phương pháp; ALNS cải thiện ít hơn so với B2. **Không nên chỉ chọn mẫu nơi ALNS thắng hoặc tuyên bố ALNS luôn tốt hơn.** Một báo cáo giải thích được trường hợp không cải thiện thường có giá trị hơn lời quảng cáo thiếu đối chứng.

Thời gian mỗi lần giải trong đợt đo khoảng 0,003–3,009 giây; khởi tạo lớn nhất khoảng 0,109 giây. Chạy tuần tự trên máy đang phát triển, không cô lập tải hệ thống; chưa đo RAM và chưa chứng minh giới hạn quy mô lớn. Không so điểm F giữa hai instance khác nhau như cùng một thang chi phí tuyệt đối.

Nguồn: [báo cáo benchmark](results/demo_upgrade_benchmark/REPORT.md) và [summary](results/demo_upgrade_benchmark/summary.json). Manifest chi tiết chỉ lưu local vì có thể chứa đường dẫn máy và trạng thái working tree. Hash/revision chỉ phản ánh thời điểm đo; bản sửa metadata sau đó không được ngầm coi là đã chạy lại toàn bộ benchmark.

## 7. Ưu tiên để tăng khả năng đạt điểm cao

### Bắt buộc trước khi nộp

1. **Chốt bản mô hình và báo cáo khớp code.** Có biến/quyết định, ràng buộc, thời gian xử lý, objective, giả định và một ví dụ tính tay. Phân biệt FCFS gom đơn với EDD xếp lịch của B0.
2. **Hoàn thành thực nghiệm có đối chứng.** Nhiều instance mỗi nhóm, seed công bố, cùng ngân sách và chuẩn hóa. Báo F, distance, makespan, tổng độ trễ, đơn trễ và thời gian; giải thích cả ca tốt lẫn ca yếu. Giữ nguyên due dates khi nghiên cứu ảnh hưởng số nhân viên.
3. **Đóng gói bản nộp tái lập được.** Review rồi commit đúng code/config/tài liệu; ghi phiên bản TTUD; kèm hướng dẫn chạy và archive raw benchmark. Test “bản sao sạch” hiện tại không có nghĩa thay đổi đã được push lên remote.
4. **Diễn tập bảo vệ.** Người làm phải tự giải thích được một phép destroy/repair, một swap lịch, vì sao phải tính lại hậu tố và vì sao có thể còn đơn trễ.

### Nên làm sau bốn việc trên

- Tách tuning/test và bổ sung ablation hoặc độ nhạy trọng số; báo thắng/hòa/thua theo instance.
- Đối chiếu gap với exact trên vài bài toán nhỏ đã được chứng nhận; không dùng nghiệm exact hết giờ làm “tối ưu thật”.
- Hoàn thành thử 3 người mới và sửa các bước gây hiểu nhầm.
- Đo thêm RAM/thời gian ở quy mô lớn hơn nếu phạm vi báo cáo yêu cầu khả năng mở rộng.

Không ưu tiên thêm GA/ACO, đổi framework giao diện hoặc thêm nhiều depot chỉ để tăng danh sách tính năng. Phạm vi rộng hơn nhưng kiểm chứng yếu dễ làm bài bảo vệ kém chắc hơn.

## 8. Các câu hỏi cần tự trả lời được khi bảo vệ

| Câu hỏi | Hướng trả lời phải gắn với code |
|---|---|
| Vì sao gọi là tối ưu kết hợp? | Đổi batch/assignment/thứ tự làm thay đổi toàn objective; tuyến được giải mã lại theo batch |
| Vì sao đơn cùng chuyến hoàn thành cùng lúc? | Giả định hoàn thành tại depot sau bàn giao; không dùng thời điểm ghé SKU |
| Dijkstra và NN khác nhau ở đâu? | Dijkstra tìm đường ngắn trên đồ thị; NN chọn thứ tự ghé các vị trí bằng khoảng cách đó |
| 2-Opt có bảo đảm tối ưu không? | Không; cải thiện tuyến cục bộ trên metric đối xứng, khác exact routing |
| ALNS khác LNS thế nào? | Điều chỉnh trọng số operator theo thành tích; không phải cứ adaptive là luôn thắng |
| Vì sao không tối thiểu quãng đường thôi? | Gom nhiều đơn có thể kéo dài hoàn thành và gây trễ; mục tiêu cần phản ánh trade-off |
| Nghiệm hợp lệ mà vẫn trễ có mâu thuẫn không? | Không: hạn mềm là thành phần phạt, không phải ràng buộc cứng |
| Làm sao biết evaluator không tính sai? | Tính tay, full/cached consistency, validator độc lập và oracle nhỏ |
| Có thực sự dùng dữ liệu thực tế không? | Có benchmark nguồn tác giả; không đồng nghĩa log vận hành thật; có adapter và giới hạn chuyển đổi |
| Đóng góp mới của nhóm là gì? | Mô hình áp dụng, tích hợp, hiện thực, kiểm chứng và phân tích; không nhận các thuật toán kinh điển là mới |

## 9. Những sửa chữa hoàn tất trong lượt này

- Tái hiện 10 ca lỗi: metadata units/layout không hợp lệ, nhãn đơn vị tùy chỉnh bị đổi thành mét/phút và snapshot sai cấu trúc.
- Chặn metadata lỗi trước khi giải/vẽ; dùng đúng nhãn đơn vị đã khai báo, không tự quy đổi giá trị.
- Trục sơ đồ dùng “tọa độ x/y”: tọa độ phục vụ vẽ, khoảng cách thuật toán vẫn theo cạnh của đồ thị.
- Thêm bảng thứ tự điểm lấy cho từng chuyến; sửa nhãn bảng tiếng Việt; giữ tương thích snapshot cũ không lưu seed.
- Bộ kiểm thử sau sửa: **102 test đạt trên TTUD**. Báo cáo nghiệm thu chi tiết và lịch sử ở [docs/DEMO_UPGRADE_VALIDATION.md](docs/DEMO_UPGRADE_VALIDATION.md).

## 10. Đánh giá cuối cùng

**Nên tiếp tục đề tài này; không cần đổi đề tài để tìm cơ hội điểm cao.** Phần triển khai đã đủ làm nền cho một đồ án tốt. Phần cần đầu tư tiếp là biến “code chạy được” thành một lập luận có bằng chứng: mô hình nhất quán, so sánh công bằng, thừa nhận giới hạn, tái lập được và người làm giải thích được quyết định của mình.

Khả năng đạt điểm cao sẽ giảm nếu chỉ demo đẹp, liệt kê nhiều thuật toán, gọi benchmark là dữ liệu vận hành thật hoặc kết luận từ một vài seed thuận lợi. Ngược lại, một phạm vi vừa phải nhưng được kiểm chứng và phân tích chặt chẽ phù hợp hơn để bảo vệ một kết quả tốt.
