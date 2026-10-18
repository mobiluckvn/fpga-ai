# Dò khả thi: bộ nhớ hai cổng (trước khi viết RTL)

Dự báo đã đóng băng: `du_bao_BONHO2CONG_truoc_khi_hien_thuc.json` —
**243.641 chu kỳ (1,3047×) trên cơ sở B-V3+PMAX4**, mức A.

Tài liệu này ghi các phép dò **trước** khi viết RTL, để biết ứng viên có khả thi không và
dự báo mức A có điều kiện gì. Mọi số đều từ công cụ thật, có lệnh tái lập.

## 1. Vì sao load/store tốn 2 chu kỳ

`mycore` dùng **một cổng bộ nhớ chung** cho nạp lệnh và truy cập dữ liệu. Ở `S_EXEC` với
`FAST_ADDR=1`, lệnh load/store chiếm cổng cho dữ liệu nên không nạp được lệnh kế trong cùng
chu kỳ → phải thêm một chu kỳ (`rtl/mycore/mycore.v`, `S_EXEC` → `pc_ret`). Tách cổng lệnh và
cổng dữ liệu (kiểu Harvard) thì hai việc xảy ra cùng chu kỳ.

Tỷ trọng đáng giá: trên B-V3+PMAX4, **load 39,3 % + store 7,4 % = 46,7 % tổng chu kỳ** là truy
cập bộ nhớ — lớn hơn cả `mac` (33,2 %). Đúng như rào roofline mà lý thuyết dự đoán: SIMD hoá
phần tính rồi thì bộ nhớ thành tường chắn (`docs/MO_HINH_CHI_PHI.md` mục 3).

## 2. Yosys CÓ suy ra BSRAM hai cổng — nhưng 64 KB thì không vừa chip

Phép dò: mảng `reg [31:0] ram [0:N-1]` với một cổng đọc-ghi (dữ liệu) và một cổng chỉ đọc
(lệnh), chạy `yosys -p "read_verilog probe_dp.v; synth_gowin -top probe_dp"`.

| bộ nhớ | khối Yosys suy ra | vừa chip (46 khối)? |
|---|---|---|
| 64 KB, một cổng — **thiết kế hiện tại** | 32 × `SP` | có (32/46 = 69,6 %) |
| 64 KB, hai cổng | **64 × `DPB`** | **KHÔNG** |
| 32 KB, hai cổng | **32 × `DPB`** | **có — đúng bằng số khối đang dùng** |
| 32 KB, một cổng | 16 × `SP` | có |

Chế độ hai cổng thật (`DPB`) mất **một nửa mật độ** mỗi khối. Nên đường khả thi duy nhất là
**thu RAM từ 64 KB xuống 32 KB và dùng hai cổng** — số khối BSRAM **không tăng**.

Tin tốt: Yosys suy ra `DPB` chứ không rơi về RAM bằng LUT. Đó là rủi ro lớn nhất đã nêu trong
file dự báo, và nó **đã được loại bỏ**.

## 3. 32 KB có đủ không? Đo ngăn xếp, hai cách độc lập

Bản đồ bộ nhớ hiện tại (`firmware.map` của `cpmax4`): `.text` 0 → `0x4954`,
`.bss` `0x4954` → `0x7b64`, `__heap_start = 0x7b64` = **31.588 byte**. `sp` khởi tạo `0x10000`
(`fw/start.S`), mọc xuống.

| cách đo | độ sâu ngăn xếp | ghi chú |
|---|---:|---|
| quét bộ nhớ sau khi chạy ISS, tìm byte khác 0 thấp nhất trên `__heap_start` | 256 byte | chặn dưới — bỏ sót byte ghi giá trị 0 |
| theo dõi trực tiếp `min(x2)` trong ISS (`Iss(..., track_sp=True)`, mới thêm) | **256 byte** | chính xác |

Hai cách **khớp tuyệt đối**. Vậy ở RAM 32 KB:

```
32.768 (đỉnh)  −  31.588 (__heap_start)  =  1.180 byte cho ngăn xếp
cần 256 byte  →  VỪA, biên an toàn 4,6×   (còn trống 924 byte)
```

Lưu ý cho sau này: 924 byte trống là **hẹp**. Mọi lần firmware lớn thêm phải kiểm lại con số này.

## 4. Rủi ro còn lại, và nó có thể làm dự báo mức A SAI

**Xung đột load-use.** BSRAM có đầu ra qua thanh ghi: đặt địa chỉ ở chu kỳ N thì dữ liệu về ở
N+1. Với hai cổng, ở `S_EXEC` ta đặt được **đồng thời** địa chỉ dữ liệu (cổng D) và địa chỉ lệnh
kế (cổng I) → chu kỳ sau có **cả** dữ liệu nạp **và** lệnh kế. Nhưng khi đó dữ liệu nạp phải ghi
về thanh ghi **trong chính chu kỳ** mà lệnh kế đang thực thi. Nếu lệnh kế **dùng ngay** thanh ghi
vừa nạp thì có xung đột RAW, và phải **chuyển tiếp dữ liệu** (forwarding) hoặc **chèn một chu kỳ
dừng**. Chèn dừng nghĩa là λ_load **vẫn là 2** cho đúng những cặp lệnh phổ biến nhất trong tải
này (nạp rồi nhân-cộng ngay).

Đây là điều kiện thật của dự báo mức A, nặng hơn rủi ro BSRAM: **λ_load = 1 chỉ đạt được nếu RTL
có đường chuyển tiếp**. Nếu không, lợi ích thật sẽ thấp hơn 1,3047× nhiều.

**Đã đếm, trước khi viết RTL.** `Iss(..., track_ldu=True)` mới thêm, đếm **chỉ trong 10 cửa sổ
đo** (tổng 3.178.780 chu kỳ = đúng 10 × 317.878 của kit):

| | load | store | load-use ngay sau | tỷ lệ |
|---|---:|---:|---:|---:|
| B-V3+PMAX4 | 624.770 | 117.600 | 114.160 | **18,3 %** số load |
| B-V3 | 677.420 | 130.830 | 113.160 | 16,7 % số load |

Hai dự báo, cả hai đóng băng trước khi hiện thực:

| trường hợp | chu kỳ/ảnh | tăng tốc | tệp |
|---|---:|---:|---|
| **có** đường chuyển tiếp (mọi load λ=1) | **243.641** | **1,3047×** | `du_bao_BONHO2CONG_truoc_khi_hien_thuc.json` |
| **không** chuyển tiếp (chèn dừng ở load-use) | 255.057 | 1,2463× | `du_bao_BONHO2CONG_khong_chuyen_tiep.json` |

Khoảng rộng **11.416 chu kỳ = 4,7 %** — **hẹp**. Kết luận quan trọng: ứng viên **đáng làm trong cả
hai trường hợp**, nên không cần chờ giải quyết chuyện chuyển tiếp mới quyết định làm. Nhưng phải ghi
rõ RTL cuối cùng thuộc trường hợp nào, vì đó là điều kiện của dự báo mức A.

**Đối chứng chéo**: con số "có chuyển tiếp" tính độc lập từ đếm theo cửa sổ ra **đúng 243.641**,
khớp tuyệt đối `est_lambda()` đã đóng băng trước đó. Hai đường tính khác nhau, cùng một kết quả.

Các rủi ro khác vẫn như file dự báo đã ghi: Fmax phải ≥ 27 MHz sau khi thêm đường dữ liệu thứ hai,
và nếu phải thêm tầng thanh ghi để giữ Fmax thì λ không về 1.

## 5. Lệnh tái lập

```bash
# dò số khối BSRAM (file dò ở scratchpad, nội dung in trong mục 2)
yosys -p "read_verilog probe_dp.v; synth_gowin -top probe_dp"
# đếm lệnh động và tỷ trọng theo lớp
./cdp analyze  --target "B-V3+PMAX4"
./cdp profile  --target "B-V3+PMAX4"
# độ sâu ngăn xếp: Iss(..., track_sp=True).run() -> iss.min_sp
```

## 6. Một bẫy phạm vi vừa gặp lại

Lần đầu tôi đếm load-use trên **toàn lần chạy** ISS (`iss.cycle` = 9.041.066 chu kỳ) thay vì trong
10 cửa sổ đo (3.178.780). Tỷ lệ và dự báo ra sai hết. Đúng họ lỗi đã ghi ở `docs/LOG.md`: trộn
phạm vi tử số và mẫu số. Phép kiểm cứu được tôi: tổng cửa sổ của B-V3+PMAX4 phải **bằng đúng**
10 × 317.878 — và chỉ bằng khi đếm theo cửa sổ.

Chi tiết liên quan: với **B-V3**, tổng 10 cửa sổ (3.659.267) **không** bằng 10 × trung vị
(3.659.920) vì 10 ảnh lệch nhau chút ít; với **B-V3+PMAX4** thì bằng đúng vì cả 10 ảnh đều
317.878. Nên mọi tỷ trọng phải chia cho **tổng của đúng 10 ảnh đó**, không chia cho trung vị.
