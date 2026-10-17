# Kết quả thí nghiệm chính — M1-S trên lõi RISC-V, Tang Nano 20K

**Ngày**: 2026-10-17 · **Máy**: Mac Intel (x86_64, macOS 26.6.2) · **Kit**: Sipeed Tang Nano 20K
(GW2AR-LV18QN88C8/I7, 27 MHz) · **Xung nhịp thí nghiệm**: 27 MHz cố định

Đây là lần đầu **một mô hình CNN hoàn chỉnh đã huấn luyện** chạy suy luận trên lõi RISC-V mềm trong
FPGA, và đo được số chu kỳ. Giai đoạn khả thi (F0–F8) chỉ kiểm phần cứng và đường ống đo bằng dữ liệu
tổng hợp; tài liệu này là kết quả trên mô hình thật.

Mọi con số lấy từ output thật. Số liệu gốc: `results/experiment/m1s/m1s.csv`.

---

## 1. Mô hình

M1-S, huấn luyện bằng PyTorch trên MNIST (60.000 ảnh train), lượng tử hoá int8 sau huấn luyện.

| Lớp | Đầu ra | Tham số | MAC |
|---|---|---:|---:|
| Conv 3×3, 1→8 kênh, bias, ReLU, requantize | 26×26×8 | 80 | 48.672 |
| MaxPool 2×2 | 13×13×8 | 0 | 0 |
| Conv 3×3, 8→16 kênh, bias, ReLU, requantize | 11×11×16 | 1.168 | 139.392 |
| MaxPool 2×2 | 5×5×16 | 0 | 0 |
| Dense 400→10, bias, giữ int32 → argmax | 10 | 4.010 | 4.000 |
| **Tổng** | | **5.258 (5,3 KB int8)** | **192.064** |

**Độ chính xác trên 10.000 ảnh test MNIST**

| | Độ chính xác |
|---|---|
| float32 (PyTorch) | **98,29 %** |
| int8 (golden Python, đúng từng bit với firmware) | **98,25 %** |
| Chênh | **+0,04 điểm %** |

Tiêu chí trong kế hoạch là *"int8 kém float không quá 1 điểm %"* → **ĐẠT** với biên rất rộng.

**Lượng tử hoá**: đối xứng, zero-point = 0 ở mọi nơi. Trọng số int8 (`Sw = max|W|/127`), bias int32,
requantize kiểu gemmlowp bằng cặp `(M0, shift)` — lớp 1 `M0=1138411053, shift=8`, lớp 2
`M0=1108363094, shift=8`. Thang đo activation lấy từ hiệu chuẩn trên 512 ảnh train. Lớp Dense
**không** requantize: giữ int32 rồi `argmax` (thang đo dương nên argmax không đổi), nhờ vậy bỏ được
một cặp `(M0, shift)` và một lần làm tròn.

---

## 2. Năm biến thể đã đo — bảng 2×2 + một bước bố cục

Hai tối ưu **độc lập nhau**, bật/tắt bằng hai cờ biên dịch trên **cùng một file `main.c`**:

| | Không DOT4 | Có DOT4 (conv2 + dense) |
|---|---|---|
| **C thẳng** | **A-V0** | **A-V2** |
| **C đã tối ưu** (`OPT_KERNELS`) | **A-V1** | **A-V1+DOT4** |

Thêm một biến thể thứ năm: **A-V1+DOT4+C1** (`CONV1_DOT4`) — gỡ nút cổ chai conv1 bằng **bố cục dữ
liệu**, không thêm phần cứng. Xem mục 3.

Bảng 2×2 này là để trả lời câu hỏi mà bất kỳ phản biện nào cũng sẽ hỏi: *tăng tốc đến từ lệnh tùy
biến, hay chỉ từ việc viết code tốt hơn?*

**Tối ưu phần mềm trong A-V1** (không đổi một phép toán nào, CRC vẫn khớp từng bit):
- conv1: đưa vòng kênh ra ra **ngoài** nên 9 trọng số + bias nằm trong thanh ghi suốt cả mặt 26×26;
  9 phép nhân dùng **offset hằng số** từ một con trỏ hàng duy nhất; con trỏ ra chạy đều bước 8 byte.
- conv2: **bung hết 9 vị trí kernel** bằng offset hằng số từ một con trỏ gốc (bước hàng của `p1` là
  13×8 = 104 byte), mỗi vị trí gọi một macro cộng dồn 8 kênh vào.
- dense: bung vòng trong theo bước 8.

**Vì sao conv1 không dùng DOT4**: `DOT4` nạp 4 byte liền nhau bằng `lw` nên **cần địa chỉ thẳng hàng
4 byte** (lõi bật `CATCH_MISALIGN`). Với bố cục channels-last, conv2 có `Cin=8` nên 4 kênh vào liền
nhau luôn thẳng hàng; conv1 có `Cin=1` nên không có 4 giá trị liền nhau để cộng dồn mà vẫn thẳng hàng.

**Vì sao conv1 không dùng DOT4**: `DOT4` nạp 4 byte liền nhau bằng `lw` nên **cần địa chỉ thẳng hàng
4 byte** (lõi bật `CATCH_MISALIGN`). Với bố cục channels-last, conv2 có `Cin=8` nên 4 kênh vào liền
nhau luôn thẳng hàng; conv1 có `Cin=1` nên không có 4 giá trị liền nhau để cộng dồn mà vẫn thẳng hàng.
conv1 chiếm 48.672/192.064 = **25,3 % số MAC** nhưng **28,8 % thời gian** của A-V0.

---

## 3. Số đo trên kit (trung vị trên 10 ảnh, 27 MHz)

| Lớp | MAC | A-V0 | A-V1 | A-V2 | A-V1+DOT4 | **A-V1+DOT4+C1** |
|---|---:|---:|---:|---:|---:|---:|
| conv1 | 48.672 | 3.491.721 | 1.600.258 | 3.491.721 | 1.600.258 | **1.133.668** |
| pool1 | — | 225.600 | 225.600 | 225.600 | 225.600 | 225.600 |
| conv2 | 139.392 | 8.153.979 | 4.199.609 | 1.924.815 | 986.226 | 986.226 |
| pool2 | — | 65.921 | 65.921 | 65.921 | 65.921 | 65.921 |
| dense | 4.000 | 192.552 | 126.224 | 48.552 | 39.052 | 39.057 |
| **TỔNG** | **192.064** | **12.129.818** | **6.217.657** | **5.756.654** | **2.917.102** | **2.450.517** |
| Số lệnh | | 1.864.264 | 911.920 | 912.832 | 460.794 | **391.278** |
| **Thời gian @27 MHz** | | **449,3 ms** | **230,3 ms** | **213,2 ms** | **108,0 ms** | **90,8 ms** |
| chu kỳ/MAC | | 63,16 | 32,37 | 29,97 | 15,19 | **12,76** |
| Ảnh/giây | | 2,23 | 4,34 | 4,69 | 9,26 | **11,02** |
| **Tăng tốc so A-V0** | | 1,00× | **1,95×** | **2,11×** | **4,16×** | **4,95×** |

### Kết quả quan trọng nhất: hai tối ưu gần như nhân được với nhau

| Nguồn tăng tốc | Hệ số |
|---|---|
| Tối ưu phần mềm một mình (A-V0 → A-V1) | **1,95×** |
| DOT4 trên C thẳng (A-V0 → A-V2) | **2,11×** |
| **DOT4 thêm vào C đã tối ưu** (A-V1 → A-V1+DOT4) | **2,13×** |
| Cả hai (A-V0 → A-V1+DOT4) | **4,16×** |
| Tích của hai hệ số riêng | 1,95 × 2,13 = **4,16×** |
| **+ phủ DOT4 cho conv1 bằng bố cục** (→ A-V1+DOT4+C1) | **4,95×** |

Tích đúng bằng số đo. Nghĩa là **lợi ích của lệnh tùy biến không biến mất khi phần mềm đã được tối
ưu** (2,13× so với 2,11×) — đây là câu trả lời cho phản biện "tăng tốc chỉ nhờ baseline code kém".
Hai tối ưu tác động vào hai thứ khác nhau: tối ưu phần mềm bỏ phần **tính chỉ số**, DOT4 bỏ phần
**nhân-cộng**.

### Gỡ nút cổ chai conv1 bằng bố cục, không thêm phần cứng (A-V1+DOT4+C1)

Ở A-V1+DOT4, conv1 chiếm 54,9 % thời gian và **không dùng được DOT4** vì `Cin=1`: không có 4 giá trị
int8 liền nhau mà địa chỉ lại thẳng hàng 4 byte. Cách gỡ **không cần lệnh mới nào**:

- Tạo **4 bản sao ảnh dịch 0/1/2/3 byte**, mỗi hàng đệm lên 32 byte:
  `ph[p][y][j] = img[y][j − p]`. Khi đó `img[y][x]` nằm ở offset `x + p`, nên chọn
  `p = (−x) & 3` thì địa chỉ luôn chia hết 4. Với `x ≤ 25`, offset đọc xa nhất là 31 < 32 nên không
  tràn hàng.
- Trọng số nhân bản thành nhóm 4 với **tap thứ 4 = 0**. Phép toán không đổi (nhân 0), nên CRC vẫn
  khớp golden từng bit.
- conv1 còn **3 lệnh DOT4** cho 3 hàng thay vì 9 phép nhân vô hướng.
- Chi phí: **3.584 byte `.bss`** cho 4 bộ đệm + **3.136 byte sao chép mỗi ảnh**.

Kết quả: conv1 **1.600.258 → 1.133.668** chu kỳ (1,41×), tổng **2.917.102 → 2.450.517** (1,19×),
đưa tăng tốc tích luỹ lên **4,95×**. conv1 từ 32,88 xuống **23,29 chu kỳ/MAC**.

### Chu kỳ/MAC từng lớp
| Lớp | A-V0 | A-V1 | A-V2 | A-V1+DOT4 | A-V1+DOT4+C1 |
|---|---:|---:|---:|---:|---:|
| conv1 (Cin=1) | 71,74 | 32,88 | 71,74 | 32,88 | **23,29** |
| conv2 (Cin=8) | 58,50 | 30,13 | 13,81 | **7,08** | 7,08 |
| dense | 48,14 | 31,56 | 12,14 | **9,76** | 9,76 |

### Chi phí của requantize — đo trực tiếp
Hai vòng lặp giống hệt nhau, khác đúng một thứ (requantize so với chỉ `clamp`), toán hạng phụ thuộc
biến đếm để trình biên dịch không nhấc ra ngoài vòng:

| | 20.000 lần |
|---|---:|
| vòng có requantize | 1.671.265 chu kỳ |
| vòng chỉ clamp | 680.007 chu kỳ |
| **requantize** | **49,6 chu kỳ/lần** |

Mỗi ảnh cần requantize **7.344 giá trị** (conv1 5.408 + conv2 1.936) → **363.990 chu kỳ = 14,9 %**
thời gian của A-V1+DOT4+C1. Nếu một lệnh `REQ` làm requantize trong ~1 chu kỳ thì tiết kiệm
~356.600 chu kỳ → **~78 ms, thêm 1,17×**. Đây là cơ sở định lượng cho lệnh REQ trong kế hoạch,
và nó cho thấy REQ đáng làm nhưng **không phải đòn lớn nhất còn lại**.

### Tính đúng đắn — điều kiện để ghi nhận số đo
Cả **năm** biến thể, lặp lại 2/2 lần đọc độc lập mỗi biến thể:

| Kiểm tra | Kết quả |
|---|---|
| CRC32 từng lớp (a1, p1, a2, p2, logit) trên kit = golden Python | **250/250 khớp** (5 lớp × 10 ảnh × 5 biến thể) |
| Dự đoán trên kit = dự đoán golden | **50/50** |
| Dự đoán trên kit = nhãn thật | **50/50** |
| Số chu kỳ trên kit = số chu kỳ trong Verilator | **bằng tuyệt đối**, cả 7 cột × 10 ảnh × 5 biến thể |

`conv1`, `pool1`, `pool2` cho **đúng cùng số chu kỳ** ở A-V0/A-V2 và ở A-V1/A-V1+DOT4 — bằng chứng
rằng mỗi cặp so sánh chỉ khác đúng một thứ. (Ngoại lệ nhỏ: `dense` ở A-V1+DOT4+C1 là 39.057 so với
39.052, lệch 5 chu kỳ, vì bản này còn biên dịch thêm phần đo requantize làm mã `dense` dài thêm
4 byte. Đã kiểm `conv2`, `pool1`, `pool2` có kích thước mã giống hệt.)

## 4. Tài nguyên FPGA

| Thiết kế | LUT4 | DFF | BSRAM | MULT18X18 | Fmax (MHz) |
|---|---:|---:|---:|---:|---:|
| A-V0, A-V1 (không DOT4) | 7.941 (38,3 %) | 1.069 | 32/46 | 0 | 71,76 |
| A-V2, A-V1+DOT4, A-V1+DOT4+C1 (có DOT4) | 8.065 (38,9 %) | 1.153 | 32/46 | 4/48 | 71,89 |
| **Chi phí của DOT4** | **+124 (+1,6 %)** | +84 | 0 | +4 | **+0,13** |

Ba biến thể có DOT4 dùng **cùng một bitstream về mặt phần cứng** — chỉ khác nội dung firmware trong
BSRAM. Tương tự A-V0 và A-V1. Nghĩa là: **toàn bộ 1,95× của A-V1 và 1,19× của bước +C1 là miễn phí
về phần cứng**; chỉ 2,13× của DOT4 phải trả **+124 LUT4 (+1,6 %)** và **không giảm Fmax**.
Biên Fmax so với 27 MHz vẫn là **2,66 lần**.

**Bộ nhớ** (RAM 65.536 byte): A-V0 27.592 (42,1 %) · A-V1 29.272 (44,7 %) · A-V2 27.488 (41,9 %) ·
A-V1+DOT4 27.792 (42,4 %) · A-V1+DOT4+C1 **32.368 (49,4 %)**. Bản +C1 tốn thêm 3.584 byte cho
4 bộ đệm pha dịch và ~1,2 KB `.text`. Còn dư ≥33 KB ở mọi biến thể.

## 5. Nhận xét

**1. Hai hướng tối ưu độc lập và nhân được với nhau.** 1,95× (phần mềm) × 2,13× (lệnh tùy biến) =
4,16× = đúng số đo. Lý do: chúng cắt hai phần khác nhau của chi phí. Tối ưu phần mềm bỏ phần tính
chỉ số (thấy rõ ở conv1: 71,74 → 32,88 chu kỳ/MAC mà không có lệnh mới nào); DOT4 bỏ phần nhân-cộng
(conv2: 30,13 → 7,08 chu kỳ/MAC trên nền đã tối ưu). **Đây là kết quả đáng giá nhất của thí nghiệm**:
nó bảo vệ kết luận khỏi phản biện "baseline code kém".

**2. Nút cổ chai conv1 gỡ được bằng BỐ CỤC, không cần phần cứng mới.** Ở A-V1+DOT4, conv1 chiếm
54,9 % thời gian và bị chặn bởi yêu cầu thẳng hàng 4 byte của `DOT4`. Bốn bản sao ảnh dịch
0/1/2/3 byte (3.584 byte `.bss`) gỡ được hạn chế đó và cho thêm **1,19×**, đưa tổng lên **4,95×**
(mục 3). → **Giới hạn của một lệnh tùy biến có thể nằm ở bố cục dữ liệu chứ không ở bản thân lệnh.**
Đây là kết luận đáng đưa vào luận văn: trước khi thiết kế thêm phần cứng, hãy kiểm xem bố cục đã cho
lệnh hiện có dùng hết chưa.

Sau bước đó, conv1 vẫn là lớp tốn nhất (1.133.668 chu kỳ = 46,3 % tổng) vì mỗi giá trị đầu ra chỉ có
9 MAC để chia sẻ chi phí cố định (requantize, lưu kết quả, vòng lặp), còn conv2 có 72 MAC mỗi giá trị
đầu ra. Đó là lý do conv1 đạt 23,29 chu kỳ/MAC trong khi conv2 đạt 7,08.

**3. Ước tính ở F7 khá sát.** F7 ngoại suy từ chu kỳ/MAC của conv1 ra **≈516 ms** cho M1-S. Số đo thật
của A-V0 là **449,3 ms** — ước tính **cao hơn 15 %**, lệch theo hướng an toàn, và đúng lý do F7 đã nêu:
conv2 có `Cin=8` nên chi phí/MAC *thấp hơn* conv1 (58,50 so với 71,74) do chia sẻ được phần tính chỉ số.

**4. Một cái bẫy của trình biên dịch, không liên quan tới phần cứng.** Ban đầu 5 lớp là hàm `static`
gọi một lần, GCC `-O2` nội suy hết vào `main`; cấp phát thanh ghi tràn làm A-V0 chạy **21.350.804**
chu kỳ. Thêm `__attribute__((noinline))` cho mỗi lớp đưa về **12.129.818** chu kỳ — **nhanh hơn 1,76×
mà không đổi một dòng thuật toán**. Tệ hơn: khi chưa có `noinline`, cấp phát thanh ghi của conv1
*thay đổi theo* việc conv2 có dùng DOT4 hay không (3.803.170 so với 4.950.316 chu kỳ), làm phép so
sánh mất ý nghĩa. → **Quy tắc phương pháp: khi so hai biến thể tập lệnh, phải cố định ranh giới hàm,
và phải kiểm rằng các lớp KHÔNG thay đổi cho ra ĐÚNG số chu kỳ cũ.** (Kiểm này đã đưa vào
`scripts/m1s_check.py` một cách gián tiếp: nó so từng cột chu kỳ với Verilator, nên mọi thay đổi
ngoài ý muốn đều lộ ra.)

**5. Một bài học vận hành.** Lần đo đầu, script báo *"kit báo biến thể A-V2, mong đợi A-V0"* — hoá ra
tôi đã khởi động vòng đo thứ hai khi vòng đầu còn đang nạp kit, nên hai tiến trình tranh nhau cùng
một kit. Phép kiểm nhãn biến thể trong mỗi khối dữ liệu đã chặn được một số đo sai. → **Mỗi khối số
đo nên tự khai báo nó thuộc biến thể nào**; chi phí gần như bằng không mà chặn được loại lỗi khó thấy
nhất.

**6. Lệnh REQ: đã định lượng được giá trị, và nó không lớn.** Đo trực tiếp: requantize tốn
**49,6 chu kỳ/lần**, mỗi ảnh cần 7.344 lần → **14,9 %** thời gian của biến thể nhanh nhất. Một lệnh
`REQ` làm việc đó trong ~1 chu kỳ sẽ cho thêm **~1,17×** (90,8 → ~78 ms). Đáng làm, nhưng nhỏ hơn
nhiều so với DOT4 (2,13×). **Đòn lớn hơn còn lại là giảm số lệnh trên mỗi giá trị đầu ra của conv1**
— ví dụ tính nhiều kênh ra cùng lúc để dùng lại 3 từ ảnh đã nạp, hoặc một lệnh nhân-cộng rộng hơn.

**7. Những gì phần này chưa làm.** Chỉ đo 10 ảnh trên kit (độ chính xác 98,25 % là của golden Python
trên đủ 10.000 ảnh, không phải của kit trên 10.000 ảnh). Chưa hiện thực **REQ**. Chưa làm **nhánh B**
(lõi tự viết). Chưa đo công suất.

## 6. Cách chạy lại

```bash
source env/setup_env.sh

# 1. Huấn luyện + lượng tử hoá (chỉ cần Python, không cần kit; venv riêng có PyTorch)
cd model && ../.venv-model/bin/python train_m1s.py      # ~35 s, in độ chính xác float
../.venv-model/bin/python quantize_m1s.py               # ~90 s, sinh fw/weights.h

# 2. Năm biến thể. Mỗi biến thể cần bitstream riêng vì firmware nằm trong nội dung
#    khởi tạo BSRAM. Build mất ~5 phút mỗi bản.
cd ../experiment/m1s
for v in v0 v1 v2 v1d v1dc; do make fw-$v sim-$v build-$v; done
# Nạp và đo TUẦN TỰ — đừng chạy song song, hai tiến trình sẽ tranh nhau cùng một kit:
for v in v0 v1 v2 v1d v1dc; do make load-$v check-$v; done
make archive
```

| Thư mục | Biến thể | Cờ biên dịch |
|---|---|---|
| `v0/` | A-V0 | (không) |
| `v1/` | A-V1 | `-DOPT_KERNELS` |
| `v2/` | A-V2 | `-DUSE_DOT4` |
| `v1d/` | A-V1+DOT4 | `-DOPT_KERNELS -DUSE_DOT4` |
| `v1dc/` | A-V1+DOT4+C1 | `-DOPT_KERNELS -DUSE_DOT4 -DCONV1_DOT4 -DREQ_BENCH` |

PyTorch nằm trong venv riêng `.venv-model` (Python 3.12 + torch 2.2.2 + numpy 1.26.4): Python 3.14
của `.venv` chính **không có** wheel torch cho macOS x86_64, và torch 2.2.2 là bản cuối còn wheel cho
nền tảng này — nó lại cần numpy < 2. Chi tiết trong `env/VERSIONS.md`.
