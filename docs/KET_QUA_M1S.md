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

| | Độ chính xác | Đo ở đâu |
|---|---|---|
| float32 (PyTorch) | **98,29 %** | máy chủ |
| int8 (golden Python, đúng từng bit với firmware) | **98,25 %** | máy chủ |
| **int8 ĐO TRỰC TIẾP TRÊN KIT** | **98,25 %** (9.825/10.000) | **kit, đủ 10.000 ảnh** |
| Chênh float → int8 | **+0,04 điểm %** | |

Dòng thứ ba là số **đo trên phần cứng**, không phải suy ra: cả 10.000 ảnh test đều được nạp vào kit
qua UART và kit tự suy luận. Xem mục 5.

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
| conv2 | 139.392 | 5.011.844 | 4.199.609 | 1.926.185 | 986.226 | 986.226 |
| pool2 | — | 65.921 | 65.921 | 65.921 | 65.921 | 65.921 |
| dense | 4.000 | 192.552 | 126.224 | 48.552 | 39.052 | 39.057 |
| **TỔNG** | **192.064** | **8.987.660** | **6.217.634** | **5.758.001** | **2.917.079** | **2.450.494** |
| Số lệnh | | 1.358.200 | 911.920 | 913.105 | 460.793 | **391.278** |
| **Thời gian @27 MHz** | | **332,9 ms** | **230,3 ms** | **213,3 ms** | **108,0 ms** | **90,8 ms** |
| chu kỳ/MAC | | 46,80 | 32,37 | 29,98 | 15,19 | **12,76** |
| Ảnh/giây | | 3,00 | 4,34 | 4,69 | 9,26 | **11,02** |
| IPC | | 0,151 | 0,147 | 0,159 | 0,158 | **0,160** |
| **Tăng tốc so A-V0** | | 1,00× | **1,45×** | **1,56×** | **3,08×** | **3,67×** |

Mọi số trong bảng đo trên kit, **cùng một trạng thái mã nguồn** (`SRC_HASH = 647f1d071aca`), mỗi biến
thể 2/2 lần đọc độc lập đạt. Xem mục 3c về việc vì sao điều kiện "cùng một trạng thái mã nguồn" phải
được kiểm bằng máy.

### Kết quả quan trọng nhất: lệnh tùy biến cho lợi ÍCH LỚN HƠN khi phần mềm đã tối ưu

| Phép so | Hệ số |
|---|---|
| Tối ưu phần mềm một mình (A-V0 → A-V1) | **1,4455×** |
| **DOT4 trên C thẳng** (A-V0 → A-V2) | **1,5609×** |
| **DOT4 thêm vào C đã tối ưu** (A-V1 → A-V1+DOT4) | **2,1315×** |
| Cả hai (A-V0 → A-V1+DOT4), đo trực tiếp | **3,0810×** |
| Tích 1,4455 × 2,1315 | **3,0810×** |
| + phủ DOT4 cho conv1 bằng bố cục (→ A-V1+DOT4+C1) | **3,6676×** |

Hai điều cần tách riêng, vì chúng hay bị nhập làm một:

**(a) Phân rã theo chuỗi thì luôn khớp tuyệt đối** — 1,4455 × 2,1315 = 3,0810, đúng bằng số đo tới
bốn chữ số thập phân. Nhưng điều này **đúng do định nghĩa**: đó là cùng một con đường A-V0 → A-V1 →
A-V1+DOT4 viết thành hai chặng. Nó xác nhận phép đo nhất quán, không phải một phát hiện.

**(b) Phép thử ĐỘC LẬP thì KHÔNG khớp — và đó mới là phát hiện.** Nếu hai tối ưu độc lập nhau thì
DOT4 phải cho cùng một hệ số bất kể phần mềm đã tối ưu hay chưa. Thực đo:

| DOT4 thêm vào | Hệ số |
|---|---|
| C thẳng (A-V0 → A-V2) | 1,5609× |
| C đã tối ưu (A-V1 → A-V1+DOT4) | **2,1315×** |

→ **DOT4 cho lợi ích gấp 1,37 lần khi phần mềm đã được tối ưu trước.** Hai tối ưu **không độc lập**,
và tương tác giữa chúng là **thuận lợi**.

Lý do, đọc được từ chính số liệu: ở C thẳng, `conv2` tốn 5.011.844 chu kỳ cho 139.392 MAC (35,95
chu kỳ/MAC) mà phần lớn là **tính chỉ số** chứ không phải nhân-cộng; DOT4 chỉ cắt phần nhân-cộng, nên
chỉ cắt được một *phân số nhỏ*. Sau khi tối ưu phần mềm, `conv2` còn 30,13 chu kỳ/MAC và phần
nhân-cộng mới chiếm tỷ trọng lớn — lúc đó DOT4 cắt được nhiều hơn.

**Hệ quả cho phương pháp thiết kế đồng thời (co-design): thứ tự có ý nghĩa.** Đo một lệnh tùy biến
trên mã nguồn chưa tối ưu sẽ **đánh giá THẤP** giá trị của nó (1,56× thay vì 2,13×). Đây cũng là câu
trả lời cho phản biện "tăng tốc chỉ nhờ baseline code kém": với baseline *đã tối ưu*, DOT4 vẫn cho
2,13× — cao hơn khi đo trên baseline kém.

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

Kết quả: conv1 **1.600.258 → 1.133.668** chu kỳ (1,41×), tổng **2.917.079 → 2.450.494** (1,19×),
đưa tăng tốc tích luỹ lên **3,67×**. conv1 từ 32,88 xuống **23,29 chu kỳ/MAC**.

### Chu kỳ/MAC từng lớp
| Lớp | A-V0 | A-V1 | A-V2 | A-V1+DOT4 | A-V1+DOT4+C1 |
|---|---:|---:|---:|---:|---:|
| conv1 (Cin=1) | 71,74 | 32,88 | 71,74 | 32,88 | **23,29** |
| conv2 (Cin=8) | 35,95 | 30,13 | 13,82 | **7,08** | 7,08 |
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

## 3b. Chạy đủ 10.000 ảnh trên kit — bỏ giả định "10 ảnh là đủ"

Năm biến thể ở mục 3 chỉ chạy **10 ảnh nhúng sẵn trong firmware** (RAM 64 KB không chứa nổi 10.000
ảnh = 7,84 MB). Nên con số 98,25 % cho tới lúc này là của **golden Python**, còn kit chỉ được kiểm
trên 10 ảnh. Đây là lỗ hổng duy nhất còn lại của chương này, và nó đã được bịt.

### Cách làm: nạp ảnh qua UART (chế độ `STREAM_10K`)
Khung truyền: **1 byte đồng bộ `0xA5` + 784 byte ảnh int8**, host gửi theo khối 64 byte (bài học F2:
ghi ≥ 67 byte một lần làm mất byte ở phía host). Hai tính chất làm giao thức tự lành:

- Pixel lượng tử hoá nằm trong **[0, 127]** nên **không bao giờ** trùng `0xA5`. Mất byte thì kit quét
  tiếp và tự đồng bộ lại ở khung sau; host gửi lại tối đa 3 lần.
- **Kit mời thì host mới gửi**: chỉ gửi sau khi nhận được một dòng hoàn chỉnh từ kit. Thanh ghi thu
  chỉ giữ **một** byte (không FIFO), nên gửi lúc kit đang bận là mất sạch.

Kit báo thêm **CRC32 của chính 784 byte nó nhận được**, nhờ vậy phân biệt được *lỗi đường truyền*
với *lỗi tính toán* — nếu trộn hai thứ này thì không kết luận được gì.

### Mã tính toán KHÔNG đổi so với bản đã kiểm
`scripts/cmp_layers.py` so mã máy từng hàm giữa `v1dc` (đã kiểm kit = Verilator) và `v10k`:

| hàm | byte | lệnh y hệt (bỏ địa chỉ tuyệt đối) |
|---|---:|---|
| `conv1` | 452 = 452 | CÓ |
| `conv1_prep` | 248 = 248 | CÓ |
| `pool1` | 276 = 276 | CÓ |
| `conv2` | 644 = 644 | CÓ |
| `pool2` | 260 = 260 | CÓ |
| `dense` | 124 = 124 | CÓ |

Chỉ khác giá trị địa chỉ tuyệt đối (bố cục `.bss` dịch vì bỏ 10 ảnh nhúng, thêm `img_buf`). Tài nguyên
FPGA **giống hệt** `v1dc`: LUT4 8.065, 4 MULT18X18, Fmax 71,89 MHz.

### Kết quả (30,0 phút chạy liên tục, 27 MHz)

| Phép kiểm | Kết quả |
|---|---|
| Khung nhận đúng | **10.000/10.000** · thất bại 0 · gửi lại **0 lần** · CRC ảnh lệch **0** |
| **CRC32 logit = golden Python** | **10.000/10.000 (100,00 %)** |
| Dự đoán trên kit = dự đoán golden | **10.000/10.000** |
| **ĐỘ CHÍNH XÁC ĐO TRÊN KIT** | **9.825/10.000 = 98,25 %** |

Bằng nhau **tuyệt đối** với golden Python: 98,25 % không còn là số suy ra mà là số đo.
0 lần gửi lại trên 7,85 MB truyền qua UART cũng xác nhận lại kết luận F2 (đường truyền sạch).

### Phân bố chu kỳ trên 10.000 ảnh — lớp nào tất định, lớp nào không

| lớp | trung vị | nhỏ nhất | lớn nhất | biên độ | độ lệch chuẩn |
|---|---:|---:|---:|---:|---:|
| conv1 | 1.133.673 | 1.133.673 | 1.133.673 | **0** | 0,0 |
| pool1 | 225.617 | 225.334 | 225.894 | 560 | 97,2 |
| conv2 | 986.226 | 986.226 | 986.228 | 2 | 0,0 |
| pool2 | 65.915 | 65.759 | 65.993 | 234 | 39,5 |
| dense | 39.057 | 39.057 | 39.057 | **0** | 0,0 |
| **TỔNG** | **2.450.490** | 2.450.049 | 2.450.814 | **765** | 133,1 |

- `conv1` và `dense` **tất định tuyệt đối** trên cả 10.000 ảnh — biên độ 0 chu kỳ.
- `pool1`/`pool2` **phụ thuộc dữ liệu** (biên độ 560 và 234) vì maxpool rẽ nhánh theo phép so sánh.
  Trước đây chúng được ghi là hằng số 225.600 / 65.921; điều đó đúng với 10 ảnh cố định nhưng
  **không phải vì lớp đó tất định** — chỉ số đo trên 10.000 ảnh mới nói được.
- `conv2` lệch tối đa **2 chu kỳ** (ReLU rẽ nhánh), gần như tất định.
- Toàn bộ biên độ là **765 chu kỳ = 0,031 %** của 2,45 triệu. Thời gian mỗi ảnh nằm trong
  **90,74 – 90,77 ms**. Nói cách khác: suy luận trên lõi mềm này **đúng thời gian thực cứng**, dao
  động chưa tới 0,3 phần nghìn — một tính chất thực tế quan trọng mà 10 ảnh không thể chứng minh.
- IPC = **0,160** (391.268 lệnh / 2.450.490 chu kỳ): PicoRV32 không pipeline, mỗi lệnh nhiều chu kỳ,
  và bus RAM 2 chu kỳ mỗi truy cập. Đây mới là lý do gốc khiến còn nhiều chu kỳ/MAC, và nó chỉ về
  **nhánh B** (lõi tự viết) chứ không về thêm lệnh tùy biến.

### Các cặp nhầm lẫn nhiều nhất (175 ảnh sai)
`4→9` 14 lần · `6→0` 11 · `7→2` 11 · `8→0` 10 · `7→9` 8 · `6→5` 6 · `2→7` 5 · `5→3` 5 · `8→9` 5 ·
`3→2` 5. Phân bố này giống đặc trưng quen thuộc của CNN nhỏ trên MNIST (4/9, 7/9, 3/5/8), và vì kit
khớp golden 10.000/10.000 nên **toàn bộ 175 lỗi là của mô hình, không phải của phần cứng**.

Vật phẩm: `results/experiment/m1s/m1s_10k.csv` (10.000 dòng, 14 cột) · `results/experiment/m1s/v10k/`.

## 3c. Một sai số đã phát hiện và sửa — và cách chặn để không lặp lại

Mục này ghi lại một lỗi thật trong chính số liệu của tài liệu này, vì cách phát hiện nó có giá trị
phương pháp.

**Lỗi.** A-V0 và A-V2 ban đầu được đo bằng một bản `main.c` **chưa commit**. Sau đó, khi thêm biến thể
A-V1, phần `conv2` *bản thẳng* được viết lại (dùng macro `MAC8` và con trỏ chạy) và trở nên nhanh hơn
— nhưng **A-V0 và A-V2 không được đo lại**. Hệ quả: baseline chậm hơn thực tế, nên **mọi tỷ số tăng
tốc so với A-V0 đều bị phóng đại**.

| | Đã công bố (sai) | Đo lại (đúng) |
|---|---:|---:|
| A-V0, conv2 | 8.153.979 | **5.011.844** |
| A-V0, tổng | 12.129.818 | **8.987.660** |
| A-V0, số lệnh | 1.864.264 | **1.358.200** |
| A-V2, conv2 | 1.924.815 | **1.926.185** |
| Tăng tốc A-V0 → A-V1 | 1,95× | **1,45×** |
| Tăng tốc A-V0 → A-V2 | 2,11× | **1,56×** |
| Tăng tốc A-V0 → A-V1+DOT4+C1 | 4,95× | **3,67×** |

**Cách phát hiện.** Không phải bằng rà soát tay. Khi chuyển sang nhánh B (lõi tự viết), tôi đặt ra một
điều kiện: *chạy cùng một file `firmware.hex` trên hai lõi thì `rdinstret` phải bằng nhau tuyệt đối*,
vì cùng mã máy thì cùng số lệnh. Lõi mới báo 1.358.178 còn số A-V0 đã công bố là 1.864.264. Chênh lệch
đó không thể giải thích bằng vi kiến trúc, nên chỉ còn một khả năng: **hai số đo không cùng firmware**.

Bước xác nhận: `GIT_HASH` nhúng trong firmware. `sim.log` đã lưu của A-V0 báo `339b4fb`, còn file hex
trên đĩa báo `c718706` — hai bản khác nhau cùng mang tên `v0/firmware.hex`.

**Cách chặn.** `GIT_HASH` **không đủ**: firmware có thể dựng từ bản nháp chưa commit, và khi đó hash
vẫn trỏ về commit cũ một cách hợp lệ. Nên firmware giờ in thêm **dấu vân tay NỘI DUNG**:

```
SRC_HASH := $(shell cat main.c $(FWDIR)/weights.h | shasum -a 256 | cut -c1-12)
```

Kit in `M1S,src,<SRC_HASH>`, và `scripts/m1s_check.py` **từ chối ghi nhận** số đo nếu giá trị đó khác
mã nguồn đang có trên đĩa. Cả năm số trong bảng mục 3 đều mang `SRC_HASH = 647f1d071aca`.

**Bài học, phát biểu cho luận văn.** Một bộ số đo chỉ so sánh được với nhau khi **mọi biến thể đến từ
cùng một trạng thái mã nguồn**, và điều kiện đó phải được **máy kiểm**, không phải người nhớ. Kiểm
tính đúng đắn (CRC khớp golden) **không** bắt được lỗi này: cả hai bản firmware đều cho kết quả đúng
từng bit — chúng chỉ chạy nhanh khác nhau.

**Phạm vi ảnh hưởng.** Chỉ các *tỷ số* so với A-V0 và các con số của A-V0/A-V2. Không ảnh hưởng:
độ chính xác 98,25 % (mục 1 và 3b), 10.000/10.000 CRC khớp golden, tài nguyên FPGA và Fmax (mục 4),
chi phí requantize 49,6 chu kỳ, và kết luận "kit = Verilator bằng tuyệt đối". Số đo 10.000 ảnh ở mục
3b chạy trên firmware dựng **trước** khi thêm dấu `SRC_HASH`; `scripts/cmp_layers.py` đã chứng minh mã
máy của cả năm lớp tính toán giống hệt bản `v1dc`, nên kết quả đó vẫn áp dụng.

## 4. Tài nguyên FPGA

| Thiết kế | LUT4 | DFF | BSRAM | MULT18X18 | Fmax (MHz) |
|---|---:|---:|---:|---:|---:|
| A-V0, A-V1 (không DOT4) | 7.941 (38,3 %) | 1.069 | 32/46 | 0 | 71,76 |
| A-V2, A-V1+DOT4, A-V1+DOT4+C1 (có DOT4) | 8.065 (38,9 %) | 1.153 | 32/46 | 4/48 | 71,89 |
| **Hiệu hai lần tổng hợp** | +124 (+1,6 %) | +84 | 0 | **+4** | +0,13 |

> **Đọc bảng này cẩn thận.** Hiệu **+124 LUT4** KHÔNG đo được chi phí của DOT4: xem
> `docs/KET_QUA_NHANH_B.md` mục 6b — đổi đúng một tham số tổng hợp đã được chứng minh làm tổng LUT4
> xê dịch tới **1.545** vì ABC chọn cách phủ khác, nên mọi hiệu số nhỏ hơn con số đó **không kết luận
> được**. Hai điều VẪN chính xác và đáng dùng: **+4 MULT18X18** (đã truy từng instance về đúng dòng mã
> trong netlist) và **Fmax không giảm**. Chi phí LUT thật của DOT4 muốn biết thì phải tổng hợp riêng
> khối đó ngoài ngữ cảnh.

Ba biến thể có DOT4 dùng **cùng một bitstream về mặt phần cứng** — chỉ khác nội dung firmware trong
BSRAM. Tương tự A-V0 và A-V1. Nghĩa là: **toàn bộ 1,45× của A-V1 và 1,19× của bước +C1 là miễn phí
về phần cứng**; DOT4 phải trả **4 khối MULT18X18** và **không giảm Fmax** (chi phí LUT: xem cảnh báo
ở trên — hiệu hai lần tổng hợp không đo được nó).
Biên Fmax so với 27 MHz vẫn là **2,66 lần**.

**Bộ nhớ** (RAM 65.536 byte): A-V0 27.592 (42,1 %) · A-V1 29.272 (44,7 %) · A-V2 27.488 (41,9 %) ·
A-V1+DOT4 27.792 (42,4 %) · A-V1+DOT4+C1 **32.368 (49,4 %)**. Bản +C1 tốn thêm 3.584 byte cho
4 bộ đệm pha dịch và ~1,2 KB `.text`. Còn dư ≥33 KB ở mọi biến thể.

## 5. Nhận xét

**1. Hai hướng tối ưu KHÔNG độc lập, và tương tác thuận lợi.** DOT4 cho 1,56× trên C thẳng nhưng
**2,13× trên C đã tối ưu** — gấp 1,37 lần. Lý do: chúng cắt hai phần khác nhau của chi phí. Tối ưu phần mềm bỏ phần tính
chỉ số (thấy rõ ở conv1: 71,74 → 32,88 chu kỳ/MAC mà không có lệnh mới nào); DOT4 bỏ phần nhân-cộng
(conv2: 30,13 → 7,08 chu kỳ/MAC trên nền đã tối ưu). **Đây là kết quả đáng giá nhất của thí nghiệm**:
nó bảo vệ kết luận khỏi phản biện "baseline code kém".

**2. Nút cổ chai conv1 gỡ được bằng BỐ CỤC, không cần phần cứng mới.** Ở A-V1+DOT4, conv1 chiếm
54,9 % thời gian và bị chặn bởi yêu cầu thẳng hàng 4 byte của `DOT4`. Bốn bản sao ảnh dịch
0/1/2/3 byte (3.584 byte `.bss`) gỡ được hạn chế đó và cho thêm **1,19×**, đưa tổng lên **3,67×**
(mục 3). → **Giới hạn của một lệnh tùy biến có thể nằm ở bố cục dữ liệu chứ không ở bản thân lệnh.**
Đây là kết luận đáng đưa vào luận văn: trước khi thiết kế thêm phần cứng, hãy kiểm xem bố cục đã cho
lệnh hiện có dùng hết chưa.

Sau bước đó, conv1 vẫn là lớp tốn nhất (1.133.668 chu kỳ = 46,3 % tổng) vì mỗi giá trị đầu ra chỉ có
9 MAC để chia sẻ chi phí cố định (requantize, lưu kết quả, vòng lặp), còn conv2 có 72 MAC mỗi giá trị
đầu ra. Đó là lý do conv1 đạt 23,29 chu kỳ/MAC trong khi conv2 đạt 7,08.

**3. Ước tính ở F7 khá sát.** F7 ngoại suy từ chu kỳ/MAC của conv1 ra **≈516 ms** cho M1-S. Số đo thật
của A-V0 là **332,9 ms** — ước tính **cao hơn 55 %**, lệch theo hướng an toàn, và đúng lý do F7 đã nêu:
conv2 có `Cin=8` nên chi phí/MAC *thấp hơn* conv1 (35,95 so với 71,74) do chia sẻ được phần tính chỉ số.

**4. Một cái bẫy của trình biên dịch, không liên quan tới phần cứng.** Ban đầu 5 lớp là hàm `static`
gọi một lần, GCC `-O2` nội suy hết vào `main`; cấp phát thanh ghi tràn làm A-V0 chạy **21.350.804**
chu kỳ. Thêm `__attribute__((noinline))` cho mỗi lớp đưa về **8.987.660** chu kỳ — **nhanh hơn 1,76×
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

**7. Số đo trên kit đã phủ đủ tập test, và nó cho một kết quả phụ đáng giá.** 10.000/10.000 ảnh khớp
golden từng bit, độ chính xác **98,25 % đo trực tiếp trên kit**. Ngoài ra phân bố chu kỳ trên 10.000
ảnh cho thấy thời gian suy luận dao động **chưa tới 0,031 %** (90,74–90,77 ms) — tính tất định mà
10 ảnh không chứng minh được, và là lập luận mạnh cho ứng dụng thời gian thực. IPC chỉ **0,160** chỉ
rõ nút cổ chai kế tiếp nằm ở **vi kiến trúc lõi**, tức nhánh B, chứ không ở thêm lệnh tùy biến.

**8. Những gì phần này chưa làm.** Chưa hiện thực **REQ**. Chưa làm **nhánh B** (lõi tự viết).
Chưa đo công suất.

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

# 3. Chạy đủ 10.000 ảnh trên kit (~30 phút). Mô phỏng trước, rồi mới tổng hợp:
make sim-v10k            # 3 ảnh trong Verilator, có bơm UART vào chân uart_rx
make cmp-v10k            # chứng minh mã 5 lớp không đổi so với v1dc
make build-v10k load-v10k
make run-v10k            # N10K=20 để thử nhanh trước
python3 ../../scripts/m1s_10k_stats.py ../../results/experiment/m1s/m1s_10k.csv
make archive
```

| Thư mục | Biến thể | Cờ biên dịch |
|---|---|---|
| `v0/` | A-V0 | (không) |
| `v1/` | A-V1 | `-DOPT_KERNELS` |
| `v2/` | A-V2 | `-DUSE_DOT4` |
| `v1d/` | A-V1+DOT4 | `-DOPT_KERNELS -DUSE_DOT4` |
| `v1dc/` | A-V1+DOT4+C1 | `-DOPT_KERNELS -DUSE_DOT4 -DCONV1_DOT4 -DREQ_BENCH` |
| `v10k/` | A-V1+DOT4+C1, ảnh qua UART | `… -DCONV1_DOT4 -DSTREAM_10K` |

PyTorch nằm trong venv riêng `.venv-model` (Python 3.12 + torch 2.2.2 + numpy 1.26.4): Python 3.14
của `.venv` chính **không có** wheel torch cho macOS x86_64, và torch 2.2.2 là bản cuối còn wheel cho
nền tảng này — nó lại cần numpy < 2. Chi tiết trong `env/VERSIONS.md`.
