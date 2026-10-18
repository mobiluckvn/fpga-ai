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

Ở bảng này $N$ là `instret` **do firmware tự báo**, tức bao luôn 16 lệnh nằm giữa các cửa sổ đo; dùng để
kiểm tính "hằng số" thì không sao, nhưng **không** dùng được để giải hệ ở mục 1.3 (xem cảnh báo ở đó).

Dự đoán "hằng số" **đúng tuyệt đối cả ba cấu hình**. Và con số 0,849 của A-V0 là chính câu chuyện vi
kiến trúc: **84,9 % chu kỳ của PicoRV32 không hoàn thành lệnh nào**.

### 1.3 Mô hình nghịch: suy ra thành phần lệnh mà KHÔNG cần mô phỏng

Hai cấu hình chỉ khác nhau ở `FAST_ADDR` chạy **cùng một file `firmware.hex`** (đã kiểm: `rdinstret`
khớp tuyệt đối). Với $N$ là số lệnh **trong năm cửa sổ đo**, hai phương trình, hai ẩn:

$$C_{\text{FA=1}} = N + n_{\text{mem}} + n_{\text{mul}}, \qquad
  C_{\text{FA=0}} = 2N + 2\,n_{\text{mem}} + n_{\text{mul}}$$

Giải **từng ảnh** (không lấy trung vị của hai đại lượng khác nhau — xem cảnh báo dưới):

| firmware | $N$ (ảnh 0) | $C_{\text{FA=1}}$ | $C_{\text{FA=0}}$ | $n_{\text{mem}}$ **[suy ra]** | $n_{\text{mul}}$ **[suy ra]** |
|---|---:|---:|---:|---:|---:|
| v0 (C thẳng) | 1.358.057 | 1.978.570 | 3.750.362 | **413.735** | **206.778** |
| v1 (đã tối ưu) | 911.777 | 1.459.866 | 2.712.980 | **341.337** | **206.752** |

**Phép kiểm K1.** ISS (bước S2) đếm trực tiếp $n_{\text{mem}}$ và $n_{\text{mul}}$ và cho **đúng các con số
này trên cả 20 ảnh (2 firmware × 10 ảnh), khớp tuyệt đối**. Mô hình nghịch — chỉ từ bốn con số đo và
bảng $\lambda$ đọc từ RTL — thay được cả một bộ mô phỏng.

**Phép kiểm chéo bằng cấu trúc mô hình** (không dùng phép đo nào):

$$n_{\text{mul}} = \underbrace{192.064}_{\text{MAC}} + 2\underbrace{(5.408 + 1.936)}_{\text{số lần requantize}} = \mathbf{206.752}$$

— **khớp chính xác** số của v1. Hai chi tiết mà chính phép đếm của ISS đã sửa lại suy đoán ban đầu:

- `dense` có **đúng 4.000** phép nhân = đúng 4.000 MAC và **không** requantize: 10 logit giữ nguyên
  int32, argmax lấy trực tiếp (xem `main.c`). Lúc đầu tôi cộng thừa $2\times10$ cho `dense`.
- v0 nhiều hơn v1 **đúng 26** phép nhân, tất cả nằm trong `conv1` = **một phép nhân tính chỉ số cho mỗi
  hàng đầu ra** (26 hàng). Đây là một trong những thứ mà tối ưu phần mềm A-V1 xoá đi bằng con trỏ chạy —
  **đòn bẩy (i) của mục 2, đo được bằng số**.

> **Cảnh báo phương pháp đã gặp thật.** Bản đầu của mục này giải hệ bằng $N$ mà *firmware tự báo*
> (`rdinstret`), và lệch 16 lệnh. Nguyên nhân: `instret` của firmware bao luôn **16 lệnh nằm GIỮA** các
> cửa sổ (8 lần `rdcycle` đóng/mở cửa sổ + các phép trừ `t1-t0`), còn $C$ thì chỉ cộng chu kỳ **trong**
> cửa sổ. Trộn hai phạm vi khác nhau cho sai số 0,0012 % — nhỏ, nhưng là **sai hệ thống**. Thêm nữa, lấy
> trung vị 10 ảnh **riêng cho từng đại lượng** rồi mới giải hệ cũng sinh lệch ±1, vì `pool1` có luồng điều
> khiển phụ thuộc dữ liệu nên trung vị của $C$ và của $N$ có thể đến từ hai ảnh khác nhau. Quy tắc rút
> ra: **giải hệ trên từng ảnh, trong cùng một phạm vi đo.**

### 1.4 Bảng $\lambda$ của PicoRV32 — **hiệu chuẩn**, không đọc được từ RTL

PicoRV32 chạy trên bus 2 chu kỳ của `feasibility/F5_soc/soc.v`, nên số chu kỳ mỗi lệnh không đọc trực
tiếp ra được từ mã. Hiệu chuẩn bằng bình phương tối thiểu trên **số đã đo**: với mỗi (cấu hình, ảnh, lớp
mạng), $\sum_c n_c\lambda_c = C_{\text{Verilator}}$ — **6 cấu hình × 10 ảnh × 5 lớp = 300 phương trình**,
$n_c$ do ISS đếm chính xác. Lệnh: `./cdp iss --calibrate picorv32`.

| lớp lệnh | $\lambda$ **[hiệu chuẩn]** | số lệnh trong hệ | giải thích tự nhất quán |
|---|---:|---:|---|
| alu | **5** | 17.043.172 | 3 chu kỳ lệnh + **2 chu kỳ bus nạp lệnh** |
| shift | **5** | 3.332.220 | **= alu** ⟹ đúng với `BARREL_SHIFTER=1` |
| branch không nhảy | **5** | 690.802 | như alu |
| branch nhảy | **9** | 2.503.998 | + 4: nạp lệnh bị hủy rồi nạp lại đích |
| jal | **5** | 60 | 3 + 2 |
| jalr | **8** | 640 | 6 + 2 |
| load | **9** | 11.465.680 | 5 + 2 (nạp lệnh) + 2 (truy cập dữ liệu) |
| store | **9** | 708.120 | như load |
| mul | **6** | 5.549.640 | 4 + 2 ⟹ đúng với `ENABLE_FAST_MUL=1` |
| csr (`rdcycle`) | **5** | 300 | 3 + 2 |
| DOT4 (qua PCPI) | **6** | 1.758.400 | alu + 1 chu kỳ bắt tay PCPI |
| REQ (qua PCPI) | **6** | 73.440 | như DOT4 |
| div | — | 0 | không xuất hiện (firmware không chia) |

**Phần dư của phép khớp: đúng 0 trên cả 300 phương trình**, với $\lambda$ **nguyên**. Nghĩa là PicoRV32 +
bus 2 chu kỳ **cũng** là một máy có $\lambda$ cố định theo lớp lệnh: mô hình ở mục 1 đúng cho cả hai lõi,
chỉ khác là với PicoRV32 ta phải *đo ra* $\lambda$ thay vì *đọc ra*.

Ba điểm đáng chú ý về phương pháp:

1. **Phép hiệu chuẩn tự tìm lại tham số RTL mà nó không được cho biết.** $\lambda_{\text{shift}} =
   \lambda_{\text{alu}}$ ứng với `BARREL_SHIFTER=1`, và $\lambda_{\text{mul}}=6$ ứng với
   `ENABLE_FAST_MUL=1` — hai tham số nằm ở `feasibility/F5_soc/soc.v` dòng 85 và 88. Nếu $\lambda$ chỉ là
   tham số khớp vô nghĩa thì không có lý do gì chúng rơi vào đúng các giá trị đó.
2. **Mọi $\lambda$ đều có dạng "chu kỳ lệnh + 2 chu kỳ mỗi lần dùng bus".** Cột bên phải trong bảng là
   cách đọc nhất quán duy nhất, và nó khớp với mô tả bus 2 chu kỳ trong `soc.v`. Chênh lệch giữa
   $\lambda_{\text{load}}=9$ và $\lambda_{\text{alu}}=5$ đúng bằng 4 = hai lần giá bus — đây chính là
   chỗ 84,9 % chu kỳ của A-V0 biến mất (mục 1.2).
3. **Một chiều suy biến, và đã được gỡ bằng điều kiện nguyên.** Mọi cửa sổ đo chỉ có hai mẫu lệnh nhảy:
   $(n_{\text{jal}},n_{\text{jalr}},n_{\text{csr}})=(0,2,1)$ cho bốn lớp thường, và $(3,4,1)$ cho `conv1`
   của biến thể C1 (vì nó gọi thêm `conv1_prep`). Hai mẫu, ba ẩn ⟹ hệ chỉ cho

   $$\lambda_{\text{csr}} + 2\lambda_{\text{jalr}} = 21, \qquad 3\lambda_{\text{jal}} + 2\lambda_{\text{jalr}} = 31$$

   còn lại **một chiều tự do**. Vì $\lambda$ là số chu kỳ nên phải **nguyên và không âm**: điều kiện đó để
   lại đúng ba nghiệm — $(\lambda_{\text{jal}},\lambda_{\text{jalr}},\lambda_{\text{csr}})$ = (5, 8, 5),
   (7, 5, 11), (9, 2, 17). `cdp` chọn nghiệm **chuẩn nhỏ nhất** là (5, 8, 5), và đó cũng là nghiệm duy nhất
   đọc được tự nhiên theo quy luật "chu kỳ lệnh + 2 chu kỳ bus" ở điểm 2. Vẫn phải ghi rõ: **đây là một
   lựa chọn, không phải một phép đo**. Muốn chốt hẳn thì cần một phép đo vi mô có tỷ lệ
   `jal`/`jalr`/`rdcycle` khác.

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

> **Các công thức L1/L2 ở trên KHÔNG phải chặn dưới thật của lợi ích.** Chúng giả định vòng lặp sau
> khi viết lại chỉ còn đúng các lệnh tính toán trong mẫu, không phát sinh thêm lệnh địa chỉ và điều
> khiển vòng. Giả định đó đã bị **bác bỏ bằng số đo**: PMAX4 dự báo mức B 316.695 chu kỳ (1,1557×),
> đo thật trên kit **317.878** (1,1514×) — lợi ích thật **thấp hơn** "chặn dưới" 0,37 %
> (`results/pipeline/S6/kit/README.md`). Vì vậy từ đây gọi chúng là **ước lượng có điều kiện**, và mỗi
> dự báo phải ghi kèm điều kiện. Chỉ hai chặn dưới đây là tuyệt đối:

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
| K2 | dự báo của $\Delta C=\sum n_c\Delta\lambda_c$ cho một thay đổi L3 so với đo thật | S7 — **ĐÃ CHẠY**: bộ nhớ hai cổng, dự báo 243.641 / đo 243.641, **sai số 0,00 %** |
| K3 | dự báo cho một **lệnh mới** (L1/L2) so với đo thật | S6 — **ĐÃ CHẠY**: PMAX4, dự báo 316.695 / đo 317.878, **sai số +0,37 %** |

Mọi dự báo ghi vào sổ cái **trước** khi hiện thực. Sai số dự báo là dữ liệu nghiên cứu, **không được sửa
lùi** (SPEC 0.3).

**Kết quả K2 (bộ nhớ hai cổng) — mức A đúng như nó tự nhận.** Dự báo đóng băng ở
`results/pipeline/S6/du_bao_BONHO2CONG_truoc_khi_hien_thuc.json` trước khi sửa `mycore.v`:
**243.641 chu kỳ (1,3047×)**. Đo bằng Verilator sau khi hiện thực: **243.641 chu kỳ**.
**Sai số 0,00 %**, và ISS khớp Verilator **tuyệt đối** từng lớp từng ảnh.

Vì sao mức A đúng tuyệt đối còn mức B lệch: ứng viên này **không sửa một dòng mã phần mềm
và không thêm lệnh nào**, nên `n_c` giữ nguyên **từng con số** (`instret` đo được giống hệt:
236.313) và `ΔC = Σ n_c·Δλ_c` là **đẳng thức**. Mức B thì buộc phải giả định mã viết lại gọn
tới đâu — giả định đó là chỗ sai số sinh ra.

**Nhưng mô hình này không thấy giá phần cứng, và lần này giá rất đắt.** Cùng một file RTL,
chỉ khác tham số: LUT4 **4.459 → 15.736** (×3,5; 75,9 % chip), Fmax 59,08 → 53,01 MHz.
Quy trách nhiệm bằng ba lần tổng hợp: bản thân bộ nhớ hai cổng chỉ +1.680 LUT, còn **+8.724
LUT là của riêng cổng ghi thứ hai** — vì tệp thanh ghi 32×32 một cổng ghi được map vào 32
khối `RAM16SDP4` (RAM phân tán), thêm cổng ghi thứ hai thì **không map được nữa** và rơi về
flip-flop cộng mux 32:1. Chi tiết: `results/pipeline/S7/README.md` mục 4.

Hệ quả cho lý thuyết: **mô hình λ dự báo chu kỳ chính xác tuyệt đối, và không nói gì về
diện tích.** So hiệu quả hai ứng viên đã hiện thực — PMAX4 tốn 9,8 LUT4 cho mỗi 1 % tăng
tốc, bộ nhớ hai cổng tốn 370 — **chênh 38 lần**. Đây đúng giới hạn số 2 đã ghi trước ở mục 6,
và nó vừa được đo thành con số.

**Kết quả K3 (PMAX4) và điều nó bác bỏ.** Dự báo đóng băng ở
`results/pipeline/S6/du_bao_PMAX4_truoc_khi_hien_thuc.json` trước khi sửa `mycore.v`:

| | chu kỳ | tăng tốc | được tôn trọng? |
|---|---:|---:|---|
| chặn trên Amdahl (mức C) | 314.561 | 1,1635× | **có** — 1,1514× < 1,1635× |
| dự báo mức B ("chặn dưới") | 316.695 | 1,1557× | **KHÔNG** — vi phạm 0,37 % |
| đo thật trên kit | **317.878** | **1,1514×** | |

Mô hình **đúng về độ lớn** (sai số 0,37 %) nhưng **sai về loại**: mức B không phải chặn dưới. Lợi ích
thật thấp hơn vì vòng pooling viết lại vẫn còn chi phí địa chỉ/điều khiển vòng. Điều kiện này đã được
ghi **trước** trong file dự báo (*"nếu trình biên dịch sinh thêm lệnh địa chỉ/vòng lặp thì lợi ích thấp
hơn"*) và nó chỉ **đúng hướng lệch** — nên ta biết **tại sao** lệch, không chỉ biết **là** lệch. Đây là
lý do SPEC 0.3 buộc ghi dự báo kèm giả định, không chỉ ghi con số.

---

## 6. Giới hạn — ghi trước, không chữa sau

1. **Không mô hình hoá Fmax.** Mọi so sánh là **số chu kỳ ở 27 MHz cố định**. Một ứng viên làm giảm Fmax
   xuống dưới 27 MHz bị loại bởi `cdp synth`, không bởi mô hình này.
2. **Không mô hình hoá chi phí LUT.** Bài học đã đo: hiệu hai lần tổng hợp chỉ đo được chi phí phần cứng
   khi RTL giống hệt nhau (S1 vừa cho một ví dụ: +20 LUT4 của B-V1 đến từ khối REQ đã tắt).
3. **Không có cache, không có dự đoán nhánh** trong thiết kế này — đó là lý do mô hình đếm lớp lệnh đủ
   chính xác để kỳ vọng khớp **tuyệt đối**. Mô hình này **không** chuyển sang lõi có cache mà không sửa.
4. **PicoRV32: $\lambda$ hiệu chuẩn, và còn một chiều suy biến đã phải chọn nghiệm.** Phần dư 0 nên
   *dạng* mô hình đúng, nhưng $\lambda_{\text{jal}}, \lambda_{\text{jalr}}, \lambda_{\text{csr}}$ chỉ xác
   định tới một chiều tự do (mục 1.4); `cdp` chọn nghiệm nguyên chuẩn nhỏ nhất. Dự báo cho ứng viên
   **đổi số lời gọi hàm** trên PicoRV32 vì vậy kém tin cậy hơn phần còn lại.
5. **Mục 1.3 giả định $n_{\text{div}}=0$** (firmware không dùng chia) và giả định cặp FA=1/FA=0 chạy đúng
   cùng một firmware — cả hai đã kiểm bằng `rdinstret` khớp tuyệt đối.
6. **Mô hình không tính chi phí địa chỉ và điều khiển vòng của mã viết lại.** Đã đo: PMAX4 lệch
   +0,37 % theo đúng hướng này (mục 5). Hệ quả: dự báo L1/L2 là **ước lượng**, và với mẫu càng nhỏ
   (ít lệnh tính toán trên mỗi lần lặp) thì phần chi phí chưa mô hình hoá càng chiếm tỷ trọng lớn,
   sai số càng tăng. Dự báo L3 (đổi $\lambda$) **không** chịu giới hạn này vì không sửa mã.
