# Mô hình chi phí — cơ sở lý thuyết của pipeline đồng thiết kế

Tài liệu này là **lý thuyết** mà pipeline CDP dựa vào: một mô hình tường minh, tham số hoá, và
**kiểm chứng được**, dùng để (a) giải thích số đã đo, (b) **dự báo một thiết kế chưa tồn tại**,
(c) định lượng sai số dự báo (câu hỏi PQ1 của `docs/PIPELINE_SPEC.md`).

Quy ước nhãn trong toàn tài liệu: **[đo]** số từ Verilator/kit · **[RTL]** tham số đọc từ mã Verilog ·
**[suy ra]** kết quả của phép tính trên hai nhãn trên · **[cấu trúc]** đếm từ cấu trúc mô hình M1-S.
Không có nhãn nào là "ước đoán".

---

## 1. Phương trình cơ bản

Lõi `mycore` là máy trạng thái tất định, **không đoán nhánh, không hazard, không cache**. Mỗi lệnh chiếm
một số chu kỳ chỉ phụ thuộc **lớp** của nó. Vì vậy thời gian chạy một đoạn mã là

$$C = \sum_{c\,\in\,\text{lớp lệnh}} n_c \cdot \lambda_c$$

- $n_c$ — **số lệnh động** thuộc lớp $c$ (một lệnh chạy 1000 lần đếm 1000). Do **ISS** đếm (bước S2).
- $\lambda_c$ — **số chu kỳ mỗi lệnh** của lớp $c$ trên lõi. Do **RTL** quy định, không phải tham số
  hiệu chuẩn.

Không có số hạng $C_{\text{stall}}$ cho `mycore`: mọi chu kỳ đều thuộc về một lệnh xác định. Với
PicoRV32 thì có (bus 2 chu kỳ cho mọi truy cập, PCPI cho lệnh tùy biến), nên mô hình PicoRV32 là mô hình
**hiệu chuẩn thống kê**, không tất định — và phải báo sai số.

### 1.1 Bảng $\lambda$ của `mycore` — đọc trực tiếp từ `rtl/mycore/mycore.v` **[RTL]**

| lớp lệnh | trạng thái máy đi qua | $\lambda$ (FAST_ADDR=1) | $\lambda$ (FAST_ADDR=0) |
|---|---|---:|---:|
| alu, lui, auipc, nhánh (nhảy hay không), jal/jalr, csr | `S_EXEC` | **1** | 2 |
| **DOT4** (lệnh tùy biến, trong tầng thực thi) | `S_EXEC` | **1** | 2 |
| load, store | `S_EXEC` → `S_MEM` | **2** | 4 |
| mul/mulh/mulhsu/mulhu | `S_EXEC` → `S_MD` | **2** | 3 |
| **REQ** (lệnh tùy biến, dùng lại bộ nhân) | `S_EXEC` → `S_MD` | **2** | 3 |
| div/divu/rem/remu | `S_EXEC` → 33×`S_MD` | **34** | 35 |

Hai điều đáng ghi: **nhánh không có hình phạt** (địa chỉ lệnh kế tính xong trong cùng chu kỳ), và
`FAST_ADDR=0` cộng đúng **+1 chu kỳ cho mọi lệnh** cộng thêm **+1 nữa cho mỗi truy cập dữ liệu**.

### 1.2 Dạng gọn cho `mycore`, FAST_ADDR=1

Vì $\lambda=1$ cho mọi lệnh trừ ba lớp, với $N$ là tổng số lệnh động (`rdinstret`):

$$C = N + n_{\text{mem}} + n_{\text{mul}} + n_{\text{REQ}} + 33\,n_{\text{div}}$$

Hệ quả kiểm được ngay: **$C-N$ phải là một hằng số không phụ thuộc ảnh đầu vào**, vì luồng điều khiển
của M1-S không phụ thuộc dữ liệu.

| cấu hình | $C$ (trung vị) **[đo]** | $N$ **[đo]** | $C-N$ trên 10 ảnh **[đo]** | $(C-N)/C$ |
|---|---:|---:|---|---:|
| A-V0 (PicoRV32) | 8.987.660 | 1.358.200 | **7.629.460, hằng số cả 10 ảnh** | 0,849 |
| B-V1 (mycore) | 1.459.993 | 911.920 | **548.073, hằng số cả 10 ảnh** | 0,375 |
| B-V3 (mycore+DOT4+REQ) | 365.992 | 277.839 | **88.153, hằng số cả 10 ảnh** | 0,241 |

Dự đoán "hằng số" **đúng tuyệt đối cả ba cấu hình**. Và con số 0,849 của A-V0 là chính câu chuyện vi
kiến trúc: **84,9 % chu kỳ của PicoRV32 không hoàn thành lệnh nào**.

### 1.3 Mô hình nghịch: suy ra thành phần lệnh mà KHÔNG cần mô phỏng

Hai cấu hình chỉ khác nhau ở `FAST_ADDR` chạy **cùng một file `firmware.hex`** (đã kiểm: `rdinstret`
khớp tuyệt đối, mục 1.2). Hai phương trình, hai ẩn:

$$C_{\text{FA=1}} = N + n_{\text{mem}} + n_{\text{mul}}, \qquad
  C_{\text{FA=0}} = 2N + 2\,n_{\text{mem}} + n_{\text{mul}}$$

| firmware | $N$ **[đo]** | $C_{\text{FA=1}}$ **[đo]** | $C_{\text{FA=0}}$ **[đo]** | $n_{\text{mem}}$ **[suy ra]** | $n_{\text{mul}}$ **[suy ra]** |
|---|---:|---:|---:|---:|---:|
| v0 (C thẳng) | 1.358.200 | 1.978.697 | 3.750.617 | **413.720** | **206.777** |
| v1 (đã tối ưu) | 911.920 | 1.459.993 | 2.713.235 | **341.322** | **206.751** |

**Phép kiểm chéo của lý thuyết.** Số phép nhân mỗi ảnh suy ra từ cấu trúc mô hình **[cấu trúc]**:
192.064 MAC + 2 phép nhân cho mỗi lần requantize × (26·26·8 + 11·11·16 + 10) = 192.064 + 2·7.354 =
**206.772**. So với **206.777** và **206.751** suy ra từ phép đo: lệch **5 và 21 lệnh trên 206 nghìn
(0,01 %)**.

Mô hình được tham số hoá **chỉ từ RTL**, nhưng đảo được hai phép đo thành thành phần lệnh động khớp với
cấu trúc toán học của mạng tới 0,01 % — **trước khi ISS tồn tại**. Đây là bằng chứng mạnh nhất cho tính
đúng của dạng phương trình ở mục 1. ISS ở S2 phải tái tạo đúng các con số này; nếu lệch, ISS sai, không
phải mô hình sai.

---

## 2. Bốn đòn bẩy, và vì sao các hệ số tăng tốc NHÂN được với nhau

Từ $C=\sum n_c\lambda_c$, chỉ có bốn cách làm $C$ nhỏ đi:

| # | Đòn bẩy | Tác động lên phương trình | Tầng trong catalog |
|---|---|---|---|
| i | **Giảm số lệnh** (bung vòng, con trỏ chạy, giữ trọng số trong thanh ghi) | $n_{\text{addr}}, n_{\text{loop\_ctrl}} \downarrow$ | B1 (phần mềm) |
| ii | **Gộp nhiều lệnh thành một** (DOT4, REQ, kẹp bão hoà) | $\sum_{i\in p}n_i\lambda_i \to n_p\lambda_{\text{mới}}$ | L1, L2 |
| iii | **Giảm $\lambda$** (bộ nhớ hai cổng → load 1 chu kỳ; nhân 1 chu kỳ) | $\lambda_c \downarrow$ | L3 |
| iv | **Phát nhiều lệnh mỗi chu kỳ** | $C \to \max(C/W,\;L_{\text{crit}})$ | L4, L5 |

Đòn bẩy (i) tác động lên các $n_c$; (iii) tác động lên các $\lambda_c$. Hai nhóm nhân tử **độc lập**
trong cùng một tích, nên nếu phần mềm chia các $n$ cho $a$ và vi kiến trúc chia các $\lambda$ cho $b$ thì
$C$ chia cho $ab$. Đó là lý do **lý thuyết** cho việc 24,6× đã đo bằng đúng tích 1,45 × 4,26 × 2,31 ×
1,29 × 1,33 **[đo]** — và cũng là lý do một lệnh tùy biến cho **lợi ích lớn hơn trên mã đã tối ưu**
(RQ2, đã đo 1,56× so với 2,13×): gộp lệnh (ii) chỉ cắt được phần $n_{\text{mac}}$, nên khi
$n_{\text{addr}}$ còn lớn thì tỷ trọng của nó nhỏ.

---

## 3. Công thức dự báo cho từng họ ứng viên

Ký hiệu: $f_X = (\text{chu kỳ thuộc } X)/C$ là tỷ trọng; tăng tốc toàn mô hình bị chặn bởi Amdahl
$S \le 1/(1-f_X)$.

| Họ | Công thức tiết kiệm $\Delta C$ | Cần gì từ S3 |
|---|---|---|
| **L1 gộp lệnh** cho mẫu $p$ | $\Delta C = n_p\left(\sum_{i\in p}\lambda_i - \lambda_{\text{mới}}\right)$ | $n_p$ = số lần mẫu xuất hiện động |
| **L2 SIMD $W$ làn** | $\Delta C = \left(1-\tfrac1W\right)\left(n_{\text{mac}}\lambda_{\text{mac}} + n_{\text{ld}}\lambda_{\text{ld}}\right) - C_{\text{bố cục}}$ | $n_{\text{mac}}, n_{\text{ld}}$, độ rộng phần tử, thẳng hàng |
| **L3 đổi $\lambda$** | $\Delta C = \sum_c n_c\,\Delta\lambda_c$ — **tính trực tiếp, không cần viết RTL** | $n_c$ theo lớp |
| **L4 mảng MAC $P\times Q$** | $C \ge n_{\text{mac}}/(PQ) + C_{\text{chuyển dữ liệu}}$ | byte/MAC, mức tái sử dụng |
| **L5 phát $W$ lệnh** | $C \ge \max(C/W,\ L_{\text{crit}})$ | đường găng $L_{\text{crit}}$ |

Hai chặn trên tuyệt đối, không phụ thuộc cách hiện thực:

- **Chặn ILP**: $C \ge L_{\text{crit}}$ (độ dài đường găng phụ thuộc dữ liệu qua thanh ghi) ⟹ $\text{IPC} \le N/L_{\text{crit}}$.
- **Chặn roofline bộ nhớ**: $\text{MAC/chu kỳ} \le \min\!\left(P,\ \dfrac{B\cdot R}{b}\right)$ với $B$ = byte/chu kỳ
  mà bộ nhớ cấp được, $R$ = mức tái sử dụng, $b$ = byte/MAC, $P$ = số MAC/chu kỳ của đơn vị tính.

Với kit này $B$ nhỏ và cố định (một cổng BSRAM, 4 byte mỗi 2 chu kỳ ở `FAST_ADDR=1`), nên **roofline là
rào chắn thật, không phải hình thức**: $n_{\text{mem}}$ của v1 là 341.322 cho 192.064 MAC
⟹ **1,78 truy cập dữ liệu mỗi MAC** **[suy ra]**. Mọi ứng viên tính toán thuần (L2, L4) sẽ đụng rào này
trước khi đụng rào số học — đây là dự đoán của lý thuyết mà S3 phải xác nhận bằng byte/MAC thật.

---

## 4. Tham số của mô hình và nguồn của từng tham số

| Tham số | Nguồn | Bước |
|---|---|---|
| $n_c$ theo lớp lệnh, theo lớp mạng, theo vòng lặp | trace của ISS | S2 → S3 |
| $\lambda_c$ của `mycore` | **đọc từ `mycore.v`** (mục 1.1), ghi thành `cdp/iss/timing/mycore.yaml` | S2 |
| $\lambda_c$ hiệu dụng của PicoRV32 | **hiệu chuẩn** từ trace Verilator; mục tiêu sai số ≤ 2 % | S2 |
| $L_{\text{crit}}$ | đồ thị phụ thuộc RAW của khối nóng | S3 |
| $b$ (byte/MAC), $R$ (tái sử dụng) | profile truy cập bộ nhớ | S3 |
| $P$, $B$ | RTL + ngân sách tài nguyên của kit | S6 |
| chi phí LUT/DFF/MULT, Fmax | yosys + nextpnr | S6 |

---

## 5. Cách lý thuyết này bị kiểm chứng (hoặc bị bác bỏ)

| Phép kiểm | Tiêu chí | Bước |
|---|---|---|
| K0 | $C_{\text{mô hình}} = C_{\text{Verilator}}$ **tuyệt đối** cho `mycore` trên **8** cấu hình | S2 |
| K0' | sai số ≤ 2 % cho PicoRV32 trên **6** cấu hình | S2 |
| K1 | $n_{\text{mem}}, n_{\text{mul}}$ do ISS đếm = số **[suy ra]** ở mục 1.3 (413.720 / 341.322 và 206.777 / 206.751) | S2 |
| K2 | dự báo của $\Delta C=\sum n_c\Delta\lambda_c$ cho một thay đổi L3 so với đo thật | S6 |
| K3 | dự báo cho một **lệnh mới** (L1/L2) so với đo thật | S6 |

Mọi dự báo ghi vào sổ cái **trước** khi hiện thực. Sai số dự báo là dữ liệu nghiên cứu, **không được sửa
lùi** (SPEC 0.3).

---

## 6. Giới hạn — ghi trước, không chữa sau

1. **Không mô hình hoá Fmax.** Mọi so sánh là **số chu kỳ ở 27 MHz cố định**. Một ứng viên làm giảm Fmax
   xuống dưới 27 MHz bị loại bởi `cdp synth`, không bởi mô hình này.
2. **Không mô hình hoá chi phí LUT.** Bài học đã đo: hiệu hai lần tổng hợp chỉ đo được chi phí phần cứng
   khi RTL giống hệt nhau (S1 vừa cho một ví dụ: +20 LUT4 của B-V1 đến từ khối REQ đã tắt).
3. **Không có cache, không có dự đoán nhánh** trong thiết kế này — đó là lý do mô hình đếm lớp lệnh đủ
   chính xác để kỳ vọng khớp **tuyệt đối**. Mô hình này **không** chuyển sang lõi có cache mà không sửa.
4. **PicoRV32 chỉ hiệu chuẩn.** $C_{\text{stall}}$ của nó phụ thuộc trạng thái bus, nên con số của nó là
   thống kê; mọi kết luận "bằng tuyệt đối" chỉ áp cho `mycore`.
5. **Mục 1.3 giả định $n_{\text{div}}=0$** (firmware không dùng chia) và giả định cặp FA=1/FA=0 chạy đúng
   cùng một firmware — cả hai đã kiểm bằng `rdinstret` khớp tuyệt đối.
