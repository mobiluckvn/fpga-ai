# S8 — mô hình giữ lại M1-L: các ứng viên phần cứng có tổng quát hoá không?

**Câu hỏi (PQ6)**: DOT4, bố cục 4 pha, REQ và PMAX4 đều được chọn dựa trên profile của
**M1-S**. Chúng còn tăng tốc một mô hình **chưa từng dùng khi chọn** không, và được bao nhiêu?

**Trả lời ngắn: có, nhưng ít hơn — và lý do đọc được thẳng từ phân rã theo lớp.**

## 1. Mô hình giữ lại

M1-L = M1-S **gấp đôi kênh** (conv1 1→16, conv2 16→32, dense 800→10).

| | M1-S | M1-L | tỷ lệ |
|---|---:|---:|---:|
| tham số | 5.258 | **12.810** | 2,44× |
| MAC/ảnh | 192.064 | **662.912** | **3,45×** |
| độ chính xác float | 98,29 % | **98,81 %** | |
| độ chính xác int8 | 98,25 % | **98,79 %** | |
| chênh int8 vs float | −0,04 điểm | **+0,02 điểm** | |

**Nó "giữ lại" theo nghĩa chặt**: không có một nhánh mã nào dành riêng cho nó. Cùng script
huấn luyện (`model/train_m1s.py --c1 16 --c2 32`), cùng script lượng tử hoá, cùng
`model/golden_m1s.py` (vốn đã không phụ thuộc kích thước), cùng `main.c`, cùng bộ kernel.
Ba phép kiểm giống-hệt-từng-bit chứng minh việc tổng quát hoá không đụng vào M1-S — xem mục 5.

## 2. Bảng chính: mô hình × cấu hình (Verilator, trung vị 10 ảnh)

| mô hình | cấu hình | chu kỳ/ảnh | ms @27 MHz | chu kỳ/MAC | IPC | so mốc | đúng bit |
|---|---|---:|---:|---:|---:|---:|---|
| M1-S | B-V1 (C thẳng) | 2.447.438 | 90,6 | 12,74 | 0,751 | 1,000× | ĐẠT 10/10 |
| M1-S | B-V3 (DOT4+REQ) | 365.992 | 13,6 | 1,91 | 0,759 | **6,687×** | ĐẠT 10/10 |
| M1-S | B-V3+PMAX4 | 317.878 | 11,8 | 1,66 | 0,743 | **7,699×** | ĐẠT 10/10 |
| **M1-L** | B-V1 (C thẳng) | 7.637.179 | 282,9 | 11,52 | 0,731 | 1,000× | ĐẠT 10/10 |
| **M1-L** | B-V3 (DOT4+REQ) | 1.208.331 | 44,8 | 1,82 | 0,710 | **6,320×** | ĐẠT 10/10 |
| **M1-L** | B-V3+PMAX4 | **1.116.402** | **41,3** | **1,68** | 0,698 | **6,841×** | ĐẠT 10/10 |

"đúng bit" = firmware tự so CRC32 của **cả 5 tensor trung gian** với golden Python nhúng sẵn,
10/10 ảnh, và dự đoán khớp golden. Dòng `M1S,sum,10,10,10,10` trong mọi `sim/*_sim.log`.

### Đối chứng: kernel tổng quát tái lập ĐÚNG số đã đo trên kit

| | kernel tổng quát (bước này) | số đã đo trên kit | |
|---|---:|---:|---|
| M1-S trên B-V3 | **365.992** | 365.992 | **khớp tuyệt đối** |
| M1-S trên B-V3+PMAX4 | **317.878** | 317.878 | **khớp tuyệt đối** |

Hai số này là của dòng 14 và dòng 15 trong `docs/KET_QUA_TONG_HOP.md`. Kernel tổng quát
không phải mã mới chưa ai kiểm — nó cho lại đúng từng chu kỳ những gì phần cứng thật đã cho.

## 3. Hệ số tăng tốc: hai mô hình cạnh nhau

| bước | M1-S | M1-L (giữ lại) | chênh |
|---|---:|---:|---:|
| DOT4 + bố cục 4 pha + REQ | 6,687× | 6,320× | **−5,5 %** |
| thêm PMAX4 | 1,151× | 1,082× | **−6,0 %** |
| **tổng: C thẳng → đủ ba lệnh** | **7,699×** | **6,841×** | **−11,1 %** |

**Các ứng viên tổng quát hoá được.** Mô hình chưa từng tham gia việc chọn vẫn nhận **6,84×**,
so với **7,70×** của mô hình đã dùng để chọn. Mất khoảng **11 %** hệ số, không mất hiệu lực.

## 4. Vì sao mất 11 % — đọc thẳng từ phân rã theo lớp

Tỷ trọng chu kỳ ở mốc C thẳng:

| | conv1 | pool1 | conv2 | pool2 | dense |
|---|---:|---:|---:|---:|---:|
| M1-S | 31 % | 2 % | **65 %** | 1 % | 2 % |
| M1-L | 20 % | 1 % | **78 %** | 0 % | 1 % |

Gấp đôi kênh làm **conv2 nặng gấp 4** (C1×C2) nhưng **pooling chỉ nặng gấp 2** (theo số
activation). Nên ở M1-L, phần việc mà **PMAX4** chạm tới co lại: pooling chiếm 15 % tổng của
M1-S ở cấu hình B-V3 nhưng chỉ 9 % của M1-L. Đó chính là lý do PMAX4 cho 1,151× trên M1-S mà
chỉ 1,082× trên M1-L.

**Bài học tổng quát: giá trị của một ứng viên phần cứng phụ thuộc TỶ LỆ PHÉP TOÁN của mô hình,
không phụ thuộc kích thước mô hình.** Mô hình giữ lại lệch tỷ lệ về phía conv, nên lệnh phục vụ
pooling mất giá, còn lệnh phục vụ MAC (DOT4) giữ giá gần như nguyên.

## 5. Ba phép kiểm giống-hệt-từng-bit của việc tổng quát hoá

Việc cho M1-L chạy đòi tổng quát hoá ba chỗ vốn ghim cứng theo M1-S. Cả ba chỗ đều nằm trong
đường đã sinh ra mọi số đã công bố, nên mỗi chỗ có một phép kiểm:

| tổng quát hoá | phép kiểm | kết quả |
|---|---|---|
| `quantize_m1s.py` suy kích thước từ hình dạng trọng số | sinh lại `fw/weights.h` của M1-S | **giống hệt từng byte** |
| `m1s_s6/Makefile` thêm biến `WEIGHTS` | dựng lại firmware M1-S, hash ghim bằng nhau | **giống hệt từng bit** |
| `cand/gen_dcr.c`, `cand/gen_dcrp.c`: 9 offset conv2 do tiền xử lý tính | so mã máy với `kernels_v3.c` và `cand/pmax4.c` | **giống hệt từng bit** |

Phép kiểm thứ ba đáng nói: với `M1S_C1 = 8`, biểu thức `((ky)*M1S_POOL1 + (kx)) * M1S_C1`
sinh đúng dãy hằng số viết tay cũ (0, 8, 16, 104, 112, 120, 208, 216, 224), nên trình biên
dịch cho ra **đúng cùng một tệp nhị phân**.

## 6. Kết quả phụ: PMAX4 làm thời gian chạy HẾT phụ thuộc dữ liệu

Max-pool viết bằng C có nhánh `if (v > m) m = v;` — rẽ nhánh theo **dữ liệu**. Hệ quả đo được:

| cấu hình | số giá trị `pool1` khác nhau trên 10 ảnh | biên độ tổng chu kỳ |
|---|---:|---:|
| M1-S, B-V1 | 10 | 0,02 % |
| M1-S, B-V3 | 10 | 0,11 % |
| **M1-S, B-V3+PMAX4** | **1** | **0,00 %** |
| M1-L, B-V1 | 9 | 0,01 % |
| M1-L, B-V3 | 9 | 0,07 % |
| **M1-L, B-V3+PMAX4** | **1** | **0,00 %** |

PMAX4 không chỉ nhanh hơn: nó **không nhánh**, nên cả 10 ảnh cho **đúng cùng một số chu kỳ**.
Với hệ thống thời gian thực, thời gian chạy tất định là một thuộc tính riêng, không phải hệ quả
phụ của việc chạy nhanh. Điều này không nằm trong tiêu chí chọn ứng viên ở S5/S6 — nó lộ ra khi
đo mô hình giữ lại.

## 7. Dung lượng RAM: vì sao B-V4 KHÔNG có trong bảng

| firmware | .text | .bss | tổng | vừa 64 KB | vừa 32 KB |
|---|---:|---:|---:|---|---|
| M1-S, C thẳng | 18.540 | 9.136 | 27.676 | vừa | vừa |
| M1-S, đủ ba lệnh | 18.772 | 12.816 | 31.588 | vừa | vừa (96,4 %) |
| M1-L, C thẳng | 25.792 | 18.232 | 44.024 | vừa | **KHÔNG** |
| M1-L, đủ ba lệnh | 26.600 | 22.008 | **48.608** | vừa (74 %) | **KHÔNG** |

**B-V4 (bộ nhớ hai cổng) chỉ có 32 KB RAM**, vì BSRAM hai cổng của GW2AR mất một nửa mật độ:
64 KB hai cổng cần 64 khối, chip chỉ có 46. M1-S đã chiếm 96,4 % của 32 KB. **Không mô hình nào
lớn hơn M1-S chạy được trên B-V4.**

Đây là **giá thứ ba** của ứng viên bộ nhớ hai cổng, bên cạnh LUT4 ×3,5 đã đo ở S7:

1. chu kỳ — mô hình λ thấy, và dự báo đúng 0,00 %;
2. diện tích — mô hình λ **không** thấy (370 LUT4 cho mỗi 1 % tăng tốc, gấp 38 lần PMAX4);
3. **dung lượng — mô hình λ không thấy, số LUT cũng không thấy: nó giới hạn MÔ HÌNH NÀO chạy được.**

Giá thứ ba chỉ lộ ra khi có một mô hình thứ hai. Đó là lý lẽ cho việc giữ lại một mô hình.

**Hướng gỡ cho lần sau** (chưa làm, thuộc vòng mở tiếp theo): Harvard tách hẳn — bộ nhớ lệnh
32 KB một cổng + bộ nhớ dữ liệu 32 KB một cổng, mỗi bên 16 khối BSRAM thường. Lấy được λ_load
= 1 mà không cần BSRAM hai cổng, và tổng vẫn 64 KB.

## 8. Còn thiếu

- **Chưa đo M1-L trên kit.** Bitstream `gl_dcrp` đang dựng. Verilator đã đúng bit 10/10.
- **Chưa có dòng PicoRV32** cho M1-L (nhánh A dùng cây RTL khác). Bảng hiện so trong nội bộ
  các cấu hình mycore, đủ để trả lời PQ6.

## 9. Tệp

| tệp | nội dung |
|---|---|
| `sim/g{s,l}_{plain,dcr,dcrp}_sim.log` | log Verilator thô, 10 ảnh, đủ CRC từng lớp |
| `sim/g*_size.txt` | kích thước từng firmware |
| `ket_qua_sim.json` | mọi số trong README này, dạng máy đọc |
| `train_m1l.log`, `quantize_m1l.log` | log huấn luyện và lượng tử hoá M1-L |
| `../../model/m1l_float.npz`, `../../model/m1l_int8.npz` | trọng số M1-L |
| `../../fw/weights_m1l.h` | header trọng số + 10 ảnh thử + CRC golden |
| `../../experiment/m1s_s6/cand/gen_*.c` | ba kernel tổng quát |
