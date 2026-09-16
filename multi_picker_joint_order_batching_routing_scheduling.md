# ĐỀ TÀI: MULTI-PICKER JOINT ORDER BATCHING, ROUTING AND SCHEDULING WITH DUE DATES

> Bản rà soát ngày 12/09/2026. Đây là đặc tả đề xuất để triển khai; chưa phải báo cáo kết quả thực nghiệm.

## 1. Tên đề tài và định hướng

**Tiếng Việt:** Tối ưu đồng thời gom đơn hàng, phân công nhân viên, định tuyến lấy hàng và lập lịch có xét hạn hoàn thành đơn trong kho.

**Tiếng Anh:** Multi-Picker Joint Order Batching, Routing and Scheduling with Due Dates.

**Câu hỏi nghiên cứu:** Khi tối ưu gom đơn, tuyến lấy hàng, phân công và thứ tự batch theo cùng một hàm mục tiêu, chất lượng nghiệm có cải thiện so với cách xử lý tuần tự từng phần hay không?

“Hạn hoàn thành đơn” trong đề tài là hạn hoàn thành công đoạn lấy hàng và bàn giao tại depot trong kho. Không đồng nhất thời điểm này với thời hạn giao hàng đến khách hoặc thời điểm hoàn tất đóng gói, vận chuyển.

## 2. Bối cảnh và các quyết định

Một đơn hàng có thể yêu cầu nhiều SKU, với số lượng khác nhau, ở nhiều vị trí trong kho. Gom nhiều đơn vào cùng chuyến có thể giảm số lượt đi lại, nhưng cũng có thể khiến đơn cần gấp phải chờ các sản phẩm còn lại của batch.

Hệ thống cần quyết định:

1. Những đơn nào được gom vào cùng batch.
2. Picker nào xử lý mỗi batch.
3. Tuyến đi hợp lệ qua các vị trí cần lấy hàng.
4. Thứ tự batch trên từng picker.
5. Cách cân bằng quãng đường, thời gian hoàn tất toàn bộ công việc và độ trễ của đơn.

Các quyết định liên quan với nhau: thay đổi thành phần batch làm thay đổi tuyến và thời gian xử lý; thời gian xử lý làm thay đổi lịch và độ trễ của các batch phía sau. Vì vậy, một pipeline gom đơn rồi lập lịch đúng một lần chỉ là phương án khởi tạo, chưa đủ thể hiện tối ưu đồng thời.

## 3. Mô hình hệ thống và giả định

### 3.1. Phạm vi chính được chốt

- Bài toán tĩnh: biết toàn bộ đơn từ thời điểm \(t=0\); không có đơn mới phát sinh trong lúc chạy.
- Một depot; mỗi batch bắt đầu và kết thúc tại depot này.
- \(m\ge1\) picker đồng nhất, cùng tốc độ \(v>0\), cùng sức chứa xe đẩy \(Q>0\), sẵn sàng từ \(t=0\).
- Mỗi đơn được xử lý trọn vẹn trong một batch; không chia đơn giữa các batch hoặc picker.
- Mỗi SKU có một vị trí lấy hàng cố định; tồn kho đủ đáp ứng. Chọn vị trí khi một SKU nằm ở nhiều nơi là bài toán mở rộng.
- Lối đi hai chiều, đồ thị liên thông, trọng số khoảng cách không âm và đối xứng. Không có tắc nghẽn, va chạm hay cấm hai picker cùng dùng một lối đi.
- Picker xử lý một batch liên tục, không tạm dừng để chuyển sang batch khác.
- Thời gian chuẩn bị/bàn giao được tính vào từng batch và chiếm thời gian của chính picker; không có tài nguyên bàn giao dùng chung bị giới hạn công suất.
- Due dates là **hạn mềm**: trễ vẫn là nghiệm khả thi nhưng bị phạt trong mục tiêu. Không áp đặt \(C_i\le d_i\) như ràng buộc cứng.
- Đơn vị thống nhất: khoảng cách mét, thời gian phút, tốc độ mét/phút.

### 3.2. Dữ liệu và ký hiệu

| Ký hiệu | Ý nghĩa |
|---|---|
| \(O=\{1,\ldots,n\}\), \(n\ge1\) | Tập chỉ số đơn |
| \(P=\{1,\ldots,m\}\) | Tập chỉ số picker |
| \(I\) | Tập SKU |
| \(a_{is}\in\mathbb Z_{\ge0}\) | Số lượng SKU \(s\) trong đơn \(i\) |
| \(\ell(s)\in V\) | Vị trí lấy SKU \(s\) |
| \(b_s>0\) | Mức chiếm dụng sức chứa của một đơn vị SKU \(s\) |
| \(q_i=\sum_{s\in I}a_{is}b_s\) | Nhu cầu sức chứa của đơn \(i\) |
| \(d_i\ge0\) | Hạn hoàn thành đơn \(i\), tính từ \(t=0\) |
| \(\rho_i\) | Thứ hạng đơn trong hàng chờ đầu vào, dùng cho FCFS |
| \(h_s\ge0\) | Thời gian lấy một đơn vị SKU \(s\) |
| \(h_{\mathrm{loc}}\ge0\) | Thời gian thao tác cố định tại mỗi vị trí có lấy hàng trong một chuyến |
| \(h_{\mathrm{batch}}\ge0\) | Tổng thời gian chuẩn bị và bàn giao cố định mỗi batch |

Không dùng tập hợp SKU đơn thuần để biểu diễn đơn vì sẽ mất thông tin số lượng. Nếu sức chứa tính bằng số sản phẩm thì đặt \(b_s=1\); nếu dùng thể tích hoặc tải trọng thì \(b_s\) và \(Q\) phải cùng đơn vị. Phiên bản chính dùng **một** đại lượng sức chứa; nhiều ngăn, nhiều giới hạn đồng thời chưa thuộc mô hình này.

Đồ thị kho \(G=(V,E)\) chứa depot \(v_0\), giao điểm lối đi và vị trí lấy hàng. Cạnh \(e\in E\) có chiều dài \(c_e\). Một cạnh biểu diễn lối đi thực sự hợp lệ, không phải đường thẳng xuyên qua kệ.

## 4. Order Batching

Nghiệm chứa \(K\) batch hoạt động, với \(1\le K\le n\). \(K\) là kết quả của quá trình gom đơn, không cố định bằng số picker.

\[
\mathcal B=\{B_1,\ldots,B_K\},\qquad
x_{ik}=\mathbf1(i\in B_k).
\]

Các ràng buộc:

\[
x_{ik}\in\{0,1\},\qquad
\sum_{k=1}^{K}x_{ik}=1\quad\forall i,
\]

\[
\sum_{i=1}^{n}x_{ik}\ge1,\qquad
\sum_{i=1}^{n}q_i x_{ik}\le Q\quad\forall k.
\]

Mỗi đơn xuất hiện đúng một lần và không có batch rỗng. Khi search chuyển hết đơn khỏi batch thì xóa batch và cập nhật lịch liên quan.

**Điều kiện đầu vào bắt buộc:** \(0<q_i\le Q\) với mọi đơn. Nếu một đơn vượt \(Q\), mô hình không chia đơn này không có nghiệm khả thi; phải báo rõ, không tự bỏ đơn hoặc tăng capacity.

Các công thức ở đây là đặc tả ràng buộc trên các batch hoạt động, chưa phải mô hình MILP hoàn chỉnh. Nếu xây MILP với tối đa \(n\) batch ứng viên thì cần thêm biến kích hoạt batch và liên kết lại các ràng buộc.

## 5. Picker Assignment

\[
y_{kj}=\mathbf1(B_k\text{ được giao cho picker }j),
\qquad y_{kj}\in\{0,1\}.
\]

\[
\sum_{j=1}^{m}y_{kj}=1\quad\forall k.
\]

Một picker có thể xử lý nhiều batch nối tiếp hoặc không có batch nào. Chỉ yêu cầu toàn bộ batch được giao đúng một lần; không ép dùng đủ \(m\) picker.

Phân công và thứ tự xử lý được lưu bằng một danh sách batch có thứ tự \(\pi_j\) cho mỗi picker. Các danh sách \(\pi_1,\ldots,\pi_m\) phải tạo thành một phân hoạch của tập batch. Biến \(y\) có thể suy ra từ các danh sách này để tránh lưu hai trạng thái mâu thuẫn.

## 6. Picker Routing

Tập vị trí phải phục vụ của batch:

\[
U_k=\{\ell(s):\sum_{i\in B_k}a_{is}>0\}.
\]

Nhiều đơn cùng cần một SKU/vị trí chỉ làm tăng số lượng phải lấy. Không bắt picker quay lại vị trí đó riêng cho từng đơn.

Tính khoảng cách đường đi ngắn nhất trên đồ thị:

\[
\delta(u,w)=\operatorname{dist}_{G}(u,w).
\]

Dùng Dijkstra từ depot và các vị trí cần thiết; lưu cả khoảng cách lẫn đường đi để dựng lại tuyến trên bản đồ. Không cần chạy từ mọi giao điểm nếu chỉ sử dụng ma trận giữa các điểm lấy hàng.

Một thứ tự phục vụ là:

\[
R_k=(z_0,z_1,\ldots,z_{r_k},z_{r_k+1}),
\qquad z_0=z_{r_k+1}=v_0,
\]

trong đó các \(z_1,\ldots,z_{r_k}\) liệt kê các vị trí khác depot trong \(U_k\). Khi đó:

\[
D_k=\sum_{\ell=0}^{r_k}\delta(z_\ell,z_{\ell+1}),\qquad
D_{\mathrm{total}}=\sum_{k=1}^{K}D_k.
\]

Nếu hàng nằm ngay depot, thời gian lấy hàng vẫn được tính nhưng không cần thêm chặng di chuyển. Tuyến vật lý là phép nối các đường đi ngắn nhất giữa hai điểm phục vụ liên tiếp; có thể đi qua một giao điểm hoặc cạnh nhiều lần. Đi ngang qua vị trí hàng không đồng nghĩa đã thực hiện thao tác lấy hàng tại đó.

NN và 2-Opt chạy trên ma trận \(\delta\), không dùng trực tiếp \(c_{uv}\) cho hai vị trí không có cạnh nối. Đồ thị có hướng/không cho quay đầu phải được xử lý bằng biến thể riêng; không tự đối xứng hóa dữ liệu.

## 7. Thời gian xử lý và Batch Scheduling

### 7.1. Thời gian của một batch

Đổi ký hiệu thời gian xử lý thành \(p_k\), tránh trùng với độ trễ của đơn:

\[
p_k=h_{\mathrm{batch}}+\frac{D_k}{v}
+h_{\mathrm{loc}}|U_k|
+\sum_{i\in B_k}\sum_{s\in I}a_{is}h_s.
\]

Đây là mô hình thời gian giả định của đề tài. Tham số cần lấy từ dữ liệu hoặc công bố rõ là tham số mô phỏng. Chi phí thao tác tại một vị trí được tính một lần mỗi batch, còn thời gian lấy từng đơn vị sản phẩm vẫn cộng đủ số lượng.

\[
S_k\ge0,\qquad C_k=S_k+p_k.
\]

### 7.2. Không chồng lấn trên cùng picker

Với hai batch \(k\ne l\) được giao cho cùng picker:

\[
C_k\le S_l\quad\text{hoặc}\quad C_l\le S_k.
\]

Để cài đặt đơn giản, dùng danh sách thứ tự \(\pi_j=(k_1,\ldots,k_t)\) và tính lịch:

\[
S_{k_1}=0,\qquad
S_{k_r}=C_{k_{r-1}}\ (r\ge2).
\]

Với các giả định ở mục 3, không có lợi ích mục tiêu khi cố ý chèn thời gian rỗi: dịch batch sớm hơn không tăng quãng đường, makespan hoặc độ trễ. Kết luận này không còn tự động đúng nếu bổ sung thời điểm phát hành đơn hoặc ràng buộc tài nguyên khác.

Nếu đổi tuyến, chuyển đơn hoặc đổi thứ tự batch, phải tính lại lịch của phần bị ảnh hưởng và các batch sau nó.

## 8. Due Dates và thời điểm hoàn thành đơn

Đơn được xem là hoàn thành khi batch chứa nó đã về depot và hoàn tất bàn giao:

\[
C_i=C_k\quad\text{khi }x_{ik}=1.
\]

Tương đương trên một nghiệm hợp lệ:

\[
C_i=\sum_{k=1}^{K}x_{ik}C_k.
\]

Biểu thức sau là quan hệ đánh giá nghiệm; nếu dùng MILP phải tuyến tính hóa liên kết thay vì coi tích \(x_{ik}C_k\) là tuyến tính.

Độ trễ của đơn:

\[
L_i=\max(0,C_i-d_i).
\]

Một batch có thể chứa cả đơn đúng hạn và đơn trễ. Luôn tính \(L_i\) theo **từng đơn**, không thay toàn bộ due dates bằng một deadline batch. Giá trị \(\min_{i\in B_k}d_i\) chỉ dùng làm quy tắc ưu tiên trong heuristic.

Phân biệt:

- Tổng độ trễ: \(\sum_i L_i\), đơn vị phút.
- Số đơn trễ: \(\sum_i\mathbf1(L_i>0)\), đơn vị đơn.

Giảm đại lượng thứ nhất không bảo đảm đại lượng thứ hai cũng giảm.

## 9. Hàm mục tiêu

Ba đại lượng được báo cáo độc lập:

\[
D_{\mathrm{total}},\qquad
C_{\max}=\max_{k=1,\ldots,K}C_k=\max_{i=1,\ldots,n}C_i,
\qquad L_{\mathrm{total}}=\sum_{i=1}^{n}L_i.
\]

Không dùng \(C_j\) cho picker khi chưa định nghĩa. Nếu cần thời điểm kết thúc picker \(j\), đó là thời điểm kết thúc batch cuối trong \(\pi_j\), bằng 0 nếu picker không có việc.

Hàm mục tiêu chính để search là tổng có trọng số đã chuẩn hóa:

\[
F=\alpha\frac{D_{\mathrm{total}}}{D_{\mathrm{ref}}}
+\beta\frac{C_{\max}}{C_{\mathrm{ref}}}
+\gamma\frac{L_{\mathrm{total}}}{L_{\mathrm{ref}}},
\qquad
\alpha,\beta,\gamma>0,\quad \alpha+\beta+\gamma=1.
\]

Quy ước mặc định đề xuất:

\[
D_{\mathrm{ref}}=\max(D_{\mathrm{baseline}},1\text{ mét}),\quad
C_{\mathrm{ref}}=\max(C_{\max,\mathrm{baseline}},1\text{ phút}),\quad
L_{\mathrm{ref}}=nC_{\mathrm{ref}}.
\]

Các mẫu số được tính một lần từ baseline xác định ở mục 14 cho mỗi instance rồi giữ nguyên cho mọi thuật toán và mọi seed trên instance đó. Cách chọn \(L_{\mathrm{ref}}\) tránh chia cho 0 khi baseline không có đơn trễ; đồng thời biến thành phần độ trễ thành độ trễ trung bình tương đối.

Bắt đầu với \(\alpha=\beta=\gamma=1/3\), sau đó phân tích độ nhạy của \(\gamma\) trên tập tuning. Đây là cấu hình thử nghiệm ban đầu, không phải khẳng định ba tác động vận hành có giá trị ngang nhau. Không đổi trọng số sau khi xem kết quả trên tập test.

Nếu yêu cầu nghiệp vụ là “ưu tiên đúng hạn bằng mọi giá”, phải đổi sang mục tiêu từ điển, chẳng hạn \((L_{\mathrm{total}},C_{\max},D_{\mathrm{total}})\), và mô tả cách so sánh/chấp nhận nghiệm tương ứng. Tổng có trọng số hiện tại cho phép đánh đổi và không bảo đảm ưu tiên tuyệt đối độ trễ.

## 10. Các phương pháp khởi tạo và cải tiến cơ bản

### 10.1. FCFS Batching

Sắp đơn theo \(\rho_i\). Thêm lần lượt vào batch đang mở; nếu đơn kế tiếp không vừa \(Q\), đóng batch và mở batch mới. Không bỏ qua đơn để lấp chỗ trống, vì đó sẽ là quy tắc khác.

Vì mọi đơn đã sẵn sàng tại \(t=0\), FCFS ở đây dựa trên thứ tự hàng chờ ban đầu. Nếu dữ liệu không có thứ tự đến, dùng thứ tự file hoặc hoán vị cố định có seed và ghi rõ là giả định.

### 10.2. Greedy Batching

Chọn đơn có due date sớm nhất chưa xử lý làm seed. Thử chèn các đơn còn lại thỏa capacity, ưu tiên phần tăng độ dài tuyến nhỏ nhất; phá hòa theo due date rồi ID. Dừng khi không còn đơn nào vừa batch.

“Gần nhau” được đo bằng khoảng cách đường đi trong kho, không dùng khoảng cách xuyên kệ. Đây là heuristic có quy tắc xác định, chưa phải tối ưu đồng thời.

### 10.3. Routing

NN tạo thứ tự thăm ban đầu trên \(\delta\), rồi quay về depot. 2-Opt thử đảo đoạn giữa hai điểm, giữ depot ở hai đầu và chỉ nhận cải thiện.

Công thức thay hai cạnh của 2-Opt chỉ áp dụng trực tiếp cho khoảng cách đối xứng. Nếu mở rộng sang đồ thị có hướng, phải tính cả chi phí các cạnh bên trong đoạn bị đảo và kiểm tra tính hợp lệ.

S-Shape là baseline bổ sung cho layout aisle/cross-aisle tương thích. Phải đặc tả cách vào/ra aisle, quay về depot và xử lý aisle cuối; không coi đây là một thuật toán dùng nguyên trạng cho mọi graph.

### 10.4. Phân công và lịch dùng chung cho các heuristic

Sau khi biết tuyến và \(p_k\), đặt \(d_k^{\min}=\min_{i\in B_k}d_i\). Sắp batch tăng dần theo \(d_k^{\min}\) (EDD), phá hòa bằng ID batch; lần lượt gán batch vào cuối lịch picker có thời điểm sẵn sàng nhỏ nhất, phá hòa bằng ID picker.

EDD và quy tắc picker rảnh sớm nhất là heuristic khởi tạo, không có cam kết tối ưu tổng độ trễ cho mô hình ghép này.

## 11. Thuật toán chính: ALNS trên nghiệm đầy đủ

Nghiệm phải chứa cả thành phần batch, tuyến và lịch phân công:

\[
\mathcal S=(\mathcal B,\{R_k\}_{k=1}^{K},\{\pi_j\}_{j=1}^{m}).
\]

\(D_k,p_k,S_k,C_k,C_i,L_i\) được tính từ nghiệm. Chỉ lưu tập batch là chưa đủ để đánh giá makespan và độ trễ.

ALNS dùng nhiều operator, điều chỉnh xác suất lựa chọn theo hiệu quả đã ghi nhận. Nguồn nền tảng: [Ropke và Pisinger (2006), An Adaptive Large Neighborhood Search Heuristic for the Pickup and Delivery Problem with Time Windows](https://pubsonline.informs.org/doi/10.1287/trsc.1050.0135). Các operator cho kho và lịch picker dưới đây là thiết kế đề xuất của đề tài.

### 11.1. Destroy

- Random removal: lấy một nhóm đơn ra khỏi các batch.
- Related removal: lấy các đơn gần nhau về vị trí và/hoặc due date.
- Late-order removal: lấy đơn trễ hoặc đơn thuộc batch đóng góp lớn vào độ trễ.
- Batch removal: tháo toàn bộ đơn của một hoặc vài batch.

Bỏ đơn trong destroy chỉ tạo nghiệm trung gian; không được coi nghiệm thiếu đơn là kết quả hợp lệ.

### 11.2. Repair

Greedy insertion chọn thao tác chèn khả thi có \(\Delta F\) nhỏ nhất. Regret-2 ưu tiên đơn có chênh lệch lớn nhất giữa phương án chèn tốt thứ hai và tốt nhất; trường hợp chỉ có một phương án khả thi được ưu tiên trước, phá hòa xác định bằng ID.

Với mỗi phép chèn cần:

1. Kiểm tra tải và khả năng phục vụ các vị trí.
2. Cập nhật tuyến, quãng đường và thời gian xử lý của batch.
3. Đánh giá lịch liên quan, gồm độ trễ của các batch phía sau.
4. Cho phép mở batch mới khi cần và thử vị trí đặt batch trên lịch picker.
5. Tính \(\Delta F\) theo mục tiêu đầy đủ.

Không dùng riêng khoảng cách tăng thêm làm tiêu chí repair cuối cùng. Có thể giới hạn danh sách ứng viên để tăng tốc, nhưng phải ghi cấu hình vì việc này thay đổi không gian tìm kiếm.

### 11.3. Neighborhood cho phân công và lịch

Sau repair, áp dụng với ngân sách giới hạn:

- Chuyển hoặc hoán đổi đơn giữa hai batch khả thi.
- Chuyển một batch sang picker khác.
- Chèn lại/hoán đổi thứ tự batch trên cùng picker hoặc giữa hai picker.
- 2-Opt cho các tuyến bị thay đổi.

Như vậy search có thể thay đổi cả batching, routing, assignment và scheduling. Không giữ cố định lịch EDD trong toàn bộ search.

### 11.4. Chấp nhận nghiệm, tính thích nghi và dừng

Khởi tạo từ Greedy + NN + 2-Opt + EDD. Giữ riêng nghiệm hiện tại và nghiệm tốt nhất **khả thi**.

Với \(\Delta=F_{\mathrm{candidate}}-F_{\mathrm{current}}\), nhận mọi ứng viên khả thi có \(\Delta\le0\); ứng viên xấu hơn được nhận với xác suất:

\[
\exp(-\Delta/\theta),\qquad \theta>0.
\]

Giảm nhiệt theo \(\theta\leftarrow\eta\theta\), \(0<\eta<1\). Nhiệt độ dùng thang của \(F\) đã chuẩn hóa; công bố cách chọn \(\theta_0,\eta\) và seed.

Mỗi operator có trọng số \(w_o>0\), xác suất chọn tỷ lệ với trọng số. Sau một đoạn lặp, cập nhật:

\[
w_o\leftarrow(1-\lambda)w_o+
\lambda\frac{\operatorname{score}_o}{\operatorname{uses}_o},
\quad 0<\lambda\le1.
\]

Giữ nguyên nếu chưa được dùng; chặn dưới bằng một giá trị dương để tránh mất hẳn khả năng khám phá. Quy định trước điểm thưởng cho nghiệm tốt nhất mới, cải thiện nghiệm hiện tại và nghiệm xấu hơn được chấp nhận; theo dõi riêng nhóm destroy và repair.

Dừng theo ngân sách thời gian và/hoặc số vòng lặp cấu hình trước. Trả về nghiệm tốt nhất đã kiểm tra khả thi, không mặc định trả nghiệm hiện tại cuối cùng. Regret-k tổng quát và operator bổ sung là phần mở rộng sau khi bản Random/Related/Late/Batch + Greedy/Regret-2 hoạt động ổn định.

## 12. Kiến trúc xử lý

~~~text
Dataset + cấu hình thực nghiệm
             |
             v
Kiểm tra đầu vào -> Graph + khoảng cách + đường đi ngắn nhất
             |
             v
Khởi tạo batch -> Route -> Thời gian xử lý -> Phân công/lịch
             |
             v
Evaluator + kiểm tra nghiệm đầy đủ
             |
             v
ALNS: thay batch / tuyến / picker / thứ tự
             |
             +--> tính lại chi phí và lịch bị ảnh hưởng
             +--> kiểm tra khả thi, chấp nhận, cập nhật nghiệm tốt nhất
             |
             v
Kiểm tra lại toàn bộ -> JSON kết quả + bảng đo + demo
~~~

Evaluator và validator là thành phần dùng chung cho mọi thuật toán. Cache tuyến theo tập vị trí và cấu hình routing; không dùng lại thời gian xử lý cũ nếu số lượng SKU trong batch đã đổi.

## 13. Dataset và mức tương thích

### 13.1. Dữ liệu chính

Bắt đầu bằng kho tổng hợp dạng chữ nhật, lối đi hai chiều, một depot và đơn được sinh có seed. Cách này cho phép kiểm thử chính xác các giả định trước khi nhập benchmark bên ngoài.

Schema nội bộ tối thiểu:

| Nhóm | Trường bắt buộc |
|---|---|
| Kho | Đỉnh, cạnh, độ dài cạnh, depot, tính có hướng |
| Sản phẩm | SKU, vị trí, mức chiếm dụng capacity |
| Đơn | ID, các cặp SKU–số lượng, due date, thứ hạng FCFS |
| Vận hành | Số picker, capacity, tốc độ, các tham số thao tác |
| Nguồn gốc | Nguồn/phiên bản, phép chuyển đổi, seed, đơn vị |

### 13.2. Foodmart và HappyChic

Foodmart và HappyChic có nguồn tải từ [trang benchmark Joint order batching and picker routing](https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/batching/). Trang nguồn mô tả Foodmart với layout hình chữ nhật, còn HappyChic có layout không cho backtracking; vì vậy không đưa HappyChic trực tiếp vào bộ giải đối xứng của phạm vi chính.

[Đặc tả format của bộ dữ liệu](https://pagesperso.g-scop.grenoble-inp.fr/~cambazah/batching/data/format.txt) còn có số thùng trên xe, capacity mỗi thùng, cờ cho phép trộn đơn trong thùng và depot xuất phát/kết thúc. Vì vậy, ngay cả Foodmart cũng cần kiểm tra từng instance; một bất đẳng thức tổng tải \(\le Q\) không tự thay thế được mọi ràng buộc thùng.

Ưu tiên các instance tương thích. Nếu đơn giản hóa kho hoặc sức chứa, đặt tên là **instance chuyển đổi**, lưu quy tắc và không so trực tiếp với best-known solution của bài toán gốc. Không tự thêm cạnh ngược hoặc đồng nhất hai depot để làm dữ liệu “chạy được”.

### 13.3. Zalando

[Repository chính thức của Zalando](https://github.com/zalandoresearch/batching-benchmarks/) có bốn file articles.json, orders.json, parameters.json và warehouse_items.json cho instance được sinh. Tuy nhiên, bài toán nguồn là *Joint Order Selection, Allocation, Batching and Picking*, có quyết định lựa chọn đơn và phân bổ item; không mặc nhiên là benchmark cho lịch nhiều picker với due dates như đề tài này. [Mô tả của nhóm Zalando](https://engineering.zalando.com/posts/2024/01/paper-warehouse-order-batching.html).

Đưa Zalando vào hướng mở rộng, sau khi xác định được cách chuyển đổi và phần nào của bài toán gốc bị lược bỏ.

### 13.4. Bổ sung due dates có thể tái lập

Chưa xác nhận các instance tải thực tế có đủ due dates, số picker và thời gian thao tác. Trước khi chạy phải kiểm tra; dữ liệu thiếu được bổ sung như **kịch bản tổng hợp**, không mô tả là hạn giao thực tế.

Một quy tắc sinh đề xuất, độc lập với thuật toán cần đánh giá:

1. Xử lý từng đơn riêng bằng NN để có thời lượng tham chiếu \(\hat p_i\).
2. Tính \(H=\max(\max_i\hat p_i,\sum_i\hat p_i/m)\).
3. Sinh \(U_i\sim\operatorname{Uniform}[0,1]\) với seed cố định.
4. Đặt \(d_i=\hat p_i+\tau H(1+\xi U_i)\), với \(\tau>0,\xi\ge0\).

Thử \(\tau\) nhỏ/vừa/lớn để tạo hạn chặt/vừa/lỏng và công bố giá trị cụ thể sau khi hiệu chỉnh trên tập tuning. Đây không phải chứng minh có lịch đúng hạn cho mọi đơn. Lưu file due dates đã sinh, dùng chung cho mọi phương pháp. Khi thay \(m\) để đo riêng tác động số picker, giữ due dates cố định; nếu sinh lại theo \(m\), phải gọi đó là thí nghiệm giữ mức tải tương đối.

## 14. Các phương pháp so sánh

| Method | Batching | Routing | Phân công và lịch | Cải tiến |
|---|---|---|---|---|
| B0 — baseline chính | FCFS | NN | EDD + picker rảnh sớm nhất | Không |
| B1 | Greedy | NN | Cùng quy tắc B0 | Không |
| B2 | Greedy | NN + 2-Opt | Cùng quy tắc B0 | Chỉ tuyến |
| B3 — đối chứng lịch | Như B2 | Như B2 | Khởi tạo như B0 rồi relocate/swap batch | Tuyến + lịch, batch cố định |
| Proposed | ALNS | NN + 2-Opt cho batch thay đổi | Search cả picker và thứ tự batch | Tối ưu phối hợp |
| B-S — bổ sung khi tương thích | FCFS | S-Shape | Cùng quy tắc B0 | Không |

B0 dùng được trên toàn bộ graph thuộc phạm vi chính, nên là baseline để chuẩn hóa \(F\). B-S chỉ báo cáo trên layout tương thích. Mọi phương pháp phải xử lý cùng tập đơn, cùng số picker, capacity, due dates, thời gian thao tác và quy tắc tính hoàn thành đơn.

So sánh thêm ALNS với LNS trọng số operator cố định để kiểm tra lợi ích của cơ chế thích nghi. Không gán mọi cải thiện của Proposed cho ALNS nếu chưa tách tác động thay batching và thay lịch.

## 15. Metrics và quy tắc báo cáo

Báo cáo tối thiểu:

- Tỷ lệ nghiệm khả thi; mọi kết quả chất lượng phải qua validator.
- \(F,D_{\mathrm{total}},C_{\max},L_{\mathrm{total}}\).
- \(N_{\mathrm{late}}=\sum_i\mathbf1(L_i>0)\), tỷ lệ đúng hạn \(1-N_{\mathrm{late}}/n\).
- Số batch, số picker thực sự dùng, mức tải theo batch.
- Thời gian tiền xử lý, thời gian tối ưu và thời gian tổng.

Với metric \(M\) càng nhỏ càng tốt và \(M_{\mathrm{baseline}}>0\):

\[
\operatorname{Improvement}_M=
100\frac{M_{\mathrm{baseline}}-M_{\mathrm{algorithm}}}
{M_{\mathrm{baseline}}}.
\]

Giá trị âm là suy giảm, không cắt về 0. Khi baseline bằng 0, ghi tỷ lệ cải thiện là N/A và báo chênh lệch tuyệt đối. Tỷ lệ cải thiện \(F\) chỉ có ý nghĩa khi giữ cùng trọng số và mẫu số chuẩn hóa.

Không gọi chênh lệch với baseline heuristic là “optimality gap”. Chỉ dùng khoảng cách tới tối ưu khi có nghiệm tối ưu được chứng nhận; nếu chỉ có cận dưới thì ghi rõ gap so với cận dưới.

## 16. Thiết kế thực nghiệm và kiểm chứng

### 16.1. Kiểm tra tính đúng trước khi đo chất lượng

Các ca kiểm tra tối thiểu:

1. Một đơn, một vị trí: tính tay được quãng đường, thao tác và thời điểm hoàn thành.
2. Nhiều đơn dùng chung SKU/vị trí: lấy đủ số lượng, không cộng lặp quãng đường vì trùng SKU.
3. Batch vừa đúng \(Q\); đơn vượt \(Q\); SKU thiếu vị trí; điểm không tới được.
4. Mỗi đơn/batch được phục vụ đúng một lần, không mất đơn sau destroy/repair.
5. Mọi route xuất phát/kết thúc đúng depot và đi theo cạnh hợp lệ.
6. Batch cùng picker không chồng lấn; tổng thời gian khớp \(D_k/v\) và thao tác.
7. Hai đơn cùng batch, due dates khác nhau: chung \(C_k\), độ trễ khác nhau.
8. Chuyển một đơn hoặc batch làm evaluator cập nhật cả những batch phía sau.
9. 2-Opt không tăng quãng đường trên dữ liệu đối xứng; tính lại tổng cạnh để kiểm tra cache.
10. Baseline có độ trễ bằng 0; picker không có việc; chạy cùng seed tái lập được kết quả.

Tạo một số instance rất nhỏ, ví dụ 4–8 đơn tùy số vị trí, để vét cạn các phân hoạch khả thi, tuyến, phân công và thứ tự. Chỉ gọi kết quả là tối ưu khi đã duyệt/chứng nhận đầy đủ; tối ưu route với batching cố định chưa chứng nhận nghiệm joint.

### 16.2. Quy mô và ngân sách

Thử \(n=20,50,100,200\); ghi thêm số SKU, số vị trí khác nhau, số dòng hàng/đơn và kích thước graph vì \(n\) đơn không phản ánh hết độ khó.

Thay đổi có kiểm soát số picker, capacity, độ chặt due dates và mức phân tán vị trí. Không cần tích Descartes toàn bộ cấu hình ngay từ đầu; chọn một cấu hình chuẩn rồi thay từng yếu tố.

Với mỗi cấu hình, đề xuất ít nhất 5 instance và 10 seed cho thuật toán ngẫu nhiên, điều chỉnh quy mô nếu ngân sách không đủ và công bố phần cắt giảm. Heuristic xác định có thể lặp để đo runtime, nhưng không coi các lần đó là nhiều nghiệm ngẫu nhiên độc lập.

Công bố CPU/RAM, phiên bản phần mềm, seed, tiêu chí dừng, ngân sách thời gian, tỷ lệ destroy và tham số ALNS. Các phương pháp search dùng cùng giới hạn thời gian trên cùng instance; heuristic dừng sớm được báo thời gian thực tế. Tách tập tuning và tập test.

### 16.3. Cách phân tích

- Báo mean, độ lệch chuẩn và best cho phương pháp ngẫu nhiên; kèm số lần chạy.
- Tổng hợp chênh lệch ghép cặp trên cùng instance; không coi seed của cùng một instance là nhiều bộ dữ liệu độc lập.
- Vẽ chất lượng nghiệm theo thời gian để xem lợi ích thêm của thời gian tính toán.
- Ablation: bỏ thích nghi operator; bỏ operator lịch; bỏ 2-Opt.
- Ghi nhận cả trường hợp ALNS không tốt hơn baseline.

Mẫu bảng sau **chưa có số liệu thực nghiệm**:

| Algorithm | F | Distance (m) | Makespan (min) | Total tardiness (min) | Late orders | Runtime (s) |
|---|---:|---:|---:|---:|---:|---:|
| B0 | — | — | — | — | — | — |
| B1 | — | — | — | — | — | — |
| B2 | — | — | — | — | — | — |
| B3 | — | — | — | — | — | — |
| ALNS | — | — | — | — | — | — |

## 17. Demo

Xây dựng giao diện 2D hiển thị:

- Graph kho, kệ, depot và vị trí lấy hàng.
- Thành phần và tải của từng batch.
- Tuyến vật lý của từng picker, được dựng từ cạnh/đường đi ngắn nhất.
- Gantt chart các batch trên picker; thời điểm hoàn thành và trạng thái đúng hạn/trễ của từng đơn.
- Bảng so sánh baseline và nghiệm tốt nhất với cùng cấu hình.
- Thời gian chạy, seed và thông báo dữ liệu/nghiệm không hợp lệ.

Hoạt ảnh là công cụ xem lại lịch đã tính. Do mô hình bỏ qua congestion, demo không được tuyên bố đã tối ưu tránh va chạm giữa picker. Không hiển thị số đo minh họa như kết quả thuật toán thật.

## 18. Cấu trúc chương trình dự kiến

~~~text
project/
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
├── configs/
├── src/
│   ├── models.py
│   ├── parser.py
│   ├── warehouse_graph.py
│   ├── batching/
│   │   ├── fcfs.py
│   │   └── greedy.py
│   ├── routing/
│   │   ├── s_shape.py
│   │   ├── nearest_neighbor.py
│   │   └── two_opt.py
│   ├── scheduling/
│   │   ├── list_scheduler.py
│   │   └── neighborhoods.py
│   ├── search/
│   │   ├── alns.py
│   │   ├── destroy.py
│   │   └── repair.py
│   ├── evaluator.py
│   ├── validator.py
│   ├── instance_generator.py
│   └── benchmark.py
├── tests/
├── demo/
│   └── app.py
├── results/
├── requirements.txt
└── README.md
~~~

ALNS nằm ở cấp search vì tác động lên cả batch và lịch, không chỉ là một thuật toán trong thư mục batching. Kết quả JSON lưu đầy đủ danh sách đơn trong batch, tuyến, picker, thứ tự, thời gian và metadata để có thể đánh giá lại.

## 19. Phạm vi bắt buộc và thứ tự triển khai

**Core bắt buộc để giữ đúng tên đề tài:** batching + routing + multi-picker assignment + scheduling + soft due dates. Không để ba thành phần cuối thành tùy chọn trong khi vẫn dùng tiêu đề “Multi-Picker … Scheduling with Due Dates”.

Triển khai theo bốn mốc:

1. Chốt schema, graph, giả định thời gian; có evaluator/validator và instance nhỏ kiểm tra bằng tay.
2. Hoàn thành B0–B2 với phân công nhiều picker, lịch và tính độ trễ đầy đủ.
3. Thêm B3, LNS rồi cơ chế thích nghi thành ALNS; kiểm tra các thao tác joint.
4. Chạy benchmark tái lập, ablation, phân tích kết quả và demo.

Phần mở rộng: HappyChic/graph có hướng, nhiều vị trí cho cùng SKU, nhiều loại picker, nhiều depot, nhiều ngăn xe đẩy, release times, congestion và dynamic orders.

Nếu phải giảm phạm vi vì thời gian, ưu tiên giảm số dataset/operator trước. Nếu thực sự chỉ hoàn thành batching + routing thì cần đổi tên và câu hỏi nghiên cứu, thay vì coi đó là hoàn thành toàn bộ đề tài hiện tại.

## 20. Kết quả mong đợi và tiêu chí hoàn thành

Đề tài được xem là hoàn thành khi:

1. Đọc được schema nội bộ và ít nhất một bộ dữ liệu có mô tả nguồn gốc/chuyển đổi.
2. Sinh được instance có seed và các mức due dates.
3. B0–B3 cùng Proposed trả nghiệm đủ đơn, đúng tải, route hợp lệ, lịch không chồng lấn.
4. Có ALNS thực sự điều chỉnh trọng số operator và thay đổi phân công/thứ tự batch.
5. Có evaluator độc lập, kiểm tra instance nhỏ và báo cáo lỗi đầu vào.
6. Có benchmark chất lượng, thời gian, độ ổn định và các đối chứng cần thiết.
7. Có demo tuyến và lịch nhiều picker.
8. Có README, cấu hình chạy và kết quả thô để tái lập.

Mong đợi là đo được lợi ích và giới hạn của cách tối ưu phối hợp. Không đặt yêu cầu “ALNS phải thắng mọi instance” hoặc một tỷ lệ cải thiện chưa được đo.

## 21. Độ khó và đóng góp của đề tài

Bài toán kết hợp lựa chọn phân hoạch đơn, tuyến và lịch trên nhiều picker. Một trường hợp riêng với một picker, một batch và không xét hạn đã chứa bài toán chọn thứ tự thăm các vị trí trên ma trận đường đi ngắn nhất; Dijkstra chỉ giải từng chặng, không giải được phần chọn thứ tự này.

Không suy ra bài toán “thuộc lớp độ khó cao hơn TSP/CVRP” chỉ vì có nhiều thành phần. Điểm khó của đề tài nằm ở tương tác giữa các quyết định và quy mô không gian nghiệm; NN, 2-Opt và ALNS là heuristic, không bảo đảm tối ưu toàn cục.

Đóng góp dự kiến trong phạm vi môn **Thuật toán ứng dụng**:

- Một mô hình có giả định, thời gian xử lý, capacity và due dates nhất quán.
- Một evaluator và validator dùng chung để so sánh công bằng.
- Bộ operator ALNS xét đồng thời vị trí hàng, hạn đơn và lịch picker.
- Thực nghiệm tách được tác động batching, routing, scheduling và cơ chế thích nghi.

Đây là đóng góp thiết kế, cài đặt và đánh giá thực nghiệm. Chưa khẳng định tính mới học thuật của mô hình hay operator khi chưa đối chiếu đầy đủ các nghiên cứu liên quan.
