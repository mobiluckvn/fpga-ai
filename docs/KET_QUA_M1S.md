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

## 2. Hai biến thể đã đo

| | A-V0 | A-V2 |
|---|---|---|
| Kernel | C thẳng, `-O2` | conv2 + dense dùng lệnh tùy biến **DOT4** |
| SoC | PicoRV32, không PCPI | PicoRV32 + khối `pcpi_dot4` (4× `MULT18X18`) |

**Vì sao conv1 không dùng DOT4**: `DOT4` nạp 4 byte liền nhau bằng `lw` nên **cần địa chỉ thẳng hàng
4 byte** (lõi bật `CATCH_MISALIGN`). Với bố cục channels-last, conv2 có `Cin=8` nên 4 kênh vào liền
nhau luôn thẳng hàng; conv1 có `Cin=1` nên không có 4 giá trị liền nhau để cộng dồn mà vẫn thẳng hàng.
conv1 chiếm 48.672/192.064 = **25,3 % số MAC** nhưng **28,8 % thời gian** của A-V0.

---

## 3. Số đo trên kit (trung vị trên 10 ảnh, 27 MHz)

| Lớp | A-V0 | A-V2 | Tăng tốc | MAC | chu kỳ/MAC A-V0 | chu kỳ/MAC A-V2 |
|---|---:|---:|---:|---:|---:|---:|
| conv1 | 3.491.721 | 3.491.721 | 1,00× | 48.672 | 71,74 | 71,74 |
| pool1 | 225.621 | 225.621 | 1,00× | — | — | — |
| **conv2** | 8.153.979 | **1.924.815** | **4,24×** | 139.392 | 58,50 | **13,81** |
| pool2 | 65.924 | 65.924 | 1,00× | — | — | — |
| **dense** | 192.552 | **48.552** | **3,97×** | 4.000 | 48,14 | **12,14** |
| **TỔNG** | **12.129.818** | **5.756.654** | **2,11×** | 192.064 | **63,16** | **29,97** |
| Số lệnh | 1.864.264 | 912.832 | 2,04× | | | |
| **Thời gian @27 MHz** | **449,3 ms** | **213,2 ms** | | | | |
| Ảnh/giây | 2,23 | 4,69 | | | | |

`conv1`, `pool1`, `pool2` giống hệt **từng chu kỳ** giữa hai biến thể — bằng chứng rằng phép so sánh
chỉ khác đúng một thứ (lệnh DOT4 trong conv2 và dense).

### Tính đúng đắn — điều kiện để ghi nhận số đo
Cả hai biến thể, lặp lại 2/2 lần đọc độc lập:

| Kiểm tra | Kết quả |
|---|---|
| CRC32 từng lớp (a1, p1, a2, p2, logit) trên kit = golden Python | **50/50 khớp** (5 lớp × 10 ảnh) |
| Dự đoán trên kit = dự đoán golden | **10/10** |
| Dự đoán trên kit = nhãn thật | **10/10** |
| Số chu kỳ trên kit = số chu kỳ trong Verilator | **bằng tuyệt đối**, cả 7 cột × 10 ảnh |

---

## 4. Tài nguyên FPGA

| Thiết kế | LUT4 | DFF | BSRAM | MULT18X18 | Fmax (MHz) |
|---|---:|---:|---:|---:|---:|
| A-V0 | 7.941 (38,3 %) | 1.069 | 32/46 | 0 | 71,76 |
| A-V2 | 8.065 (38,9 %) | 1.153 | 32/46 | 4/48 | 71,89 |
| **Chi phí của DOT4** | **+124** | +84 | 0 | +4 | **+0,13** |

Thêm một lệnh tùy biến cho **tăng tốc 2,11× toàn mô hình** với giá **+124 LUT4 (+1,6 %)** và
**không giảm Fmax**. Biên Fmax so với 27 MHz vẫn là **2,66 lần**.

**Bộ nhớ**: A-V0 dùng `.text` 18.428 + `.bss` 9.136 = **27.564 / 65.536 byte (42,1 %)**;
A-V2 dùng 27.472 byte. Trong `.text` có 13,4 KB dữ liệu tĩnh (trọng số 5,3 KB + 10 ảnh thử 7,8 KB).
Còn dư ~38 KB.

---

## 5. Nhận xét

**1. Tăng tốc bị chặn bởi conv1, đúng như dự báo ở F8.** Trong A-V2, conv1 chiếm **60,7 %** thời gian
và không được DOT4 cắt. Theo định luật Amdahl, dù conv2 và dense có nhanh vô hạn thì tăng tốc toàn mô
hình cũng chỉ tới 12.129.818 / 3.783.266 ≈ **3,21×**. Phần thời gian có thể cắt là
12.129.818 − 3.783.266 = 8.346.552 chu kỳ; DOT4 đã cắt được 12.129.818 − 5.756.654 = 6.373.164 chu kỳ,
tức **76,4 % phần có thể cắt**. Muốn đi xa hơn phải nhắm vào conv1 — ví dụ một lệnh dạng DOT4 đọc
toán hạng không cần thẳng hàng, hoặc đổi bố cục để conv1 cũng cộng dồn được 4 phần tử liền địa chỉ.

**2. Tăng tốc theo lớp sát tỉ lệ giảm số lệnh, giống kết luận F8.** conv2 đạt 4,24× — *cao hơn* giới
hạn lý thuyết 4× của DOT4, vì bản DOT4 còn bỏ luôn phần tính chỉ số của vòng lặp kênh vào. dense đạt
3,97×, gần đúng 4×.

**3. Ước tính ở F7 khá sát.** F7 ngoại suy từ chu kỳ/MAC của conv1 ra **≈516 ms** cho M1-S. Số đo thật
của A-V0 là **449,3 ms** — ước tính **cao hơn 15 %**. Sai lệch theo hướng an toàn, và đúng như ba lý do
đã nêu ở F7: conv2 có `Cin=8` nên chi phí/MAC *thấp hơn* conv1 (58,50 so với 71,74) do chia sẻ được
phần tính chỉ số.

**4. Một phát hiện về trình biên dịch, không liên quan tới phần cứng.** Ban đầu 5 lớp là hàm `static`
gọi một lần, GCC `-O2` nội suy hết vào `main`; cấp phát thanh ghi tràn làm A-V0 chạy **21.350.804**
chu kỳ. Thêm `__attribute__((noinline))` cho mỗi lớp đưa về **12.129.818** chu kỳ — **nhanh hơn
1,76× mà không đổi một dòng thuật toán nào**. Tệ hơn nữa, nếu không có `noinline` thì cấp phát thanh
ghi của conv1 *thay đổi theo* việc conv2 có dùng DOT4 hay không (3.803.170 so với 4.950.316 chu kỳ),
làm phép so sánh A-V0/A-V2 mất ý nghĩa. → **Kết luận phương pháp: khi so hai biến thể tập lệnh, phải
cố định ranh giới hàm, và phải kiểm rằng các lớp không thay đổi cho ra ĐÚNG số chu kỳ cũ.**

**5. Những gì phần này chưa làm.** Chỉ đo 10 ảnh trên kit (độ chính xác 98,25 % là của golden Python
trên đủ 10.000 ảnh, không phải của kit trên 10.000 ảnh). Chưa làm biến thể A-V1 (chỉ tối ưu phần mềm,
nhóm đối chứng) và A-V3 (thêm lệnh REQ). Chưa đo công suất.

---

## 6. Cách chạy lại

```bash
source env/setup_env.sh

# 1. Huấn luyện + lượng tử hoá (chỉ cần Python, không cần kit; venv riêng có PyTorch)
cd model && ../.venv-model/bin/python train_m1s.py      # ~35 s, in độ chính xác float
../.venv-model/bin/python quantize_m1s.py               # ~90 s, sinh fw/weights.h

# 2. Mô phỏng và nạp kit, cả hai biến thể
cd ../experiment/m1s
make fw-v0 sim-v0 build-v0 load-v0 check-v0             # A-V0
make fw-v2 sim-v2 build-v2 load-v2 check-v2             # A-V2
make archive
```

PyTorch nằm trong venv riêng `.venv-model` (Python 3.12 + torch 2.2.2 + numpy 1.26.4): Python 3.14
của `.venv` chính **không có** wheel torch cho macOS x86_64, và torch 2.2.2 là bản cuối còn wheel cho
nền tảng này — nó lại cần numpy < 2. Chi tiết trong `env/VERSIONS.md`.
