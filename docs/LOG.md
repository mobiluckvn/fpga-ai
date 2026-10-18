# Nhật ký làm việc

Mỗi phiên một mục, mới nhất ở trên cùng:

## 2026-10-18 — PMAX4 lần thử 4: giả thuyết của tôi bị bác bỏ, dừng theo quy tắc 3 lần

Người dùng cắm lại cáp USB. Tôi đo **PMAX4 trước tiên**, không chạy gì khác trước nó —
đúng như điều tôi đã kết luận ở mục trên. Run `20261018-220038-kit`:

| bước | kết quả |
|---|---|
| đối chứng TRƯỚC | ĐẠT — "MIN" 8 lần |
| lần đọc 1/2 | **ĐẠT** — xả 4.548 byte tồn, CRC 10/10, chu kỳ = Verilator |
| lần đọc 2/2 | **0 dòng thô** |
| đối chứng SAU | 0 byte cả hai cổng |

**Giả thuyết "kênh UART chịu được ba lần truyền dài sau mỗi lần cắm cáp" là SAI.** Nó dự
đoán lần này sẽ qua, vì đây là lần truyền dài đầu tiên sau khi cắm cáp. Nó không qua. Tôi
đã sửa lại chỗ đã viết trong `docs/KET_QUA_TONG_HOP.md` và `results/pipeline/S6/kit/README.md`
— không để một kết luận sai nằm lại trong báo cáo.

### Điều còn đứng vững sau bốn run

Lần đọc 1 **luôn** ĐẠT. Lần đọc 2 hoặc ĐẠT (run `190740`) hoặc **mất sạch** — 0 dòng thô, chứ
không phải dữ liệu sai. Riêng B-V4 qua được cả hai lần đọc. Bốn run PMAX4 dùng cùng một tệp nhị
phân giống từng bit, nên khác biệt không nằm ở firmware.

### Nghi can tiếp theo, chưa kiểm chứng

`scripts/m1s_check.py` **đóng cổng serial sau mỗi lần đọc rồi mở lại** cho lần kế: `read_kit()`
kết thúc bằng `finally: ser.close()`, vòng lặp `for attempt in range(1, args.repeat+1)` gọi lại
nó. Trong lúc cổng đóng, kit **vẫn phát liên tục**, nên bộ đệm FT2232 đầy và kênh có thể kẹt
đúng ở nhịp mở lại. Điều này khớp với việc lần đọc 1 luôn sống và lần đọc 2 mất sạch.

Cách kiểm mà **không nới tiêu chí**: thêm tuỳ chọn **giữ cổng mở** xuyên hai lần đọc — đọc hai
khối báo cáo liên tiếp từ cùng một luồng. Hai lần đọc vẫn độc lập về nội dung, thậm chí chặt hơn
vì không có gì khởi động lại ở giữa. Tuỳ chọn **mặc định tắt** để mọi số đã ghi nhận giữ nguyên
cách đo. Tôi **chưa làm** việc này — sửa script đo là chạm vào hạ tầng đã sinh ra mọi số đã công
bố, nên cần người dùng đồng ý trước.

### Dừng ở đây (quy tắc 2)

Bốn lần thử cho cùng một mục tiêu nhỏ, mỗi lần tốn của người dùng một thao tác vật lý. Không thử
tiếp trên kit cho tới khi có hướng mới. **B-V4 (mục tiêu chính của S7) đã ĐẠT trọn vẹn và đã vào
bảng chính** — việc còn thiếu chỉ là con số 317.878 của dòng 15, vốn đã có bằng chứng rải trên
bốn run.

### Việc tiếp theo / cần người dùng quyết

Ba lựa chọn, tôi nghiêng về (1):

1. **Thêm tuỳ chọn `--keep-open` cho `m1s_check.py`** (mặc định tắt, không đổi hành vi cũ), rồi
   đo lại PMAX4 một lần. Nếu đúng là lỗi đóng/mở cổng thì xong, và còn biết thêm nguyên nhân thật.
2. **Chấp nhận bằng chứng rải trên bốn run** cho dòng 15 và ghi rõ điều đó trong báo cáo — mọi
   tiêu chí đều có bằng chứng, chỉ không nằm trong cùng một run.
3. **Để nguyên**, đi tiếp sang S8; dòng 15 vẫn ở ngoài bảng chính.


## 2026-10-18 — S7 ĐẠT: B-V4 đo trên kit 243.641 chu kỳ, dự báo mức A sai 0,00 %

Người dùng rút/cắm lại cáp USB. UART sống lại (`...171`, "MIN" 10 lần). Đo lại và **ĐẠT**.

### Kết quả: 243.641 chu kỳ trên kit — bằng tuyệt đối dự báo đóng băng

Run `20261018-214712-kit`, 18,7 s (bitstream đã có trong cây bóng nên không tổng hợp lại):

| tiêu chí | kết quả |
|---|---|
| đối chứng TRƯỚC (`min/top.fs`) | ĐẠT — "MIN" 8 lần |
| CRC 5 tensor × 10 ảnh vs golden | **10/10** |
| dự đoán khớp golden | **10/10** |
| chu kỳ kit = Verilator từng ảnh | **BẰNG TUYỆT ĐỐI** (10/10 ảnh đều 243.641) |
| 2/2 lần đọc độc lập | **ĐẠT** |
| chốt `SRC_HASH` | **có** (`a7dca19c8cec`) |

**Chuỗi ba số bằng nhau tuyệt đối: dự báo mức A (đóng băng trước khi viết RTL) = Verilator =
kit = 243.641.** Sai số 0,00 %. Đây là phép kiểm **K2** của `docs/MO_HINH_CHI_PHI.md`, và là
lần đầu một dự báo mức A được đối chiếu số đo phần cứng thật.

**9,0 ms · 110,8 ảnh/s · 1,27 chu kỳ/MAC · IPC 0,970 · 36,89× so A-V0.** Phân rã trên kit:
conv1 109.636 (45,0 %) · pool1 3.288 · conv2 123.702 (50,8 %) · pool2 1.421 · dense 5.594.

Dòng 16 đã vào **bảng chính** của `docs/KET_QUA_TONG_HOP.md`.

### Quy luật UART: ba lần truyền dài mỗi lần cắm cáp

Sau khi đo B-V4 xong, tôi tranh thủ đo luôn PMAX4 (dòng 15 còn thiếu một run sạch). Nó **chết
đúng ở lần đọc 2** — lần thứ ba cùng một kiểu. Xếp theo thời gian thì quy luật rõ ràng:

| # | việc | độ dài truyền | kết quả |
|---|---|---|---|
| 1 | cắm lại cáp, đối chứng `min` | ngắn (~50 byte) | ĐẠT |
| 2 | B-V4 lần đọc 1 | dài (~4,8 KB) | ĐẠT |
| 3 | B-V4 lần đọc 2 | dài | ĐẠT |
| 4 | đối chứng `min` trước PMAX4 | ngắn | ĐẠT ("MIN" 9 lần) |
| 5 | PMAX4 lần đọc 1 | dài (~9,4 KB tồn) | ĐẠT |
| 6 | PMAX4 lần đọc 2 | dài | **0 byte — chết** |

Kênh UART của FT2232 chịu được khoảng **ba lần truyền dài** sau mỗi lần cắm lại cáp rồi chết;
chuỗi ngắn không làm nó chết. Lần trước (`190740` → `190840`) cũng đúng mẫu này.

**Hệ quả cho cách làm: mỗi lần cắm lại cáp chỉ đo MỘT cấu hình, và đo cấu hình quan trọng nhất
trước.** Phiên này vô tình kiểm chứng đúng điều đó — B-V4 đo trước nên ĐẠT trọn vẹn, PMAX4 đo
sau nên chết. Nếu lúc đó tôi đo PMAX4 trước thì có lẽ cả hai dòng đã xong.

`csv_restore()` lại chạy đúng: trả 10 dòng cũ của `bs6pmax4`, bỏ 10 dòng mới không đáng tin.

### Lỗi hạ tầng: thêm cấu hình S7 làm hỏng đặc tả S6 (hồi quy)

`./cdp kit --spec pipeline/specs/s6_pmax4.yaml` **không chạy được nữa**:

    ValueError: tham số RTL chưa đủ để phân giải: còn
    ['B-V3+PMAX4', 'B-V3+PMAX4@32K', 'B-V4']

`targets.resolve()` phân giải cấu hình theo (lõi, tập cờ, tham số RTL). Ba cấu hình S7 có **cùng
tập cờ** với `s6_pmax4.yaml` và chỉ khác nhau ở `DUAL_PORT` cùng `RAMKB` — mà `RAMKB` thuộc
firmware, **không nằm trong `rtl_params`**, nên không có cách nào phân biệt `B-V3+PMAX4` với
`B-V3+PMAX4@32K` bằng `rtl_params`. Tức việc thêm cấu hình mới ở phiên trước đã **âm thầm làm
hỏng một đặc tả đang chạy được** — không ai phát hiện vì không chạy lại đặc tả cũ.

Sửa: `spec.load()` nay dùng `expect.target` để **chốt thẳng tên cấu hình** khi đặc tả có ghi (cả
sáu đặc tả hiện tại đều ghi), và vẫn **kiểm nhất quán** lõi, tập cờ và từng tham số RTL — nên đây
là chốt chứ không phải đường tránh. Không có `expect.target` thì vẫn phân giải như cũ. Đã kiểm
cả 6 đặc tả: `example_bv3`, `s1_av0`, `s1_bv1`, `s1_bv3`, `s6_pmax4`, `s7_dualport` — tất cả ĐẠT
và ra đúng cấu hình mong đợi.

**Bài học**: thêm cấu hình vào `targets.py` phải chạy lại `./cdp spec` cho **mọi** đặc tả cũ.

### Lỗi báo cáo % RAM: đã sửa và thấy hiệu lực ngay

Lần chạy này in đúng: `31.588/32.768 byte (96,4 %, còn 1.180 byte cho ngăn xếp)` cho B-V4
(RAMKB=32) và `31.588/65.536 byte (48,2 %, còn 33.948 byte)` cho PMAX4 (64 KB). Trước khi sửa,
cả hai đều báo 48,2 %.

**Ràng buộc kéo theo cho S8**: B-V4 chỉ còn 1.180 byte ngăn xếp. Mô hình giữ lại lớn hơn (M1-L
gấp đôi kênh) gần như chắc chắn **không vừa** RAM 32 KB. Phải tính trước khi chọn mô hình ở S8 —
hoặc chọn mô hình nhỏ, hoặc đo mô hình giữ lại trên B-V3/B-V3+PMAX4 (RAM 64 KB) thay vì B-V4.

### Việc tiếp theo / cần người dùng

- **Để xong dòng 15 (PMAX4)**: cần người dùng rút/cắm lại cáp USB **một lần nữa**, rồi tôi đo
  **PMAX4 trước tiên** (`./cdp kit --spec pipeline/specs/s6_pmax4.yaml`), không đo gì khác trước
  nó. Khoảng 20 s.
- Sau đó: S8 (mô hình giữ lại) — nhưng phải giải quyết ràng buộc RAM 32 KB nói trên trước khi
  chọn mô hình.


## 2026-10-18 — S7: thử đo B-V4 trên kit — KHÔNG ĐẠT vì UART của kit chết giữa phép đo

Phiên này làm ba việc: thử đo B-V4 trên kit (thất bại, phân loại được), sửa một lỗi báo cáo
dung lượng RAM, và chỉnh lại đánh số các bước của kế hoạch pipeline.

### 1. Đo B-V4 trên kit: KHÔNG ĐẠT, nhưng đối chứng chỉ đúng nguyên nhân

Trước khi chạy, tôi kiểm riêng đường UART bằng thiết kế đã biết chạy: nạp `rtl/mycore/min/top.fs`
rồi đọc 2,5 s → `...171` cho **40 byte, thấy "MIN" 8 lần**. Đường đo sống, nên mới chạy phép đo.

`./cdp kit --spec pipeline/specs/s7_dualport.yaml` → run `20261018-212201-kit`:

| bước | kết quả |
|---|---|
| dựng firmware `cdp32` (RAMKB=32) | rc=0 · sha256 `2c5641d3d800a8c4…` |
| tổng hợp `bs7dp` trong cây bóng | rc=0 · **1.139,6 s** · bitstream 7.261.470 byte |
| **đối chứng TRƯỚC** | ĐẠT — thấy "MIN" **1.342 lần** trên `...171` |
| nạp `bs7dp/top.fs` (SRAM) | rc=0 |
| `m1s_check.py`, 2/2 lượt đọc | **0 dòng thô** cả hai lượt → `M1S_FAIL` |
| **đối chứng SAU** | **KHÔNG ĐẠT — 0 byte cả hai cổng** |

Đối chứng sau là chỗ quan trọng: cùng thiết kế `min` vừa phát 1.342 lần "MIN" trước phép đo, sau
phép đo phát **0 byte**. Nên đây **không phải lỗi thiết kế B-V4** — đường UART của kit chết giữa
phép đo. Đúng triệu chứng đã ghi nhiều lần: JTAG vẫn sống (`idcode 0x81b`, nạp `DONE`), chỉ kênh
UART của FT2232 chết, và nó chết trong lần truyền dài (M1-S in ~4.650 byte mỗi lượt) chứ không
chết với chuỗi ngắn.

CSV được `csv_restore()` trả về nguyên trạng (0 dòng mới, không mất dòng cũ) — đường lùi thêm ở
commit `3276883` chạy đúng như thiết kế.

### 2. Ba hướng gỡ không cần tay người, tất cả thất bại (quy tắc 2)

1. Nạp lại `min/top.fs` rồi đọc 3 s → 0 byte cả hai cổng.
2. Đóng/mở lại cổng và **đảo DTR/RTS** (False→True→False) trên cả hai cổng, xả bộ đệm, đọc lại
   3 s → 0 byte.
3. `openFPGALoader --reset` (FPGA reset qua JTAG) → nạp lại `min/top.fs` → đọc **6 s** → 0 byte.

Hết ba hướng. Theo quy tắc 2 và quy tắc 4 (việc vật lý do người dùng làm): **DỪNG, cần người dùng
rút và cắm lại cáp USB**. Không có cách nào power-cycle cổng USB bằng phần mềm trên macOS.

### 3. Kết quả phụ đáng ghi: luồng tổng hợp tái lập từng bit

Lần tổng hợp này chạy trong **cây bóng** (`pipeline/work/s1`), độc lập với lần dựng trước ở
`rtl/mycore/bs7dp/`. Hai bitstream **giống hệt từng bit**:

| | kích thước | sha256 |
|---|---:|---|
| `rtl/mycore/bs7dp/top.fs` (lần trước) | 7.261.470 | `22bbbe32918954ef…` |
| `pipeline/work/s1/.../bs7dp/top.fs` (lần này) | 7.261.470 | `22bbbe32918954ef…` |

`report.json` cũng khớp hoàn toàn: `utilization`, `fmax` (53,011024475 MHz), `critical_paths` —
cả ba trường bằng nhau tuyệt đối. Tức yosys → nextpnr-himbaechel → gowin_pack **tất định** cho
thiết kế này, kể cả khi chip đã chiếm 75,9 %. Điều này có giá trị cho bài báo: mọi số tài nguyên
và Fmax đã báo đều dựng lại được, không phụ thuộc thư mục hay thứ tự chạy.

### 4. Lỗi hạ tầng phát hiện và sửa: % RAM tính theo 64 KB cứng

`cdp` in `31.588/65.536 byte (48,2 %)` cho cấu hình RAM **32 KB**. `build.read_size()` chia cứng
cho 65536. Con số thật: **31.588/32.768 = 96,4 %**, **chỉ còn 1.180 byte cho ngăn xếp**. Đây đúng
là con số cần biết — Verilator chạy trọn 10 ảnh nên ngăn xếp đủ, nhưng biên độ mỏng tới mức phải
ghi lại, và mô hình giữ lại ở S8 (M1-L gấp đôi kênh) gần như chắc chắn **không vừa** RAM 32 KB.
Đã thêm `build.ram_bytes(t)` lấy `RAMKB` của chính cấu hình và in thêm phần dư.
(Dòng log trong run `20261018-212201-kit` vẫn là bản cũ vì run chạy trước khi sửa.)

### 5. Chỉnh lại đánh số bước của kế hoạch pipeline

Kế hoạch gốc gộp vòng mở vào S6 và đặt "mô hình giữ lại" ở S7, nhưng vòng mở đã sinh ra **hai**
ứng viên phần cứng hiện thực trọn vẹn, và kết quả cái thứ hai đã nằm ở `results/pipeline/S7/`.
Đã tách: S6 = phễu + PMAX4 (đánh dấu ĐẠT, 4 cặp dự báo–đo kit), S7 = bộ nhớ hai cổng (B-V4),
S8 = mô hình giữ lại, S9 = báo cáo. **Không đổi tên thư mục kết quả nào**; thêm bảng ánh xạ
thư mục ↔ bước ở đầu `docs/PIPELINE_PLAN.md`. `CLAUDE.md` đổi "(S0 → S8)" thành "(S0 → S9)".

### Việc tiếp theo / cần người dùng

- **Cần người dùng: rút cáp USB của kit ra, chờ ~5 giây, cắm lại.** Sau đó tôi chạy lại
  `./cdp kit --spec pipeline/specs/s7_dualport.yaml`. Lần này bitstream đã có trong cây bóng nên
  không mất 19 phút tổng hợp lại — phép đo chỉ còn ~2 phút.
- Nếu rút/cắm lại mà UART vẫn chết: triệu chứng này đã lặp nhiều lần và luôn tự hồi phục sau một
  lúc. Phương án dự phòng nếu không hồi: B-V4 đã có số Verilator đúng tuyệt đối và đúng từng bit
  (243.641 chu kỳ, `results/pipeline/S7/`), nên có thể ghi vào báo cáo là **"đo bằng mô phỏng,
  chưa xác nhận trên kit"** — đúng như dòng 15 (PMAX4) đã làm trước khi đo được.
- Chưa đưa B-V4 vào bảng chính `docs/KET_QUA_TONG_HOP.md` (vẫn thiếu phép đo kit).


## 2026-10-18 — S7: hiện thực bộ nhớ hai cổng — K2 sai số 0,00 %, nhưng LUT4 gấp 3,5 lần

Kit vẫn chết (kiểm lại: nạp `min/top.fs` được, đọc 0 byte cả hai cổng) nên làm trọn phần
không cần kit: hiện thực ứng viên bộ nhớ hai cổng và kiểm bằng Verilator + riscv-tests +
tổng hợp.

### K2: dự báo mức A đúng TUYỆT ĐỐI

| | chu kỳ | tăng tốc |
|---|---:|---:|
| dự báo mức A, đóng băng trước khi viết RTL | 243.641 | 1,3047× |
| **đo bằng Verilator** | **243.641** | **1,3047×** |

**Sai số 0,00 %.** ISS khớp Verilator tuyệt đối từng lớp từng ảnh. So với K3 (PMAX4, mức B,
lệch 0,37 %): mức A đúng tuyệt đối vì **không sửa mã, không thêm lệnh** → `n_c` giữ nguyên
từng con số (`instret` giống hệt 236.313) → `ΔC = Σ n_c·Δλ_c` là **đẳng thức**.

### Thiết kế

`DUAL_PORT=1` thêm cổng lệnh riêng (`imem_addr`/`imem_rdata`). Ở `S_EXEC` lõi đặt đồng thời
địa chỉ dữ liệu và địa chỉ lệnh kế → bỏ hẳn `S_MEM`, load/store về 1 chu kỳ. Kéo theo hai
thứ bắt buộc: **cổng ghi thứ hai** của tệp thanh ghi (cổng 1 ưu tiên khi trùng) và **đường
chuyển tiếp** `ld_fwd` cho lệnh ngay sau load (18,3 % số load). RAM thu 64 KB → 32 KB.

Mọi thứ thêm qua tham số mới mặc định tắt: `DUAL_PORT=0`, `RAMKB=64`, `RVT_LD/RVT_WORDS/
RVT_STACK` mặc định như cũ, `fw/link32.ld` và `tests/link_test32.ld` là tệp THÊM. Đã kiểm
`fw/start.S` sau khi tham số hoá `STACK_TOP`: dựng hai bản cùng `GIT_HASH`, firmware
**giống hệt từng bit**.

### Hai phép đối chứng

1. **Liên kết lại 32 KB không đổi số chu kỳ**: firmware 32 KB trên lõi MỘT cổng cho đúng
   **317.878** chu kỳ, y bản 64 KB. Hai bản khác đúng một lệnh (`lui sp,0x8`). Nên chênh
   lệch là **thuần vi kiến trúc**.
2. **Đúng từng bit**: CRC 5 tensor × 10 ảnh giống hệt giữa một cổng và hai cổng; `instret`
   giống hệt; cả 10 ảnh đều 317.878 → 243.641.

### Kết quả B-V4

243.641 chu kỳ = **9,02 ms = 110,8 ảnh/s = 36,89× so A-V0** · 1,269 chu kỳ/MAC ·
**IPC = 0,970** (nhánh A trên PicoRV32: 0,151). `conv2` xuống **0,89 chu kỳ/MAC** — dưới 1,
vì DOT4 làm 4 MAC mỗi lệnh.

Cổng kiểm: riscv-tests **48/48 ĐẠT**, `fence_i` ĐẠT, `ma_data` KHÔNG (y mọi cấu hình trước,
lệch địa chỉ cố ý trap) · Fmax **53,01 MHz** ĐẠT.

### Giá phần cứng: đắt, và phải truy mới hiểu

Cùng file RTL, chỉ khác `DUAL_PORT`: LUT4 **4.459 → 15.736** (×3,5; **75,9 %** chip),
DFF 580 → 1.661, BSRAM **32 → 32 khối** (`SP` → `DPB`, đúng như phép dò đoán),
Fmax 59,08 → 53,01 MHz.

LUT4 gấp 3,5 lần là bất thường nên tôi quy trách nhiệm bằng ba lần tổng hợp Yosys, mỗi lần
đổi đúng một thứ:

| | LUT1-4 | MUX2_LUT* | `RAM16SDP4` |
|---|---:|---:|---:|
| `DUAL_PORT=0` | 4.263 | 978 | **32** |
| `DUAL_PORT=1`, MỘT cổng ghi (bản dò, sai chức năng) | 5.943 | 2.538 | **32** |
| `DUAL_PORT=1`, HAI cổng ghi (bản thật) | **14.667** | **8.637** | **0** |

- bộ nhớ hai cổng tự nó: **+1.680 LUT**
- **riêng cổng ghi thứ hai: +8.724 LUT, +6.099 MUX**

Nguyên nhân: tệp thanh ghi 32×32 với MỘT cổng ghi + hai cổng đọc tổ hợp được map vào **32
khối `RAM16SDP4`** (RAM phân tán GW2A). Thêm cổng ghi thứ hai thì **không map được nữa** và
rơi về flip-flop + mux 32:1 mỗi bit.

**Đây là tương tác vi kiến trúc ↔ nguyên thuỷ FPGA mà mô hình λ hoàn toàn không thấy** —
đúng giới hạn số 2 đã ghi TRƯỚC ở `docs/MO_HINH_CHI_PHI.md`, nay đo thành con số.

Hiệu quả diện tích hai ứng viên đã hiện thực: PMAX4 **9,8 LUT4** cho mỗi 1 % tăng tốc, bộ
nhớ hai cổng **370** — **chênh 38 lần**. Cả hai đều ĐẠT ràng buộc, nhưng dưới ngân sách LUT
chặt thì PMAX4 thắng áp đảo.

### Lỗi hạ tầng phát hiện và sửa

- `cdp sim` so `SRC_HASH` do firmware tự báo với hash của `experiment/m1s` cho **mọi** cấu
  hình → mọi cấu hình S6/S7 bị báo lệch oan (`a7dca19c8cec` vs `c3966b0011df`) và run bị
  đánh KHÔNG ĐẠT dù mọi số đều đúng. Thêm `provenance.src_hash_for(t)` tính theo `fw_root`
  và `KERNELS` của chính cấu hình đó, cùng công thức với Makefile của nó.
- `riscv_tests.sh` ghim cứng `link_test.ld` và `--words 16384` → mọi bài hỏng trên RAM
  32 KB với lỗi `$readmem file address beyond bounds of array`. Thêm `RVT_LD/RVT_WORDS/
  RVT_STACK`, mặc định y cũ.
- Hai lần đọc Fmax khác nhau trong cùng log nextpnr: **29,76 MHz sau khi ĐẶT** và
  **53,01 MHz sau khi ĐỊNH TUYẾN**. Số cuối cùng (và số trong `report.json`) là 53,01.
  Tôi đã đọc nhầm số sau khi đặt trước khi kiểm — phải lấy dòng cuối.

### Bước tiếp theo mà kết quả chỉ ra

Cổng ghi thứ hai là **77 %** chi phí LUT của ứng viên. Kỹ thuật FPGA chuẩn cho tệp thanh ghi
nhiều cổng ghi mà vẫn dùng RAM phân tán: **hai bản sao** tệp thanh ghi (mỗi bản một cổng
ghi) cộng **bảng giá trị sống** 32 × 1 bit. Dự kiến ~64 `RAM16SDP4` + vài chục LUT thay vì
+8.724 LUT. Lần này phải đóng băng dự báo **diện tích** trước, không chỉ dự báo chu kỳ.

### Còn thiếu

**Chưa đo trên kit.** `bs7dp/top.fs` đã dựng xong, sẵn sàng nạp. Chưa đưa B-V4 vào bảng
chính `docs/KET_QUA_TONG_HOP.md` — y như dòng PMAX4.


## 2026-10-18 — S7: dò khả thi bộ nhớ hai cổng, và đóng băng dự báo mức A đầu tiên (phép kiểm K2)

Kit chết nên chuyển sang việc không cần kit: ứng viên **bộ nhớ hai cổng**, dự báo **mức A**
(chính xác, không phải ước lượng). Đây sẽ là **K2** — lần đầu một dự báo mức A được đối chiếu đo thật.

### Hạ tầng phải sửa trước

- `cdp profile/analyze` không chạy được cấu hình PMAX4: `run_one()` truyền `with_dot4`/`with_req`
  nhưng **thiếu `with_pmax4`** → ISS trap "lệnh custom-0 không được bật". Đã sửa.
- **Bảng profile chia sai phạm vi**: `cycles_by_sem` tính trên profile đã gộp 10 ảnh
  (`merge_profs`) nhưng dòng in chia cho `cycles_median` của **1 ảnh** → tỷ lệ gấp 10 lần, tổng ra
  **1000 %**. Lần trước tôi sửa phép kiểm đồng nhất mà bỏ sót đúng chỗ in bảng. Đã sửa, giờ tổng
  đúng 100 %.
- `estimate._load()` chỉ đọc `results/pipeline/S3/`. Cho tìm **S6 trước, rồi S3**, và `cdp analyze`
  của cấu hình mới lưu vào `results/pipeline/S6/` — **không chạm tệp S3 cũ** (quy tắc 2).

### Cấu hình mới qua ISS: khớp kit tuyệt đối, và bộ nhớ đã thành tường chắn

`./cdp analyze --target "B-V3+PMAX4"` → **317.878 chu kỳ, khớp tuyệt đối số đo kit**, đẳng thức
phân loại KHỚP (10 ảnh = 3.178.780). Tức K0 đạt cho cấu hình mới.

Tỷ trọng chu kỳ: `mac` 33,2 % · **`load` 39,3 %** · `store` 7,4 % · `addr` 8,7 % ·
`loop_ctrl` 6,2 % · `requant` 4,6 % · `other` 0,5 %.

**Truy cập bộ nhớ = 46,7 %, lớn hơn cả `mac`.** Đúng điều lý thuyết roofline dự đoán: SIMD hoá
phần tính rồi thì bộ nhớ thành tường chắn.

### Dự báo mức A, đóng băng trước khi viết RTL

Tự kiểm phương pháp trước: `est_lambda("B-V3", {load:1, store:1})` tái lập **đúng 285.167 chu kỳ /
1,2834×** — con số đã đóng băng trước đó. Phương pháp không đổi.

| cơ sở | λ load/store 2→1 | chu kỳ | tăng tốc |
|---|---|---:|---:|
| B-V3 | mức A | 285.167 | 1,2834× |
| **B-V3+PMAX4** | mức A | **243.641** | **1,3047×** |

243.641 chu kỳ = **9,02 ms = 36,89× so A-V0**. Ghi ở
`results/pipeline/S6/du_bao_BONHO2CONG_truoc_khi_hien_thuc.json`.

Vì sao là mức A chứ không phải B: **không viết lại mã, không thêm lệnh** → `n_c` giữ nguyên, chỉ λ
đổi, nên `ΔC = Σ n_c·Δλ_c` là **đẳng thức**. Khác PMAX4 (mức B) vốn phải giả định mã viết lại gọn
tới đâu — và đã lệch 0,37 % đúng vì giả định đó.

### Ba phép dò khả thi, trước khi viết RTL

**1. Yosys CÓ suy ra BSRAM hai cổng — nhưng 64 KB không vừa chip.**

| bộ nhớ | khối Yosys suy ra | vừa 46 khối? |
|---|---|---|
| 64 KB, một cổng (hiện tại) | 32 × `SP` | có |
| 64 KB, hai cổng | **64 × `DPB`** | **KHÔNG** |
| 32 KB, hai cổng | **32 × `DPB`** | **có — đúng bằng số đang dùng** |

Chế độ hai cổng thật mất **một nửa mật độ** mỗi khối. Đường khả thi: **thu RAM 64 KB → 32 KB và
dùng hai cổng**, số khối BSRAM **không tăng**. Rủi ro lớn nhất đã nêu trong file dự báo (Yosys rơi
về RAM bằng LUT → không vừa FPGA) **đã bị loại bỏ**.

**2. 32 KB có đủ không? Đo ngăn xếp hai cách độc lập.** `__heap_start = 0x7b64` = 31.588 byte.

| cách đo | độ sâu |
|---|---:|
| quét bộ nhớ, byte khác 0 thấp nhất trên `__heap_start` | 256 byte (chặn dưới) |
| theo dõi trực tiếp `min(x2)` trong ISS (`track_sp=True`, mới thêm) | **256 byte** |

Khớp tuyệt đối. Ở 32 KB: dư `32.768 − 31.588 = 1.180` byte, cần 256 → **VỪA, biên 4,6×**
(còn trống 924 byte — hẹp, firmware lớn thêm phải kiểm lại).

**3. Rủi ro nặng hơn BSRAM: xung đột load-use.** BSRAM có đầu ra qua thanh ghi. Với hai cổng, ở
`S_EXEC` đặt được đồng thời địa chỉ dữ liệu và địa chỉ lệnh kế → chu kỳ sau có cả hai. Nhưng dữ
liệu nạp phải ghi về thanh ghi **trong chính chu kỳ** lệnh kế đang thực thi. Lệnh kế dùng ngay
thanh ghi đó thì cần **đường chuyển tiếp**, không có thì phải **chèn một chu kỳ dừng** — tức
λ_load **vẫn 2** cho đúng những cặp phổ biến nhất (nạp rồi nhân-cộng ngay).

Đã **đếm** bằng `track_ldu=True` mới thêm, **chỉ trong 10 cửa sổ đo**:

| | load | store | load-use ngay | tỷ lệ |
|---|---:|---:|---:|---:|
| B-V3+PMAX4 | 624.770 | 117.600 | 114.160 | **18,3 %** |
| B-V3 | 677.420 | 130.830 | 113.160 | 16,7 % |

| trường hợp | chu kỳ/ảnh | tăng tốc |
|---|---:|---:|
| **có** chuyển tiếp (mọi load λ=1) | **243.641** | **1,3047×** |
| **không** chuyển tiếp (dừng ở load-use) | 255.057 | 1,2463× |

Khoảng rộng 11.416 chu kỳ = **4,7 %, hẹp** → **ứng viên đáng làm trong cả hai trường hợp**, không
cần chờ giải quyết chuyện chuyển tiếp mới quyết định. Nhưng RTL cuối cùng phải ghi rõ thuộc trường
hợp nào, vì đó là điều kiện của dự báo mức A. Cả hai đã đóng băng thành tệp riêng.

**Đối chứng chéo**: số "có chuyển tiếp" tính độc lập từ đếm theo cửa sổ ra **đúng 243.641**, khớp
tuyệt đối `est_lambda()`. Hai đường tính khác nhau, cùng kết quả.

### Lại gặp bẫy trộn phạm vi

Lần đầu tôi đếm load-use trên **toàn lần chạy** ISS (`iss.cycle` = 9.041.066 chu kỳ, gồm cả phần in
UART) thay vì trong 10 cửa sổ đo (3.178.780). Tỷ lệ và dự báo sai hết. Phép kiểm cứu được: tổng cửa
sổ của B-V3+PMAX4 phải **bằng đúng** 10 × 317.878 — và chỉ bằng khi đếm theo cửa sổ.

Chi tiết liên quan: với **B-V3**, tổng 10 cửa sổ (3.659.267) **không** bằng 10 × trung vị
(3.659.920) vì 10 ảnh lệch nhau chút ít; với **B-V3+PMAX4** thì bằng đúng vì cả 10 ảnh đều 317.878.

### Kiểm hồi quy

Đã chạm vòng chạy nóng của ISS nên kiểm lại: B-V3 365.992/365.992 **bằng tuyệt đối** từng lớp từng
ảnh · B-V1+DOT4+C1 487.865/487.865 bằng tuyệt đối · A-V3 1.842.219/1.842.219 sai số 0,0 %.
Không hồi quy.

Việc nhỏ còn nợ: `cdp iss --target` chỉ nhận **một** cấu hình (lấy cái cuối) trong khi
`cdp profile --target` lặp được. Chưa sửa.


## 2026-10-18 — S6: lượt đo PMAX4 sạch thất bại lần 2, và lỗi mất dữ liệu do chính bản sửa của tôi

Mục tiêu: một run duy nhất đạt 2/2 lần đọc **và** chốt `SRC_HASH` để đưa dòng 15 vào bảng chính.

UART **đã hồi phục** giữa hai lượt (nạp `min/top.fs`, đọc được 20 byte / 4 lần "MIN" ở `...171`,
trước đó là 0 byte). Chạy `cdp kit --spec s6_pmax4.yaml` → run `20261018-192413-kit`:

| đối chứng trước | đo | đối chứng sau |
|---|---|---|
| **ĐẠT** — 8 lần "MIN" ở `...171` | `check` treo **84,7 s**, **0 dòng CSV**, không lần đọc nào hoàn tất | **0/0 ở cả hai cổng** |

Tệ hơn lần trước (`190840` còn hoàn tất được lần đọc 1). Quy luật đang thấy: UART sống qua phép đối
chứng (chuỗi ngắn ~20 byte, phát liên tục) nhưng chết trong lần truyền dài của M1-S (~4.650 byte mỗi
lần đọc). Sáng nay cùng lệnh này chạy 6,5 s là xong.

**Dừng phần kit theo quy tắc 5** sau 2 lượt. Không thử lượt 3: đối chứng đã chứng minh đường đo đang
chết, nên lượt sau sẽ bị chặn ngay ở bước đối chứng trước (`cdp kit` có sẵn đường thoát sớm đó).
Cần rút/cắm lại cáp USB — thao tác vật lý, quy tắc 4.

### Lỗi của tôi: bản `csv_drop()` vừa thêm làm MẤT số đo cũ

`csv_drop()` tôi thêm ở mục trước xoá 10 dòng cũ **trước** khi đo. Phép đo chết giữa đường và không
ghi lại gì → CSV còn **0 dòng**. Tức bản sửa cho một lỗi (ghi nối thành 20 dòng) đã tạo ra lỗi nặng
hơn (mất sạch số đo). Phục hồi được vì đã lưu trữ và commit `results/pipeline/S6/kit/m1s_s6_kit.csv`
**trước** khi chạy lại — đúng lý do quy tắc "lưu log thô" tồn tại.

Đã sửa đúng cách: `csv_drop()` trả về bản sao các dòng đã xoá, và `csv_restore()` đặt lại **y nguyên**
nếu phép đo không ĐẠT, đồng thời bỏ các dòng mới không đáng tin → CSV về đúng trạng thái trước khi
chạy. Bài học: một bản sửa xoá dữ liệu trước khi có dữ liệu thay thế thì phải có đường lùi.


## 2026-10-18 — S6 phần 3: đo PMAX4 trên kit thật — 317.878 chu kỳ, 28,27× so A-V0

Người dùng cắm kit. Ba phép đo, log đầy đủ ở `results/pipeline/S6/kit/`.

### Kết quả

| biến thể | chu kỳ/ảnh | ms | chu kỳ/MAC | ảnh/s | so A-V0 | run |
|---|---:|---:|---:|---:|---:|---|
| B-V3 (`WITH_PMAX4=0`) | 365.992 | 13,6 | 1,91 | 73,8 | 24,56× | `20261018-190322-kit` |
| B-V3+PMAX4 | **317.878** | **11,8** | **1,66** | **84,9** | **28,27×** | `20261018-190740-kit` |

Hai lớp pooling: 54.991 → 6.899 chu kỳ (**−48.092**). pool1 42.472 → 4.978, pool2 12.519 → 1.921.

**B-V3 = 365.992 tái lập CHÍNH XÁC con số đã công bố** (dòng 14 bảng chính), nhưng dựng từ bản RTL
**đã chứa** logic PMAX4 với `WITH_PMAX4=0`. Đây là bằng chứng trên phần cứng thật rằng tham số mới
không làm hồi quy hành vi cũ — đúng quy tắc "biến thể mới chỉ thêm qua tham số mới, mặc định giữ
hành vi cũ". Phép đo này cũng đóng lại việc kiểm kit còn treo từ S1.

### Dự báo vs đo — mức B tự nhận là chặn dưới, và bị số đo vượt qua

| | chu kỳ | tăng tốc | vai trò |
|---|---:|---:|---|
| chặn trên Amdahl (mức C) | 314.561 | 1,1635× | lợi ích nhiều nhất có thể |
| dự báo mức B (chặn dưới của lợi ích) | 316.695 | 1,1557× | lợi ích ít nhất theo mô hình |
| **đo thật** | **317.878** | **1,1514×** | |

Sai số **+0,37 %**. Thứ tự: `314.561 < 316.695 < 317.878`.

- Chặn trên Amdahl **được tôn trọng** (1,1514× < 1,1635×) — mức C làm đúng việc.
- Chặn dưới mức B **bị vi phạm 0,37 %** → **mức B không phải chặn dưới thật, chỉ là ước lượng có
  điều kiện.** Phải sửa cách gọi nó trong `docs/MO_HINH_CHI_PHI.md`.
- Nhưng điều kiện đã ghi TRƯỚC và chỉ **đúng hướng lệch**: file dự báo đóng băng viết sẵn *"nếu
  trình biên dịch sinh thêm lệnh địa chỉ/vòng lặp thì lợi ích thấp hơn"*. Lợi ích thật đúng là
  thấp hơn. Ghi giả định ra trước nên biết **tại sao** lệch, không chỉ biết **là** lệch.

### Giá phần cứng — cùng một file RTL, chỉ khác `WITH_PMAX4`

| | LUT4 | ALU | DFF | Fmax |
|---|---:|---:|---:|---:|
| `WITH_PMAX4=0` | 4.211 | 968 | 580 | 65,89 MHz |
| `WITH_PMAX4=1` | 4.359 | 1.008 | 580 | 55,26 MHz |
| chênh | **+148** (+3,5 %) | +40 | 0 | −10,6 MHz |

Cả hai ĐẠT ràng buộc 27 MHz. **148 LUT4 cho 1,1514×.**

### Hai lỗi của tôi

1. **So LUT4 giữa hai bản RTL khác nhau.** Lần đầu tôi lấy 4.359 (PMAX4) trừ 5.073 (`bv1dcr` dựng
   từ bản RTL **cũ**) → kết luận vô lý *"thêm một lệnh tiết kiệm 714 LUT4"*. Tự phát hiện vì con số
   vô nghĩa. Sửa: dựng `WITH_PMAX4=0` trên **đúng file RTL đó** → 4.211 → giá thật **+148 LUT4**.
   Bằng chứng mới cho cạm bẫy số 5: hai văn bản RTL tương đương logic lệch tới 862 LUT4 / 10 MHz.
2. **`cdp kit` ghi nối CSV không xoá dòng cũ** → `m1s_s6.csv` có 20 dòng cho một biến thể.
   `scripts/branch_b_measure.sh` đã có `drop()` đúng cho việc này mà tôi không bọc lại. Đã thêm
   `csv_drop()` vào `pipeline/cdp/kit.py`. Lần này vô hại (cả 20 dòng đều 317.878) nhưng nếu hai
   lần đo khác nhau thì trung vị vô nghĩa. Đã dọn CSV về 10 dòng.

### UART của kit chết giữa phép đo — phân loại được nhờ đối chứng

Run `20261018-190840-kit` (lần đo lại có chốt `--src-hash`):

| đối chứng trước | đo | đối chứng sau |
|---|---|---|
| **ĐẠT** — 9 lần "MIN" ở `...171`, 0 ở `...170` | lần đọc 1 **ĐẠT đủ tiêu chí**, lần đọc 2 **0 dòng thô** | **0/0 ở cả hai cổng** |

Kiểm thêm bằng tay: `openFPGALoader` nạp `min/top.fs` vào SRAM **thành công** (JTAG tốt), đọc 8.000
byte từ cả hai cổng được **0 byte**. Đúng triệu chứng đã ghi: UART của BL616 chết sau vài phép đo,
JTAG vẫn tốt, chỉ rút/cắm lại cáp USB mới hồi phục. **Phép đối chứng đã làm đúng việc của nó:
phân biệt "thiết kế sai" với "đường đo chết".** Không có nó thì `M1S_FAIL` sẽ bị đọc oan là PMAX4 sai.

### Điều còn thiếu — nói thẳng

Tiêu chí ghi nhận đòi **đồng thời** 2/2 lần đọc **và** chốt `SRC_HASH`:

| dòng | CRC+dự đoán+kit=Verilator | 2/2 lần đọc | chốt `SRC_HASH` |
|---|---|---|---|
| B-V3 | ĐẠT | **2/2** | **có** (`c3966b0011df`) |
| PMAX4 run `190740` | ĐẠT | **2/2** | không chốt |
| PMAX4 run `190840` | ĐẠT ở lần đọc 1 | 1/2 | **có** (`a7dca19c8cec`) |

Hai run PMAX4 nạp **cùng tệp nhị phân giống từng bit** (`firmware.hex sha256 = e477ee6122…` ở cả hai
`meta.json`), nên lần đọc 1 của `190840` chứng minh chính tệp cho 2/2 ở `190740` có `SRC_HASH` khớp
mã nguồn hiện tại. Mọi tiêu chí **đều** có bằng chứng, nhưng **rải trên hai run**, không phải một run.

Đã kiểm chốt `--src-hash` không vô hiệu: `m1s_s6/main.c:176` phát `M1S,src,<hash>`,
`m1s_check.py:218` so sánh `k.get("src")` — firmware không phát thì giá trị là `None` và vẫn bị từ chối.

→ **Chưa đưa dòng PMAX4 vào bảng chính** `docs/KET_QUA_TONG_HOP.md`. Ghi ở mục riêng, nói rõ mức bảo
đảm. Vào bảng chính sau một run duy nhất đạt 2/2 **và** chốt hash — việc đó cần **rút/cắm lại cáp USB**
(quy tắc 4: thao tác vật lý do người dùng làm). Đã hỏi người dùng.


## 2026-10-18 — S6 phần 2: hiện thực PMAX4 — dự báo sai 0,37 %, đúng từng bit, 5/5 cổng kiểm ĐẠT

Người dùng giao toàn quyền quyết. Tôi chọn hiện thực **PMAX4** trước (lệnh mới thêm được bằng
tham số mặc định tắt, rủi ro thấp) thay vì bộ nhớ hai cổng (lợi ích lớn hơn nhưng sửa đường bộ
nhớ, rủi ro Fmax/BSRAM cao hơn). Không tự quyết được: cắm kit.

PMAX4 là ứng viên **do S5 sinh ra ở chế độ mù** (4/6 lần chạy AI đề xuất), nhắm đúng chỗ mà S3
chỉ ra là chưa ai chạm: `pool1`+`pool2` = 15,0 % chu kỳ B-V3, 34 % trong đó là lệnh so sánh/chọn.
`custom-0, funct3=010, funct7=0`, `rd[i] = max((int8)rs1[i], (int8)rs2[i])`, **1 chu kỳ**.

### Dự báo đóng băng TRƯỚC khi hiện thực, rồi đo
| | chu kỳ/ảnh | tăng tốc |
|---|---:|---:|
| B-V3 gốc | 365.992 | 1,000× |
| **dự báo** (ghi sổ cái trước khi viết dòng mã nào) | **316.695** | **1,1557×** |
| **đo thật** (ISS, RTL xác nhận) | **317.878** | **1,1514×** |
| | | **sai số +0,37 %** |

`pool1` 42.472 → **4.978** (8,5×) · `pool2` 12.519 → **1.921** (6,5×) · ba lớp còn lại không đổi
một chu kỳ nào. Số lệnh PMAX4 = **1.314/ảnh** = đúng (169·2 + 25·4)·3 theo hình học.

### PQ1: độ chính xác của dự báo KHÔNG phải hằng số
| ứng viên | dự báo | đo | sai số |
|---|---:|---:|---:|
| DOT4 | 1,524× | 2,313× | −34,1 % |
| REQ | 1,180× | 1,333× | −11,5 % |
| **PMAX4** | **1,1557×** | **1,1514×** | **+0,37 %** |

Dự báo mức B chính xác khi lệnh mới **thay đúng một chỗ** trong một vòng đơn giản (pooling), và
lệch nhiều khi việc biến đổi mã còn kéo theo thay đổi khác (DOT4/REQ cắt thêm địa chỉ/vòng lặp).
Đây là phát hiện có ích hơn một con số sai số trung bình.

### Năm cổng kiểm chứng (SPEC 4.3) — ĐẠT HẾT
- **Vector ngẫu nhiên**: RTL và plugin ISS cho **cùng CRC `649A9D5E` trên 1.000.000 vector**
  (đúng 1.000.000 lệnh PMAX4 đã chạy; dãy có ép biên −128/127 mỗi 64 vector).
- **riscv-tests** với `WITH_PMAX4=1`: **48/48** RV32IM (`fence_i` ĐẠT, `ma_data` không — như lõi gốc).
- **Đúng từng bit M1-S**: CRC32 cả 5 tensor × 10 ảnh khớp golden.
- **ISS = Verilator tuyệt đối**: 317.878 = 317.878, từng lớp từng ảnh.
- **Không hồi quy**: A-V0, B-V1, B-V3 với `WITH_PMAX4=0` bằng tuyệt đối số cũ.

### Chi phí phần cứng — và một LỖI CỦA TÔI đã tự bắt được
Phép so duy nhất có nghĩa: **cùng file RTL, cùng firmware, khác đúng một tham số**.
| | PMAX4=0 | PMAX4=1 | chi phí |
|---|---:|---:|---:|
| LUT4 | 4.211 | 4.359 | **+148** |
| ALU | 968 | 1.008 | **+40** |
| DFF / BSRAM / MULT18X18 | 580 / 32 / 4 | 580 / 32 / 4 | **0 / 0 / 0** |
| Fmax | 65,89 MHz | 55,26 MHz | **−10,63 MHz (−16 %)**, vẫn 2,05× mức cần |

**Lỗi tôi đã mắc**: ban đầu tôi so LUT4 của bản có PMAX4 (4.359) với `bv1dcr` cũ (5.073) và ra
kết luận **vô lý rằng thêm lệnh làm GIẢM 714 LUT4**. Nguyên nhân: hai số đó đến từ **hai phiên
bản `mycore.v` khác nhau**. Tổng hợp lại `WITH_PMAX4=0` trên cùng file RTL cho 4.211 → chi phí
thật là +148.

**Bằng chứng MỚI, mạnh hơn, cho cạm bẫy số 5**: `bv1dcr` cũ và `bs6off` có **cùng tham số** và
`mycore.v` **tương đương logic** (các dây `pmax4_val` bị cắt bỏ khi tham số = 0), nhưng lệch
**862 LUT4 (−17 %)** và **10 MHz Fmax**. Hệ quả phải ghi vào luận văn: mọi con số "chi phí LUT
của một lệnh" chỉ đáng tin nếu đến từ một cặp A/B khác nhau **đúng một tham số** trên **cùng một
file nguồn**.

### Hạ tầng mới
- `rtl/mycore/mycore.v`: tham số `WITH_PMAX4`, **mặc định 0** (đã chứng minh không hồi quy).
  `soc_b.v`, `top_b.v`, `Makefile` truyền tham số; Makefile thêm `bs6pmax4` / `bs6ref` / `bs6off`.
- `pipeline/cdp/iss/ext/pmax4.py` — mô hình tham chiếu (khớp mô hình C 200.000/200.000 vector).
- `experiment/m1s_s6/` (thư mục MỚI): hạ tầng firmware trên đỉnh B-V3, kernel thay được; cổng
  kiểm bắt buộc **ĐẠT** (`kernels_v3.c` cho đúng 365.992 chu kỳ bằng tuyệt đối như B-V3);
  `cand/pmax4.c` (kernel pooling dùng PMAX4) và `pmax4_vectors.c` (firmware kiểm vector).
- `cdp/b1/prepare_s6.py`: giải chỉ thị tiền xử lý với bốn macro tính năng **BẬT**.

### Vấn đề, đã thử
`pmax4_vectors.c` lúc đầu trap ở `start.S` (`sw` lệch địa chỉ) vì chương trình không có biến
`.bss` nào nên ranh giới `.bss` lẻ; thêm một biến `aligned(4)` là xong.

### Chưa làm — và không tự quyết được
**Đo trên kit.** Chưa thấy `/dev/cu.usbserial*`. Bitstream `bs6pmax4/top.fs` đã dựng xong, sẵn
sàng nạp SRAM. Khi đo sẽ gộp luôn phép kiểm đường đo `cdp kit` hoãn từ S1.

## 2026-10-18 — S6 phần 1: `cdp estimate` — dự báo GHI TRƯỚC, và PQ1 đã có câu trả lời cho tầng L1/L2

Theo yêu cầu người dùng: làm phần dự báo trước (chưa cần kit), lưu đủ để viết báo cáo.
Nguyên tắc SPEC 0.3: dự báo ghi vào sổ cái **trước** khi hiện thực, **không sửa lùi**.

### Ba mức dự báo, độ tin cậy khác nhau hẳn — không được trộn
- **A. Đổi λ** (L3): ΔC = Σ n_c(λ_cũ − λ_mới). **Chính xác theo mô hình** đã khớp tuyệt đối
  với RTL trên 14 cấu hình (S2) và trên mã mới do AI sinh (S4).
- **B. Gộp/vector hoá một mẫu lệnh** (L1/L2): ΔC = n_nhóm(Σλ_bị_thay − Σλ_mới). **Chặn dưới.**
- **C. Chặn trên Amdahl**: ≤ 1/(1−f). Cho mọi ứng viên, nhưng là **chặn trên**, không phải dự báo.

### PQ1 cho tầng L1/L2 — trả lời được NGAY, không cần viết thêm RTL
Ba ứng viên ưu tiên đã có số đo thật từ giai đoạn trước:
| | dự báo (mức B) | đo thật | sai số |
|---|---:|---:|---:|
| DOT4 | 1,524× | **2,313×** | **−34,1 %** |
| Bố cục dữ liệu | 1,370× | **1,294×** | **+5,9 %** |
| REQ | 1,180× | **1,333×** | **−11,5 %** |
| | | **|sai số| trung bình** | **17,2 %** |

**Dự báo mức B lệch tới 34 %, và lệch CÓ HỆ THỐNG theo hướng thiếu** ở hai ứng viên gộp lệnh.
Nguyên nhân truy được từ chính dữ liệu S3: mức B chỉ tính các lệnh **bị thay trực tiếp**, còn
việc biến đổi mã để dùng lệnh mới **còn cắt thêm** chi phí địa chỉ và điều khiển vòng. Ngược
lại, bố cục dữ liệu **trả giá thêm** (+addr +loop_ctrl +store) nên ở đó dự báo lại **THỪA**.

Hệ quả phương pháp, phải ghi vào luận văn: **mức B dùng để XẾP HẠNG ứng viên thì được, dùng
để CAM KẾT một con số thì không.** Chỉ mức A mới cam kết được — và chưa ứng viên mức A nào có
số đo đối chứng, nên đó chính là việc của phần đo kit.

### Dự báo chính xác (mức A) cho các ứng viên L3
| ứng viên | cơ sở | dự báo |
|---|---|---:|
| Bộ nhớ hai cổng (load/store 2→1 ck) | B-V3 | **1,283×** (285.167 chu kỳ) |
| Bộ nhớ hai cổng | B-V1 | 1,305× |
| Nhân 1 chu kỳ (λ_mul 2→1) | B-V3 | **1,000×** |
| Hạ λ lệnh lượng tử hoá lại (2→1) | B-V3 | 1,021× |
| Bộ nhớ hai cổng + mọi phép nhân 1 ck | B-V3 | **1,317×** → C = 277.823 = đúng N, **IPC = 1,00** |

"Nhân 1 chu kỳ cho 1,000× trên B-V3" **không phải lỗi**: ở B-V3 thì n_mul = 0 (mọi MAC đã là
lệnh 4 làn, requantize đã là một lệnh). Muốn hạ chi phí số học ở B-V3 phải hạ λ của chính lệnh
lượng tử hoá lại. Ghi rõ chỗ này vì con số 1,020× ở `S3/summary.md` mục 5 dùng định nghĩa gộp
cả hai, dễ bị đọc thành mâu thuẫn.

### Dự báo được tới đâu, trên 78 ứng viên của S5
**32** ứng viên dự báo được chính xác (mức A, hầu hết là L3/L4/L5 có `timing_changes`);
**32** dự báo được dưới dạng chặn dưới (mức B, hầu hết L1/L2 có đủ mã hoá + ngữ nghĩa + độ trễ);
**14** chỉ có chặn trên.

Và một kết luận về chính chặn trên Amdahl: **nó KHÔNG phân biệt được các ứng viên** — hầu hết
đều nhắm `mac`+`load_data` cộng lại 85 % chu kỳ nên chặn trên của chúng gần như bằng nhau
(trung vị = lớn nhất ≈ 6,65×). Vì vậy **không dùng chặn trên để chọn top-K**.

### Đề nghị top-K (chờ người dùng quyết)
1. **Bộ nhớ hai cổng** — 1,283× trên B-V3, **mức A nên cam kết được**; không thêm lệnh mới,
   **không đổi firmware**; 7/7 lần chạy S5 đều đề xuất.
2. **PMAX4** — chặn trên 1,164×; nhắm đúng 15,0 % chu kỳ **chưa tối ưu nào chạm tới**; 4/6 lần
   chạy AI đề xuất.
3. Hạ λ lệnh lượng tử hoá lại — 1,021×, rất nhỏ nhưng gần như miễn phí nếu đã mở khối nhân.
4. MACC/FMAC có thanh ghi tích luỹ riêng — 5/6 lần chạy đề xuất nhưng **đặc tả chưa đủ** để
   tính mức B; cần làm rõ trước khi xếp hạng.

**Cảnh báo**: làm cả 1 và 2 thì **không được nhân hai hệ số** rồi coi là dự báo. Hai hướng tác
động lên các số hạng khác nhau của Σn_cλ_c nên *xấp xỉ* nhân được, nhưng đó là **giả thuyết cần
đo**, không phải dự báo.

### Lưu cho báo cáo
`results/pipeline/S6/`: `README_estimate.md` · `estimates_priority.json` (đủ công thức và từng
số hạng) · `du_bao_vs_do.csv` · `estimates_all_candidates.csv` (78 ứng viên) · `estimates_full.json`
· `estimate.log` · `so_cai_candidates.csv` (**90 dòng sổ cái** trạng thái `estimated`, có
`predicted_cycles`/`predicted_speedup`, git commit, run_id).

### Việc tiếp theo
Hiện thực top-K → `cdp verify` → **đo kit** (lần đầu cần kit; gộp luôn phép kiểm đường đo
`cdp kit` đã hoãn từ S1).

## 2026-10-18 — PIPELINE CDP bước S5 ĐẠT: AI mù tái khám phá DOT4, REQ, bố cục và bộ nhớ nhanh — và tìm thêm 34 ứng viên mới

Trả lời PQ3 và PQ4. Điểm xuất phát B-V1 (1.459.993 chu kỳ). Sáu lời gọi AI mù (3 `blind_open`
không cấp catalog + 3 `blind_catalog`) cộng một bộ sinh theo luật cố định làm đối chứng.

### Bảng tái khám phá
| | DOT4 | REQ | LAYOUT | FASTMEM |
|---|---|---|---|---|
| AI `blind_open` (3 lần) | **3/3** | **1/3** | **2/3** | **3/3** |
| AI `blind_catalog` (3 lần) | **3/3** | **3/3** | **3/3** | **3/3** |
| luật cố định (không AI) | có | **không** | có | có |

Mỗi lần chạy AI cho **12 ứng viên trải đủ 5 tầng L1–L5**, cả 6 tệp **hợp lệ lược đồ**.
Luật cố định cho 6 ứng viên, 4 tầng.

### PQ3: có, tái khám phá được
DOT4 và bộ nhớ nhanh hơn: 7/7 lần chạy. Bố cục: 6/7. REQ: 4/7. Ở `blind_catalog` thì **cả bốn
đáp án đều tìm lại được ở cả 3 lần**. Ở `blind_open` (không catalog), một lần tự nghĩ ra REQ chỉ
từ con số `requant 8,8 % chu kỳ`: *"gộp chuỗi làm-tròn-dịch-kẹp của requant int8 thành một lệnh
1 chu kỳ"*.

### PQ4: AI hơn luật ở đúng một chỗ, và chỗ đó có lý do rõ ràng
- **DOT4, LAYOUT, FASTMEM: luật cố định tìm được hết** ⟹ đây là những kết luận mà **chỉ cần
  profile là suy ra được**, không cần AI. Đó là một kết quả quan trọng và hơi phản trực giác:
  phần lớn giá trị nằm ở **phân tích**, không ở AI.
- **REQ là chỗ AI hơn**: luật `L1.fused_op` cần dữ liệu n-gram mẫu lệnh mà profile chưa đo nên
  **không đánh giá được** (ghi đúng như vậy, KHÔNG coi là "luật sai" — coi vậy sẽ thổi phồng AI).
- **Catalog giúp rõ rệt**: REQ 1/3 → 3/3, LAYOUT 2/3 → 3/3 ⟹ hai chế độ phải báo riêng.
- **Độ ổn định của AI chưa cao** khi không có catalog. Báo nguyên số, không chọn lần tốt nhất.

### Phần giá trị nhất: 34 ứng viên MỚI, ngoài bốn đáp án đã biết
| ý tưởng | số lần chạy đề xuất |
|---|---|
| nhân-cộng có thanh ghi tích luỹ riêng (MACC/FMAC/LMAC) | 5/6 |
| phát hai lệnh mỗi chu kỳ (dual-issue hẹp) | 5/6 |
| bộ sinh địa chỉ / nạp tự tăng | 5/6 |
| **lệnh max gói 4 làn cho pooling (PMAX4)** | **4/6** |
| nhân 1 chu kỳ (hạ λ_mul 2 → 1) | 4/6 |
| mở rộng tệp thanh ghi / bank tích luỹ | 1/6 |
| chia cơ số cao | 1/6 |

**PMAX4 là ứng viên đáng chú ý nhất**: S3 đã chỉ ra `pool1`+`pool2` chiếm 15,0 % chu kỳ của
B-V3 và **chưa có tối ưu nào chạm tới** (34 % chu kỳ của chúng là lệnh so sánh/chọn nên DOT4 vô
dụng ở đó). AI mù tìm đúng ứng viên cho chỗ đó ở 4/6 lần — **một tối ưu người chưa làm**.
Và L3 "nhân 1 chu kỳ" trùng đúng ứng viên mà mô hình chi phí ở S3 đã dự báo được sẵn (1,020×).

### Chế độ mù: cơ chế và bằng chứng
Mù **có cấu trúc** (`cdp blind`): tiến trình `claude` riêng, thư mục làm việc ngoài cây dự án,
prompt không nêu đường dẫn dự án. **Tự khai báo của 6/6 lần chạy**: ngữ cảnh thêm chỉ có
`~/.claude/CLAUDE.md` (Vnstock, không liên quan); **đọc ngoài: không có; lệnh ngoài: không có**.

`cdp propose` tự kiểm rò rỉ trước khi cấp, **dừng** nếu còn sót. Hai chỗ phải làm sạch:
`static.json` ghi "custom-0 đã dùng funct3 000 (DOT4) và 001 (REQ)" → với B-V1 sự thật là toàn
bộ không gian custom còn trống; và bảng λ bỏ hai dòng `custom_dot4`/`custom_req`. **Giữ** lớp
`requant` vì đó là tên công việc trong phần mềm, không phải tên giải pháp phần cứng.
Một lần chạy tự đặt tên ứng viên là `dot4` — không phải rò rỉ (chuỗi đó không có trong file nào
được cấp), chỉ là tên tự nhiên của phép tích vô hướng 4 làn.

### Hai lỗi của chính tôi đã sửa trong bước này
1. **Bộ chấm có dương tính giả**: nó tính LAYOUT cho ứng viên SIMD chỉ vì trường `risks` *nhắc
   tới* "cần đổi bố cục dữ liệu". Nhắc tới một thứ như rủi ro không phải là đề xuất thứ đó. Đã
   bỏ `risks` và `evidence` khỏi vùng quét (trường `evidence` trích số từ analysis nên chứa sẵn
   từ "requant" — trích một tỷ trọng không phải là đề xuất).
2. **Đối chứng bị đánh giá thấp không công bằng**: bản đầu đánh giá luật chỉ trên lớp mạng nóng
   nhất (`conv2`) nên ra 1 ứng viên; nhưng cơ hội gói 4 làn nằm ở `conv1`. Đã sửa thành đánh giá
   **từng lớp mạng** → 6 ứng viên. Nếu không sửa thì kết luận PQ4 sẽ sai theo hướng có lợi cho AI.

Ngoài ra sửa một lỗi đua trong `runctx.py`: hai tiến trình `cdp` khởi động cùng một giây tính ra
cùng `run_id` rồi cả hai `mkdir` → một lời gọi chết. Đã đổi sang `mkdir` rồi bắt `FileExistsError`.

### Việc tiếp theo
S6: `cdp estimate` toàn bộ ứng viên (giải tích + ISS), chọn top-K, hiện thực RTL, `cdp verify`,
rồi đo kit. Đây là lần đầu **cần kit** — và cũng là lúc gộp phép kiểm đường đo `cdp kit` đã hoãn
từ S1.

## 2026-10-18 — CHẶN rò rỉ ngữ cảnh cho chế độ mù: `cdp blind` (bắt buộc trước S5)

Vấn đề từ S4: subagent mù được sinh ra TỪ phiên điều phối, nên harness tự chèn `CLAUDE.md` của dự
án vào ngữ cảnh của nó — và `CLAUDE.md` có câu nêu đích danh **"thêm lệnh tùy biến (DOT4, REQ)"**,
tức đúng đáp án mà S5 phải tái khám phá. Subagent tự khai báo việc này ở cả 4 vòng B1.

### Cách chặn: đổi từ mù-bằng-chỉ-thị sang mù-bằng-CẤU-TRÚC
Chạy AI trong **một tiến trình `claude` riêng**, với **thư mục làm việc nằm ngoài cây dự án**.
`CLAUDE.md` được tìm từ thư mục làm việc đi lên, nên tiến trình đó không thấy `CLAUDE.md` của dự án.
Prompt cũng **không nêu đường dẫn** tới cây dự án, nên không còn con trỏ nào dẫn tới đáp án.

Đã thử cờ `--bare` (nó tắt hẳn "CLAUDE.md auto-discovery") nhưng cờ đó tắt luôn việc đọc keychain
nên không đăng nhập được ("Not logged in") → không dùng được. Cách đổi thư mục làm việc đạt cùng
mục đích mà vẫn chạy được.

### Kiểm bằng thực nghiệm, không tin suông
Chạy một phiên `claude -p` với thư mục làm việc trung tính và hỏi thẳng nó liệt kê mọi chỉ thị được
chèn vào ngữ cảnh, rồi hỏi có biết gì về dự án TinyML RISC-V / Tang Nano 20K hay hai lệnh DOT4, REQ.
Trả lời (nguyên văn): *"**Không.** Tôi không được cung cấp bất kỳ thông tin nào về dự án TinyML trên
RISC-V / Tang Nano 20K, cũng không có gì về hai lệnh tùy biến tên DOT4 hay REQ. Lần đầu tiên những
tên này xuất hiện trong context của tôi là ở chính câu hỏi của bạn."*
Log: `results/pipeline/S5/blind_probe.txt`.

### Công cụ: `cdp blind`
`pipeline/cdp/blind.py` + `./cdp blind --sandbox <dir> --prompt|--prompt-file … [--collect MẪU]`:
sao file được cấp sang thư mục trung tính → chạy `claude -p` ở đó → sao file kết quả về sandbox →
ghi `ai/{prompt.md, output.txt, meta.json}` gồm model, thư mục làm việc, hash từng file được cấp,
danh sách thông tin bị giữ lại, và **bản tự khai báo của chính AI** (prompt luôn buộc nó trả lời ba
dòng: ngữ cảnh thêm · file đã đọc ngoài thư mục · lệnh đã chạy ra ngoài).

Thử đầu-cuối: cấp 10 file hồ sơ, yêu cầu đọc một file và ghi `answer.md`. Kết quả sau 17 s đúng
(`conv2, conv1, pool1` và `1.978.697 chu kỳ` — khớp hồ sơ), và bản tự khai báo: ngữ cảnh thêm chỉ có
`~/.claude/CLAUDE.md` (Vnstock, không liên quan), **đọc ngoài: không có**, **lệnh ngoài: không có**.

### Hai giới hạn còn lại, ghi rõ
1. `~/.claude/CLAUDE.md` của người dùng **vẫn** được nạp (ở máy này là hướng dẫn cài "Vnstock",
   hoàn toàn không liên quan dự án). Không chặn được từ phía dự án.
2. Tiến trình vẫn chạy trên cùng hệ thống file. Nó không được cho biết đường dẫn cây dự án, và mỗi
   lần gọi đều phải tự khai báo đã đọc/chạy gì ra ngoài — nhưng đây là **ghi nhận**, không phải
   cách ly cứng.

### Hệ quả cho các kết quả đã có
S4 giữ nguyên nhãn **"mù một phần"** — không sửa lùi. Nếu sau này cần, có thể chạy lại một vòng B1
bằng `cdp blind` để so "mù bằng chỉ thị" với "mù bằng cấu trúc"; đó sẽ là một đối chứng về phương
pháp, không phải để thay số cũ.

## 2026-10-18 — PIPELINE CDP bước S4 ĐẠT: vòng B1 mù VƯỢT tối ưu phần mềm làm bằng tay

Người dùng đổi quyết định: làm S4 (trước đó kế hoạch ghi "bỏ qua"). Trả lời PQ2.

### Kết quả — hai con số, KHÔNG được trộn
| | chu kỳ/ảnh | so B-V0 | biên độ theo ảnh |
|---|---:|---:|---:|
| B-V0 (C thẳng, điểm xuất phát) | 1.978.697 | 1,000× | 0,02 % |
| **người làm bằng tay** (B-V1, KHÔNG cấp cho AI) | 1.459.993 | **1,355×** | 0,03 % |
| **AI mù, tốt nhất không phụ thuộc dữ liệu** (`r2c`) | **1.249.201** | **1,584×** | 0,03 % |
| **AI mù, tốt nhất kể cả phụ thuộc dữ liệu** (`r4a`) | **822.796** | **2,405×** | 13,70 % |

**PQ2: có, và vượt.** So sánh ngang hàng: **1,584× so với 1,355×**, tức AI cắt thêm 14,4 % chu kỳ
so với bản người làm — **sau hai vòng**. Đường cong: 1,000× → 1,227× → 1,584× → 2,073× → 2,405×
(cải thiện 18,53 % · 22,51 % · 23,58 % · 13,81 %). **12/12 ứng viên trong 4 vòng ĐÚNG TỪNG BIT.**
Vòng lặp **dừng theo quyết định của người dùng ở vòng 4**, chưa tới bão hoà (quy tắc dừng là 2 vòng
liên tiếp < 2 %; vòng 4 vẫn còn 13,81 %).

### Phát hiện đáng kể nhất: AI tìm ra một LỚP tối ưu mà người không dùng
Từ vòng 3, AI khai thác **tính thưa**: bỏ qua cả chùm phép nhân khi gặp giá trị 0 (`p1` là đầu ra
ReLU+MaxPool nên tỷ lệ 0 cao). Hợp lệ, đúng từng bit — nhưng làm số chu kỳ **phụ thuộc đầu vào**:
biên độ giữa 10 ảnh nhảy từ **0,03 %** lên **8,61 %** rồi **13,70 %**. Hệ quả phương pháp: từ đây
"tăng tốc" không còn là một hằng số của thiết kế mà là một **phân bố** phụ thuộc thống kê đầu vào,
nên phải báo kèm biên độ, và 10 ảnh là mẫu quá nhỏ cho loại tối ưu này.
Bản thủ công A-V1 và **mọi** cấu hình trong 14 cấu hình cũ đều không phụ thuộc dữ liệu (0,02–0,03 %).

### Xác nhận Verilator — và một kết quả ngoài dự kiến cho PQ1
`r2c`: ISS 1.249.201 = Verilator 1.249.201. `r4a`: ISS 822.796 = Verilator 822.796. Cả hai **bằng
tuyệt đối từng lớp từng ảnh**, CRC khớp golden. Ở S2 mô hình chu kỳ được kiểm trên 14 cấu hình **đã
biết**; đây là lần đầu nó dự báo cho **mã hoàn toàn mới** do AI sinh (cấu trúc vòng khác hẳn, có cả
nhánh phụ thuộc dữ liệu) và vẫn đúng tuyệt đối — bằng chứng cho PQ1 mạnh hơn hẳn việc chỉ khớp trên
các cấu hình đã hiệu chuẩn.

### Hạ tầng mù, và cổng kiểm của nó
`experiment/m1s_b1/` (thư mục MỚI): `main.c` + một `kernels.c` thay được. `cdp/b1/prepare.py` giải
chỉ thị tiền xử lý của sáu macro tính năng ở trạng thái **không định nghĩa** rồi cắt vùng kernel ra —
nếu đưa thẳng `main.c` gốc thì subagent thấy luôn bản đã tối ưu nằm trong `#ifdef OPT_KERNELS`.
**Cổng kiểm bắt buộc** (bài học số 3): firmware từ `kernels_v0.c` cho đúng 1.978.697 chu kỳ, bằng
tuyệt đối từng lớp từng ảnh như B-V0. Không kiểm trước thì mọi sai lệch sau sẽ bị gán cho AI thay vì
cho hạ tầng. Thêm `cdp b1 prepare|sandbox|eval`, `cdp/isa.py`, và `wrap.py` symlink được thư mục con.

### Chất lượng lập luận của subagent — ba điểm đáng ghi
1. **Nó dùng đúng cột "thanh ghi còn trống" của phân tích tĩnh S3 làm căn cứ định lượng**, và tự chẩn
   đoán ra rằng bản thắng vòng 2 (ghim 18 trọng số) **đã gây tràn thanh ghi**: *"`load_data` 97.938
   chu kỳ ≈ 48.969 truy cập, gấp ~2 lần số byte ảnh thật sự cần (24.336 `lb`), trong khi vòng `conv1`
   chỉ còn 3 thanh ghi trống"*. Vòng 4 nó đưa ra bản sửa.
2. **Nó tự suy ra rằng phần mềm một mình KHÔNG khai thác được DLP trên lõi này** (vòng 2): *"nạp
   32 bit cho 4 byte không có lợi — một `lw` tốn 2 chu kỳ nhưng tách 4 byte có dấu cần 7 lệnh dịch,
   tổng 9 > 8 chu kỳ của 4 lệnh `lb`"*. Vòng 3 nó tự sửa con số 7 thành 2 nhưng giữ kết luận. Đây
   chính là lý do **cần một lệnh phần cứng** — và nó suy ra chỉ từ bảng λ, không thấy DOT4.
3. Nó tính điểm hoà vốn của phép bỏ-qua-0 bằng λ của lõi (1 chu kỳ nhánh để bỏ 6 ⟹ hoà vốn ở 17 %
   số 0), và tự thêm khẳng định lúc biên dịch để build **dừng hẳn** nếu `M1S_C2 ≠ 16` thay vì cho
   kết quả sai.

### RÒ RỈ PHẢI GHI RÕ, và phải chặn trước S5
Hệ thống **tự chèn `CLAUDE.md` của dự án vào ngữ cảnh subagent ở cả 4 vòng** — subagent tự khai báo
mỗi vòng, kèm cả `~/.claude/CLAUDE.md` của người dùng (khối "Vnstock", không liên quan).
`CLAUDE.md` dự án có câu nêu đích danh **"thêm lệnh tùy biến (DOT4, REQ) để giảm số chu kỳ"**.
- Với S4: gần như vô hại — nhiệm vụ **cấm** dùng lệnh tùy biến/hợp ngữ, và `CLAUDE.md` không nói gì
  về biến đổi vòng lặp (thứ mà A-V1 làm). Nhưng vẫn phải coi đây là **mù một phần**.
- Với S5: **nghiêm trọng** — DOT4 và REQ chính là đáp án cần tái khám phá. Phải chặn trước khi chạy
  S5. Chưa có cách chặn kỹ thuật (việc chèn do harness làm, không do tôi); hướng đang tính: dựng
  sandbox ngoài cây dự án và/hoặc chạy subagent ở một phiên riêng không có `CLAUDE.md`.
- Ngoài ra, chế độ mù nói chung bảo đảm bằng **chỉ thị**, không bằng sandbox hệ điều hành.

### Việc tiếp theo
Chặn rò rỉ `CLAUDE.md` rồi mới sang S5 (sinh ứng viên phần cứng mù + bộ sinh theo luật đối chứng).
Nếu muốn chốt S4 ở mức bão hoà thì chạy tiếp vòng 5+ (mỗi vòng ~13 phút).

## 2026-10-18 — S3 bổ sung: phân tích TĨNH (`cdp static`) — áp lực thanh ghi, phụ thuộc vòng lặp, không gian mã lệnh

Theo yêu cầu của người dùng, thêm lớp phân tích tĩnh vào S3. Phân tích động cho biết chu kỳ đi
vào đâu; ba thứ dưới đây quyết định một lệnh mới có **khả thi** hay không, và chỉ đọc được từ mã.

### Công cụ
- `cdp/isa.py`: giải mã trường lệnh theo **dạng** lệnh (R/I/S/B/U/J). Cần thiết vì bit [24:20] là
  `rs2` ở dạng R/S/B nhưng là phần immediate ở dạng I, và bit [11:7] là `rd` ở dạng R/I/U/J nhưng
  là immediate ở dạng S/B — nhầm chỗ này đã gây một lỗi thật ở S3.
- `cdp/static_analysis.py` (`cdp static`): với mỗi vòng nóng — thanh ghi dùng/còn trống, đỉnh khoảng
  sống, thanh ghi mang theo vòng, chuỗi hồi quy (λ-weighted), phụ thuộc **qua bộ nhớ nội vòng**,
  tỷ lệ lệnh nạp liên tục 1 byte, và không gian mã lệnh còn trống.
- ISS thêm `memdep=True`: ghi pc của lệnh store ghi sau cùng vào mỗi từ bộ nhớ; khi load đọc từ đó
  thì ghi lại cặp (store, load). **Lọc bắt buộc**: chỉ tính cặp mà **cả hai** pc nằm trong cùng thân
  vòng — số thô vô nghĩa, vì `conv2` có 119.472 cặp nhưng phần lớn là phụ thuộc **giữa các lớp**
  (`conv2` đọc `p1[]` do `pool1` ghi), không chặn vector hoá.

### Ba kết quả, và chúng ràng buộc S5 như thế nào
| | kết quả đo | ràng buộc cho ứng viên |
|---|---|---|
| Áp lực thanh ghi | vòng nóng nhất của `conv2` (68,9 % chu kỳ B-V1) dùng **28/31 thanh ghi, còn 3** | mọi ứng viên L1/L2 phải dùng **đúng 2 nguồn + 1 đích**, không thêm trạng thái kiến trúc |
| Phụ thuộc vòng lặp | **0** phụ thuộc qua bộ nhớ nội vòng ở **mọi** vòng nóng; chuỗi hồi quy 1–12 ck so với 32–535 ck/vòng | vector hoá **hợp lệ**; hồi quy không phải rào chắn |
| DLP theo lớp | `pool1` 90 % và `pool2` 95 % lệnh nạp **liên tục 1 byte**, mỗi vòng còn **21** thanh ghi trống; `conv2` **0 %** (toàn nạp từ 4 byte) | pooling: gói 4 làn 8 bit được ngay; `conv2`: muốn SIMD rộng hơn **buộc** phải đổi bố cục dữ liệu |
| Không gian mã lệnh | `custom-0` còn 6 mã `funct3` (mỗi mã 128 `funct7`) + ba opcode `0x2b/0x5b/0x7b` trống hoàn toàn | không có ràng buộc về chỗ đặt lệnh mới |

Điểm đáng ghi: **áp lực thanh ghi giải thích đúng cạm bẫy số 6** của `KET_QUA_TONG_HOP.md`.
`REQ_BENCH` đo 9,56 chu kỳ mỗi requantize trong một vòng vi mô **không có áp lực thanh ghi**, còn
trong `conv2` thực tế tiết kiệm 16,6 — và giờ đã có số: vòng đó chỉ còn 3 thanh ghi trống.

Và một quan sát nữa: bố cục 4 pha (C1) **đổi `conv1` từ 86,5 % lệnh nạp liên tục 1 byte xuống 0 %**
(biến nạp byte thành nạp từ 4 byte) và giảm thanh ghi dùng từ 20 xuống 15. Đó chính là cơ chế của
hệ số 1,29× — nhìn thấy được ở mức tĩnh, không chỉ ở mức tỷ trọng chu kỳ.

### Giới hạn của phép đo này, ghi trước
Áp lực thanh ghi tính bằng khoảng sống trong thân vòng (lần dùng đầu → lần dùng cuối theo thứ tự
địa chỉ) nên là **chặn trên**: một thanh ghi có thể chết giữa hai lần dùng mà cách tính không thấy.
Thân vòng lấy theo cạnh nhảy ngược **đã thực sự chạy**, nên nhánh trong thân làm phép tính gần đúng.

## 2026-10-18 — PIPELINE CDP bước S3 ĐẠT: profile 3 tầng + phân tích, giải thích bằng số mọi hệ số đã đo

Phân tích firmware ở mức lệnh động cho **cả 14 cấu hình**. Kết quả quan trọng nhất không phải các
bảng, mà là **hai trần đã đo được**, vì chúng quyết định hướng tối ưu phần cứng tiếp theo.

### Tiêu chí ĐẠT
| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | profile 3 tầng (SPEC 2.2) | **ĐẠT** — hàm/lớp · vòng lặp · 7 lớp ngữ nghĩa cho từng lệnh động |
| 2 | ILP, DLP, byte/MAC, roofline | **ĐẠT** — đo trực tiếp, không hệ số tay |
| 3 | tổng chu kỳ profile = ISS | **ĐẠT khớp tuyệt đối 14/14**, cả tổng và từng lớp mạng |
| 4 | giải thích định lượng các hệ số đã đo | **ĐẠT** (bảng dưới) |
| 5 | chạy cho 5 cấu hình | **ĐẠT, vượt** — chạy cả 14 |

### Giải thích bằng số từng hệ số đã đo (chênh lệch chu kỳ TUYỆT ĐỐI)
| hệ số | nguồn cắt chính | % của tổng cắt |
|---|---|---:|
| **1,45×** tối ưu phần mềm | `loop_ctrl` 41,4 % + `addr` 32,8 % | **74,2 %** (+ `load_data` 25,9 %) |
| **1,36×** cùng tối ưu đó trên mycore | `addr` 35,0 % + `loop_ctrl` 30,0 % | 65,0 % |
| **4,26×** vi kiến trúc (cùng firmware) | `load_data` 47,8 % + `mac` 33,5 % | 81,3 % — win **đều** trên mọi lớp |
| **2,31×** DOT4 | `load_data` 54,9 % + `mac` 42,1 % | **97,0 %** |
| **1,29×** bố cục 4 pha | `mac` 60,4 % + `load_data` 40,0 % + `requant` 18,4 %, **trả giá** +`loop_ctrl` −7,5 % +`addr` −5,4 % +`store` −4,9 % | net |
| **1,33×** REQ | `requant` 61,0 % + phần `mac` của phép nhân 64 bit 42,2 % | **103,2 %** |

Mọi dự đoán của kế hoạch S3 đều đúng: A-V0→A-V1 cắt chủ yếu `addr`/`loop_ctrl`; DOT4 cắt chủ yếu
`mac`+`load_data`; REQ cắt chủ yếu `requant`.

### Hai trần đã ĐO ĐƯỢC — đây là đóng góp chính của S3
1. **Trần của lõi phát một lệnh mỗi chu kỳ.** Dùng mô hình $\Delta C=\sum n_c\Delta\lambda_c$ (không
   viết dòng RTL nào): bộ nhớ hai cổng cho **1,283×** trên B-V3, nhân 1 chu kỳ cho 1,020×, **cả hai
   cho 1,317×** (365.992 → 277.823 chu kỳ, 13,6 → 10,3 ms) — và khi đó **IPC = 1,00**, trần tuyệt đối.
   Muốn đi xa hơn **buộc** phải rời mô hình một lệnh/chu kỳ.
2. **Trần băng thông bộ nhớ, và nó đã gần.** `conv2` ở B-V1 có **4,52 byte/MAC**, chỉ còn **3,19×** là
   đụng trần ($B = 4/\lambda_{load} = 2$ byte/chu kỳ); sau DOT4 + bố cục 4 pha còn **2,06×**. Nghĩa là
   một lệnh tính toán mạnh gấp 4 lần DOT4 sẽ **không** cho 4×. Mọi ứng viên tính toán từ S5 trở đi
   **phải kèm** giải pháp băng thông.

Thêm một chỗ chưa ai chạm tới: `pool1`+`pool2` chiếm **15,0 %** chu kỳ của B-V3 và **không** được
DOT4 hay REQ giúp gì (max-pooling không có phép nhân; 34 % chu kỳ của nó là lệnh so sánh/chọn).
Chặn Amdahl 1,177×.

### ILP: dư thừa, nên không phải rào chắn
IPC lý tưởng (đường găng RAW đo trực tiếp) là hàng trăm đến hàng nghìn ở mọi lớp, trong khi IPC
thật 0,59–0,84. Nguyên nhân: GCC dùng con trỏ chạy nên mỗi tầng vòng lặp chỉ chuỗi phụ thuộc trong
tầng của nó, không nhân lên. Vậy SIMD / phát nhiều lệnh / mảng MAC **có** chỗ để khai thác — cái
chặn chúng là cổng bộ nhớ, không phải phụ thuộc dữ liệu.

### Công cụ mới
- `cdp/profile.py`: tầng 1 (bảng ký hiệu ELF, `cdp/iss/elf.py` tự viết), tầng 2 (cạnh nhảy ngược →
  vòng lặp, số vòng, chu kỳ trong thân), tầng 3 (7 lớp ngữ nghĩa).
- `cdp/analyze.py`: byte/MAC, trần bộ nhớ theo λ của từng lõi, Amdahl theo lớp, DLP theo khoảng
  cách địa chỉ, ILP theo đường găng.
- ISS thêm 6 phép đo khi bật `profile=True`: lược sử theo địa chỉ lệnh, cạnh nhảy, số lần nhảy của
  từng nhánh, byte nạp/lưu, đường găng RAW, khoảng cách địa chỉ từng load, và **hai vết lan truyền**
  (sau `mulh` → chuỗi requantize; sau `mul`/`DOT4` → chuỗi cộng dồn MAC). Chậm hơn ~30 %.

### Bốn lỗi đã gặp và sửa (đều là bẫy phương pháp, đáng ghi vào luận văn)
1. **Trường `rd` của lệnh `store` không phải thanh ghi đích** (bit đó là phần immediate). Ghi chiều
   cao phụ thuộc vào một thanh ghi ngẫu nhiên → đường găng bị đứt, IPC lý tưởng sai.
2. **Gộp `add` cộng dồn ra khỏi `mac`** làm tỷ trọng MAC bị báo thiếu (`other` phình lên 17,1 %).
   Nhân-cộng là một phép toán; đã gộp bằng vết "sau mul". `other` còn 1,4 %.
3. **Lệnh bộ nhớ bị gán vào `requant`** ở biến thể này nhưng `store_data` ở biến thể kia → sinh
   chênh lệch GIẢ +14.518 chu kỳ. Quy tắc đã chốt: **lệnh bộ nhớ luôn thuộc lớp bộ nhớ**, vì nó
   tiêu thụ băng thông và đó là thứ roofline quan tâm.
4. **Trộn phạm vi đo** (tử số 10 ảnh, mẫu số 1 ảnh) và **giải mã tĩnh gán mọi nhánh là "nhảy"**
   (λ=9 thay vì 5 trên PicoRV32) → đẳng thức kiểm tra lệch 287 và 123.093 chu kỳ. Lỗi thứ hai
   **không lộ ra trên mycore** vì ở đó cả hai λ đều bằng 1 — đúng kiểu lỗi chỉ hiện khi đổi lõi.

### Còn thiếu: ba việc phân tích TĨNH, cần trước S5
Phân tích hiện tại chủ yếu là động. Ba thứ tĩnh thực sự cần cho việc đề xuất phần cứng còn thiếu:
(1) **áp lực thanh ghi** trong vòng nóng — lệnh mới cần 2 nguồn + 1 đích, nếu vòng đã dùng hết thì
lợi ích bị tràn thanh ghi ăn mất (đây là lý do `REQ_BENCH` đo 9,56 chu kỳ nhưng thực tế tiết kiệm
16,6); (2) **phụ thuộc mang theo vòng lặp** — quyết định một vòng có vector hoá được hợp lệ hay
không; (3) **chỗ trống trong không gian mã lệnh** (`custom-0` đã dùng `funct3` 000 và 001).
Đã hỏi người dùng có thêm bước `cdp static` trước S5 hay không — **đang chờ trả lời**.

## 2026-10-18 — PIPELINE CDP bước S2 ĐẠT: ISS RV32IM + mô hình chu kỳ khớp TUYỆT ĐỐI cả 14 cấu hình

Dựng bộ mô phỏng tập lệnh và mô hình chu kỳ — dụng cụ đo $n_c$ cho lý thuyết
`docs/MO_HINH_CHI_PHI.md`. Tiêu chí của S2 chỉ yêu cầu PicoRV32 sai số ≤ 2 %; kết quả thực tế là
**cả 14 cấu hình bằng tuyệt đối 0,0 %, từng lớp, từng ảnh**.

### Tiêu chí ĐẠT của S2 và kết quả
| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | CRC ISS = golden cho cả 14 | **ĐẠT** 14/14 (CRC32 cả 5 tensor × 10 ảnh) |
| 2 | mycore: ISS = Verilator **tuyệt đối** từng lớp | **ĐẠT** 8/8 cấu hình |
| 3 | PicoRV32: sai số từng lớp ≤ 2 % | **ĐẠT, vượt xa** — 6/6 **bằng tuyệt đối 0,0 %** |
| 4 | Thời gian ISS ≤ 30 s mỗi ảnh | **ĐẠT** — 1,4–3,0 s/ảnh (~640k lệnh/s, Python thuần) |

### Đã dựng
- `cdp/iss/core.py`: RV32IM đầy đủ, CSR `cycle`/`instret`, MMIO đúng bản đồ `soc_b.v`. Nạp **đúng
  file `firmware.hex`** mà RTL nạp, nên không có khâu dịch lại nào làm lệch được.
- 14 lớp lệnh: `alu, shift, branch_taken, branch_nt, jal, jalr, load, store, mul, div, csr, misc,
  custom_dot4, custom_req`. Tách `shift` khỏi `alu` và tách `jal`/`jalr` là **bắt buộc** (xem dưới).
- `cdp/iss/ext/{dot4,req}.py`: ngữ nghĩa lấy đúng từ `mycore.v`. REQ đã kiểm **20.000/20.000 vector
  ngẫu nhiên** khớp mô hình C trong `main.c` (`sat_rdhmul` + `rdiv_pot` + clamp).
- `cdp/iss/timing/mycore.yaml`: λ **đọc từ RTL**, không hiệu chuẩn — alu/shift/branch/jal/jalr/csr = 1,
  load/store = 2, mul/REQ = 2, div = 34, DOT4 = 1 (FAST_ADDR=1); FAST_ADDR=0 thì mọi lệnh +1 và mỗi
  truy cập dữ liệu +1 nữa.
- `cdp/iss/calibrate.py`: hiệu chuẩn PicoRV32 bằng bình phương tối thiểu trên **300 phương trình**
  (6 cấu hình × 10 ảnh × 5 lớp), $n_c$ do ISS đếm, $C$ do Verilator đo.
- Cửa sổ đo: ISS nhận ra các lần đọc `rdcycle` và ghép thành cửa sổ **đúng như firmware tự đo**, nên
  đầu ra UART của ISS có y nguyên các dòng `M1S,*` và so sánh là so hai khối cùng định dạng.

### λ hiệu chuẩn của PicoRV32: phần dư ĐÚNG 0, và λ đều NGUYÊN
alu 5 · shift 5 · branch không nhảy 5 · branch nhảy 9 · jal 5 · jalr 8 · load 9 · store 9 · mul 6 ·
csr 5 · DOT4 6 · REQ 6 (div không xuất hiện).

Mọi λ đọc được nhất quán theo một quy luật duy nhất: **số chu kỳ lệnh + 2 chu kỳ cho mỗi lần dùng bus**
(bus của `F5_soc/soc.v` tốn 2 chu kỳ mỗi truy cập). Chênh λ_load − λ_alu = 4 = đúng hai lần giá bus —
đây chính là chỗ **84,9 % chu kỳ của A-V0** biến mất.

**Phép hiệu chuẩn tự tìm lại hai tham số RTL mà nó không được cho biết**: λ_shift = λ_alu ứng với
`BARREL_SHIFTER=1`, và λ_mul = 6 ứng với `ENABLE_FAST_MUL=1` (`feasibility/F5_soc/soc.v` dòng 85, 88).

### Ba cái bẫy đã gặp và cách gỡ (đáng ghi vào luận văn)
1. **Gộp `jal` với `jalr` làm λ ra phân số 6,2 — vô nghĩa vật lý.** Mọi cửa sổ đo có 2 lệnh nhảy, trừ
   `conv1` của biến thể C1 có **7** (vì gọi thêm `conv1_prep`), nên λ gộp ra trung bình phân số. Tách
   hai lớp thì hệ thành: λ_csr + 2λ_jalr = 21 và 3λ_jal + 2λ_jalr = 31.
2. **Vẫn còn một chiều suy biến** (hai mẫu cửa sổ, ba ẩn). Gỡ bằng điều kiện λ phải **nguyên, không
   âm**: còn đúng ba nghiệm, chọn nghiệm chuẩn nhỏ nhất (5, 8, 5) — cũng là nghiệm duy nhất đọc được
   theo quy luật "+2 chu kỳ bus". Đã ghi rõ trong tài liệu: **đây là một lựa chọn, không phải một phép
   đo.**
3. **Làm tròn λ bằng `int()` cắt 8,6 → 8 làm mỗi cửa sổ thiếu 1 chu kỳ** → sai số 0,0026 %. Nhỏ nhưng là
   sai hệ thống; đã sửa bằng tìm nghiệm nguyên đúng.

### Phép kiểm K1 của lý thuyết: ĐẠT 20/20 ảnh
`./cdp iss --check-k1`. Chỉ từ **bốn con số đo** + λ đọc từ RTL, giải hệ hai ẩn ra thành phần lệnh động:
| firmware | n_mem suy ra | n_mem ISS đếm | n_mul suy ra | n_mul ISS đếm |
|---|---:|---:|---:|---:|
| v0 | 413.735 | **413.735** | 206.778 | **206.778** |
| v1 | 341.337 | **341.337** | 206.752 | **206.752** |

Kiểm chéo bằng cấu trúc mô hình, không dùng phép đo nào: 192.064 MAC + 2 × 7.344 lần requantize =
**206.752** = đúng `n_mul` của v1.

**Hai chỗ chính phép đếm của ISS đã SỬA LẠI suy đoán ban đầu của tôi** (ghi lại vì đúng tinh thần
"công cụ tất định phán quyết"):
- `dense` có **đúng 4.000** phép nhân = 4.000 MAC, **không** requantize: 10 logit giữ nguyên int32 và
  argmax lấy trực tiếp. Bản lý thuyết đầu cộng thừa 2×10.
- v0 nhiều hơn v1 **đúng 26** phép nhân, toàn bộ trong `conv1` = **một phép nhân tính chỉ số cho mỗi
  hàng đầu ra** (26 hàng). Đó là một phần cụ thể của 1,45× mà tối ưu phần mềm A-V1 đã xoá.
- Bản đầu của mô hình nghịch còn lệch 16 lệnh vì trộn hai phạm vi: `instret` firmware tự báo bao luôn
  16 lệnh **giữa** các cửa sổ, còn $C$ chỉ cộng chu kỳ **trong** cửa sổ. Quy tắc rút ra: giải hệ **trên
  từng ảnh, trong cùng một phạm vi**. Lấy trung vị riêng từng đại lượng rồi mới giải cũng sinh lệch ±1
  vì `pool1` có luồng điều khiển phụ thuộc dữ liệu.

### Việc tiếp theo
S3: profile 3 tầng + phân tích ILP/DLP/byte-MAC/roofline. Đầu vào đã có: `n_c_theo_lop.csv`
(14 cấu hình × 5 lớp mạng × 14 lớp lệnh) và lược sử thực thi theo địa chỉ lệnh (`--pc-hist`).

## 2026-10-18 — PIPELINE CDP bước S1: tái lập qua `cdp` ĐẠT trên Verilator và tổng hợp · bỏ đo kit

Bọc hai Makefile và script có sẵn bằng `cdp`, rồi tái tạo ba cấu hình đã công bố (A-V0, B-V1, B-V3).
Không viết lại một dòng nào của luồng build/sim/tổng hợp/đo — `cdp` chỉ gọi `make` và `scripts/*.py`,
đọc log, so sánh, ghi sổ cái.

### Cách giải bài "không được sửa cây cũ": cây bóng
`experiment/m1s/v*/` và `rtl/mycore/bv*/` đã nằm trong git (130 + 839 file) và là bằng chứng của giai
đoạn trước, nên chạy `make` tại chỗ là ghi đè chúng. `cdp/wrap.py` dựng **cây bóng** `pipeline/work/s1/`:
chỉ gồm symlink tới mã nguồn, sắp đúng độ sâu để mọi đường dẫn tương đối trong hai Makefile
(`../../fw`, `../../scripts`, `../../hw`, `../uart`, `../../feasibility/...`, `../../experiment/m1s`) vẫn
trỏ đúng. Riêng `results/` trong cây bóng là thư mục **thật và rỗng**, nên `make check-*` không bao giờ
ghi lên CSV số đo cũ. Nhánh B trong cây bóng dùng lại đúng `firmware.hex` mà nhánh A vừa dựng trong cùng
cây bóng, nên vẫn giữ tính chất "chênh lệch giữa hai nhánh là thuần vi kiến trúc".

### Tiêu chí ĐẠT của S1 và kết quả
| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | `cdp build/sim/synth/kit` gọi Makefile + script có sẵn | **ĐẠT** — `build` `sim` `synth` đã chạy thật; `kit` viết xong, dừng đúng chỗ khi không thấy `/dev/cu.usbserial*` |
| 2 | Đặc tả YAML cho A-V0, B-V1, B-V3 | **ĐẠT** — `pipeline/specs/s1_{av0,bv1,bv3}.yaml`, cả ba phân giải đúng cấu hình |
| 3 | Chu kỳ **bằng tuyệt đối** 8.987.660 / 1.459.993 / 365.992 | **ĐẠT** — và bằng tuyệt đối **từng lớp, từng ảnh**, không chỉ trung vị |
| 4 | CRC khớp golden | **ĐẠT** — CRC32 cả 5 tensor × 10 ảnh + dự đoán, cả ba cấu hình |
| 5 | SRC_HASH khớp | **ĐẠT** — firmware tự báo `c3966b0011df` = dấu vân tay mã nguồn hiện tại |
| 6 | Ba dòng sổ cái `origin=human_replay` | **ĐẠT** — `replay.A-V0`, `replay.B-V1`, `replay.B-V3`; 30 dòng `measurements` nguồn `verilator` |
| 7 | Đo trên kit | **BỎ** theo quyết định của người dùng (xem dưới) |

### Số đo (Verilator, qua `cdp`, log: `results/pipeline/S1/`)
| cấu hình | chu kỳ/ảnh | ms @27 MHz | chu kỳ/MAC | chu kỳ/lệnh | IPC |
|---|---:|---:|---:|---:|---:|
| A-V0 (PicoRV32) | 8.987.660 | 332,9 | 46,80 | 6,617 | 0,151 |
| B-V1 (mycore) | 1.459.993 | 54,1 | 7,60 | 1,601 | 0,625 |
| B-V3 (mycore+DOT4+REQ) | 365.992 | 13,6 | 1,91 | 1,317 | 0,759 |

Mỗi cấu hình chạy **hai lượt độc lập** → 60 dòng `measurements`, hai lượt cho số **giống nhau từng ảnh**.

### Tổng hợp lại netlist: hai trong ba cấu hình ra ĐÚNG TỪNG CON SỐ
| cấu hình | LUT4 lần này | LUT4 đã ghi | Fmax lần này | Fmax đã ghi |
|---|---:|---:|---:|---:|
| A-V0 | 7.941 | 7.941 | 71,76 MHz | 71,76 MHz |
| B-V1 | 3.255 | 3.235 (**+20**) | 56,47 MHz | 53,05 MHz |
| B-V3 | 5.073 | 5.073 | 55,82 MHz | 55,82 MHz |

Việc A-V0 và B-V3 trùng khít cả LUT4, ALU, DFF, BSRAM, MULT18X18 **và** Fmax chứng minh luồng
yosys + nextpnr ở đây **tất định**. Nhờ vậy chênh +20 LUT4 của B-V1 **không phải nhiễu công cụ**: netlist
`bv1` cũ được tổng hợp từ bản `mycore.v` **chưa có** khối REQ (lệnh yosys trong `bv1/yosys.log` thậm chí
chưa có tham số `WITH_REQ`, và log đó không có một lần nhắc `req` nào), còn `mycore.v` hôm nay có khối REQ
và `WITH_REQ=0` không gấp hằng được hết. Đây là một ví dụ cụ thể cho cạm bẫy số 5 của
`KET_QUA_TONG_HOP.md`: **hiệu hai lần tổng hợp chỉ đo được chi phí phần cứng khi RTL giống hệt nhau.**
Số chu kỳ thì không đổi — vẫn bằng tuyệt đối.

### Quyết định của người dùng: BỎ bước đo kit của S1
Người dùng chốt (2026-10-18): ba cấu hình này đã có số đo kit đầy đủ, nạp lại chỉ để thấy lại số cũ nên
không có giá trị. Phép kiểm đường đo `cdp kit` gộp vào lần đo thật đầu tiên ở S6. `cdp kit` đã viết xong
và đã kiểm nhánh "không có kit" (dừng ngay, không nạp gì). Bitstream cả ba cấu hình đã dựng sẵn.
Hệ quả phải ghi rõ: tiêu chí *chu kỳ kit = Verilator bằng tuyệt đối* KHÔNG được kiểm lại trong phiên này.

### Vấn đề, đã thử
1. `cdp sim` hỏng ngay lần đầu vì `Path.relative_to` trên đường dẫn tương đối — sửa bằng `resolve()` trong
   `spec.load` và một hàm `util.rel()` hiển thị an toàn.
2. `cdp kit` ban đầu định đọc dòng `M1S,*` thô từ log của `make check-*`, nhưng `m1s_check.py` **không**
   in lại các dòng đó; nguồn đủ số duy nhất là CSV nó ghi. Đã đổi sang đọc CSV
   (`wrap.measurement_rows_from_csv`).

### Việc tiếp theo
S2 (ISS + mô hình chu kỳ) rồi S3 (profile 3 tầng + phân tích), theo yêu cầu của người dùng: tập trung vào
phân tích firmware và **dựng thành một lý thuyết** (mô hình chi phí tường minh) để dẫn ra hướng tối ưu.

## 2026-10-18 — PIPELINE CDP bước S0 ĐẠT: khung `cdp`, sổ cái, khoá kit, kiểm đặc tả

Bắt đầu giai đoạn dựng pipeline đồng thiết kế có AI hỗ trợ (`docs/PIPELINE_PLAN.md`, S0→S8).
S0 là hạ tầng: không có số đo hiệu năng mới nào, chỉ có hạ tầng để mọi số sau này truy được nguồn.

### Đã dựng
- Gói `pipeline/cdp/` + lối vào `./cdp` (tương đương `PYTHONPATH=pipeline python -m cdp`).
  Đã hiện thực: `spec`, `db`, `targets`, `lock`, `selftest`. Mười một lệnh còn lại in "chưa hiện thực"
  kèm bước dự kiến và trả mã thoát 2 (`build`/`sim`/`kit`/`synth` → S1, `iss` → S2,
  `profile`/`analyze` → S3, `propose` → S5, `estimate`/`verify` → S6, `report` → S8).
- Sổ cái `pipeline/db/ledger.sqlite` theo SPEC mục 3, **ba** bảng: `runs`, `candidates`, và
  `measurements` (thêm ngoài SPEC — S1/S2 cần so từng ảnh từng lớp, không chỉ trung vị).
  `./cdp db export` ra `ledger.csv`, `candidates.csv`, `measurements.csv`.
- Khoá kit `pipeline/runs/kit.lock` (`fcntl.flock`); file khoá chứa thông tin ai đang giữ.
- `pipeline/schemas/spec.schema.json` (tự viết từ `pipeline/specs/example_bv3.yaml`), kiểm ba lớp:
  cú pháp YAML → lược đồ → **phân giải về đúng một trong 14 cấu hình** và đối chiếu trường `expect`.
- `pipeline/cdp/targets.py`: bản ĐỌC MÁY của bảng 14 cấu hình (đích make, thư mục build, cờ `-D`,
  tham số RTL, nhãn CSV, chu kỳ trung vị). Nhờ vậy S1 chỉ cần gọi đúng đích make, không phải đoán.
- Mỗi lệnh ghi `pipeline/runs/<id>/meta.json`: git commit + sạch/bẩn, `SRC_HASH`, phiên bản
  yosys/nextpnr/verilator/openFPGALoader/riscv-gcc/make/gowin_pack (lấy bằng cách source chính
  `env/setup_env.sh`, không nhân bản logic PATH), tham số, máy, kết quả.

### Tiêu chí ĐẠT (`./cdp selftest` — log: `results/pipeline/S0/`)
| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | `cdp spec pipeline/specs/example_bv3.yaml` hợp lệ | **ĐẠT** — phân giải về **B-V3** |
| 2 | Hai tiến trình xin khoá kit, tiến trình thứ hai chờ | **ĐẠT** — A giữ 2 s, B xin sau 0,5 s, B chờ **1,53 s** |
| 3 | Sổ cái ghi / đọc / xuất CSV | **ĐẠT** |
| 4 | (tự thêm) Bảng 14 cấu hình của `cdp` = số đo thật | **ĐẠT** — cả 14 trung vị tính lại từ CSV kit **và** từ `sim.log` đều bằng số trong `KET_QUA_TONG_HOP.md`; kit = Verilator từng ảnh |

### Hai điều phát hiện khi đối chiếu số cũ (quan trọng cho S1)
1. **Trong dự án có hai định nghĩa "trung vị".** `scripts/m1s_check.py` lấy phần tử thứ 6 của 10
   (`sorted[n//2]`), còn `scripts/branch_b_table.py` dùng `statistics.median` (trung bình hai phần tử
   giữa). Chênh đúng **23 chu kỳ** ở mọi biến thể. Mọi số trong báo cáo (8.987.660 · 1.459.993 ·
   365.992) là số của `branch_b_table.py`; `m1s_check.py` in 8.987.683 · 1.460.016 · 366.015.
   `cdp` chốt dùng `statistics.median` và đã kiểm khớp **cả 14 dòng**.
2. **12/14 cấu hình đã đo được dựng từ `main.c` cũ** (`SRC_HASH=647f1d071aca`); bản hiện tại là
   `c3966b0011df` (commit `542764e` thêm mã REQ trong `#ifdef`). Firmware nhúng cả `GIT_HASH` và
   `SRC_HASH` nên **không thể** dựng lại ra file giống từng byte — nếu không kiểm trước, tiêu chí
   "bằng tuyệt đối" của S1 sẽ hỏng vì một lý do chẳng liên quan gì tới `cdp`.
   Đã thăm dò: dựng lại A-V1 từ `main.c` hiện tại rồi chạy trên `rtl/mycore/Vsoc_b1` → **đúng từng
   chu kỳ, từng lớp, từng ảnh** như `rtl/mycore/bv1/sim.log` đã ghi.
   Log: `results/pipeline/S0/recon_rebuild_av1_sim.log` · so sánh: `recon_rebuild_av1.json`.

### Quyết định ghi lại để S1 làm theo
- `cdp build` của S1 dựng **ngoài cây**: `experiment/m1s/v*/` và `rtl/mycore/bv*/` **đã nằm trong git**
  (130 + 839 file), nên dựng tại chỗ là sửa thư mục kết quả cũ — trái quy tắc. Cách làm: thư mục bóng
  có symlink tới mã nguồn để `../../fw`, `../../scripts`, `../../hw` của hai Makefile vẫn đúng, còn
  `results/` trong thư mục bóng là thư mục **thật và rỗng** để không bao giờ ghi lên CSV cũ.
- `pipeline/runs/` không vào git (đã thêm `.gitignore`); bằng chứng từng bước sao sang
  `results/pipeline/S<n>/`.

### Vấn đề, đã thử
Không có lỗi phải xử lý. Đã thêm `pyyaml 6.0.3` + `jsonschema 4.26.0` vào `.venv`.

### Việc tiếp theo / cần người dùng
- S1: bọc build/sim/kit/synth và tái tạo A-V0, B-V1, B-V3. Phần build + Verilator làm được ngay.
- **Cần kit cho phần đo**: hiện **không** thấy `/dev/cu.usbserial*` (kit chưa cắm). Tới bước đo sẽ dừng
  và xin người dùng cắm kit; chỉ nạp SRAM, có đối chứng như `scripts/branch_b_measure.sh`.

## 2026-10-17 — HOÀN TẤT: A-V3 và B-V3 đo trên kit · 14 cấu hình · 332,9 ms → 13,6 ms (24,6×)

Cổng B5 ĐẠT và biến thể A-V3 xong. Toàn bộ kế hoạch gốc (nhánh A V0–V3, nhánh B V0–V3) đã **đo trên
phần cứng thật**.

| | chu kỳ | ms | chu kỳ/MAC | so A-V0 |
|---|---:|---:|---:|---:|
| A-V3 (PicoRV32+DOT4+REQ) | 1.842.219 | 68,2 | 9,59 | 4,88× |
| **B-V3 (mycore+DOT4+REQ)** | **365.992** | **13,6** | **1,91** | **24,56×** |

Cả hai 2/2 lần đọc, CRC 5 lớp × 10 ảnh khớp golden, kit = Verilator bằng tuyệt đối. Phép đo A-V3 trên
kit cũng **xác nhận netlist A-V3 đúng chức năng** dù cách phủ của nó lạ (mục 6b của KET_QUA_NHANH_B).

### Phân rã 24,6× — và câu trả lời cho câu hỏi "nên đầu tư vào đâu"
| Hướng | Hệ số | Giá phần cứng |
|---|---|---|
| Tối ưu phần mềm | 1,45× | 0 |
| **Vi kiến trúc** | **4,26×** | **ít LUT4 hơn ~2,4 lần** |
| DOT4 | 2,31× | 4 DSP |
| Bố cục 4 pha | 1,29× | 0 |
| REQ | 1,33× | 4 DSP |

**Vi kiến trúc là hướng lớn nhất và là hướng duy nhất vừa nhanh hơn vừa rẻ hơn.**

### RQ3 có thêm bằng chứng mạnh nhất
REQ chuyển giao **gần như chính xác**: 1,330× trên PicoRV32 so với 1,333× trên lõi tự viết — lệch
0,2 %. Hợp lý vì REQ là khối tính toán thuần, ít phụ thuộc vi kiến trúc, khác với DOT4 (2,131 → 2,313)
và bố cục (1,190 → 1,294) vốn phụ thuộc chi phí cố định xung quanh.

Đã viết `docs/KET_QUA_TONG_HOP.md` (136 dòng): bảng 14 cấu hình, phân rã, RQ1/RQ2/RQ3, 7 cạm bẫy,
3 bài học phương pháp, và bảng "những gì KHÔNG kết luận được".

## 2026-10-17 — NHÁNH B cổng B6 ĐẠT: 100 và 10.000 ảnh đúng từng bit trên lõi tự viết

Tiêu chí ĐẠT của cả nhánh B trong kế hoạch gốc (*"lõi qua riscv-tests; 100 ảnh đúng từng bit"*) nay
thoả cả hai phần. Dùng chế độ `STREAM_10K` nạp ảnh qua UART trên lõi tự viết (100 ảnh nhúng sẵn không
vừa RAM 64 KB). Đã mô phỏng 3 ảnh trước khi tổng hợp: CRC logit `9377670B`/`3C922E73`/`46B2E0F3` khớp
golden từng bit.

| | 100 ảnh | **10.000 ảnh** |
|---|---|---|
| khung nhận đúng / gửi lại | 100/100 · 0 | 10.000/10.000 · **0** |
| CRC32 logit khớp golden | 100/100 | **10.000/10.000** |
| độ chính xác đo trên kit | 100 % | **98,25 %** |
| trung vị chu kỳ/ảnh | 487.846 | **487.857** |

**98,25 % bằng tuyệt đối nhánh A và bằng golden** → cùng mô hình, cùng kết quả từng bit, trên hai vi
kiến trúc khác hẳn nhau; chỉ khác thời gian 90,8 ms so với **18,1 ms**. 175 ảnh sai giống y nhánh A tới
từng cặp nhầm.

Kiểm chéo: 487.857 (10.000 ảnh, firmware STREAM_10K) so với 487.888 (10 ảnh nhúng, firmware khác) —
lệch 31 chu kỳ = 0,006 %.

### Kết quả phụ gọn: phần phụ thuộc dữ liệu nằm ở SỐ LỆNH
`instret` dao động **đúng 765**, độ lệch chuẩn **133,1** — **trùng khít** dao động chu kỳ, và **giống
hệt nhau trên cả hai lõi**. Nghĩa là mỗi lệnh thêm (nhánh so sánh trong maxpool) tốn **đúng 1 chu kỳ
trên cả hai**. Với lõi tự viết đó là giá bình thường của lệnh ALU; với PicoRV32 (6,6 chu kỳ/lệnh trung
bình) thì những lệnh này **lọt vào khe đang chờ bộ nhớ**. Suy luận phù hợp số liệu, chưa chứng minh cơ chế.

### UART đã thành nút cổ chai
18,1 ms để tính một ảnh, ~68 ms để nạp 784 byte qua UART 115200. 10.000 ảnh mất 16,7 phút, **chỉ ~3
phút là tính**. Lõi đã nhanh hơn đường nạp dữ liệu — giới hạn của **bàn đo**, không phải của thiết kế.

Đã viết tổng kết RQ3 chính thức vào `docs/KET_QUA_NHANH_B.md` mục 9: cả ba tối ưu đều giữ nguyên bậc
độ lớn khi đổi vi kiến trúc (DOT4 2,13→2,31×, bố cục 1,19→1,29×, tối ưu phần mềm 1,45→1,36×).

## 2026-10-17 — Nhánh B: số liệu TRỌN VẸN, 7 biến thể × 10 ảnh trên kit

Sau khi viết lại `scripts/branch_b_measure.sh` cho bền với sự cố, một lượt duy nhất đo xong **5 biến
thể còn lại, không một lần UART chết** (trước đó chết sau 2 phép đo). CSV: **70 dòng**, 7 biến thể.

### Hai thay đổi làm script bền — và có lẽ đã chữa luôn nguyên nhân
1. **Không bao giờ ghi đè CSV.** Trước mỗi phép đo chỉ xoá các dòng *của chính biến thể đó* rồi ghi
   nối; biến thể đã đủ 10 dòng thì bỏ qua. Nên chạy một phần vẫn tích luỹ, không mất gì. (Bản trước
   ghi đè ở biến thể đầu tiên và đã làm mất số đo **hai lần**.)
2. **Chỉ đối chứng ở đầu lượt và sau một phép đo THẤT BẠI**, không đối chứng sau mỗi lần thành công —
   một phép đo thành công đã tự chứng minh đường đo sống (CRC khớp golden + kit = Verilator). Việc này
   **giảm một nửa số lần nạp JTAG**, và lượt đo sau đó chạy liền 5 biến thể không hỏng, so với 2 trước
   đây. Giả thuyết: chính hoạt động JTAG (libusb chiếm thiết bị) làm interface UART chết. Chưa chứng
   minh được nhân quả, nhưng tương quan đủ mạnh để giữ cách làm này.

### Giá của thiết kế bảo thủ — đo được
| | `FAST_ADDR=1` (địa chỉ tổ hợp) | `FAST_ADDR=0` (ghi thanh ghi) | giá |
|---|---:|---:|---:|
| C thẳng | 1.978.720 · **73,3 ms** | 3.750.662 · 138,9 ms | **1,90×** |
| +tối ưu phần mềm | 1.460.016 · **54,1 ms** | 2.713.280 · 100,5 ms | **1,86×** |

**Thủ thuật "địa chỉ bộ nhớ tổ hợp" đáng giá 1,9× mà không tốn một cổng logic nào** — gần bằng cả lệnh
DOT4 (2,31×). Nhưng tính đúng đắn về thời gian của nó **không kiểm được bằng công cụ mã nguồn mở này**
(nextpnr không ràng buộc đường tới BSRAM); nó chỉ được chứng minh bằng chạy đúng trên kit với CRC khớp
golden. Trong thiết kế đưa vào sản xuất, đó là lý do chính đáng để chọn bản bảo thủ.

### Toàn cảnh: 12 cấu hình đã đo trên kit
Nhanh nhất **B-V1+DOT4+C1: 487.888 chu kỳ = 18,1 ms = 2,54 chu kỳ/MAC = 55,3 ảnh/giây**, **18,4×** so
với A-V0. Chậm nhất A-V0: 332,9 ms. Phân rã: 1,45× phần mềm (miễn phí) × 4,26× vi kiến trúc (tiết kiệm
58,8 % LUT4) × 2,31× DOT4 (+1.122 LUT4) × 1,29× bố cục (miễn phí).

## 2026-10-17 — NHÁNH B cổng B4 ĐẠT: DOT4 trong tầng thực thi — 18,1 ms, và RQ3 có câu trả lời

Gắn DOT4 **thẳng vào tầng thực thi** của lõi tự viết (không qua PCPI): toán hạng từ tệp thanh ghi,
4 phép nhân int8 + cây cộng, ghi về trong **cùng chu kỳ** như lệnh ALU → **1 chu kỳ**, so với **2 chu
kỳ** qua PCPI trên PicoRV32. Mã hoá giữ y nhánh A nên **dùng lại đúng firmware.hex của nhánh A**.

Phép nhân int8 cố ý dựng bằng **logic LUT** chứ không gọi `MULT18X18`: F4 đã chứng minh đường LUT đúng
trên kit còn DSP suy luận thì sai, và gọi DSP ở đây sẽ thêm độ trễ vào đường tới hạn của tầng thực thi
— đường mà nextpnr **không ràng buộc**. Trả giá +1.122 LUT4 để giữ đường ngắn.

| Biến thể | A (kit) | **B (kit)** | B nhanh hơn | chu kỳ/MAC | so A-V0 |
|---|---:|---:|---:|---:|---:|
| C thẳng + DOT4 | 213,3 ms | **43,3 ms** | 4,93× | 6,09 | 7,69× |
| +tối ưu PM + DOT4 | 108,0 ms | **23,4 ms** | 4,62× | 3,29 | 14,24× |
| **+bố cục 4 pha** | 90,8 ms | **18,1 ms** | **5,02×** | **2,54** | **18,4×** |

`instret` khớp tuyệt đối nhánh A ở cả ba; CRC 5 lớp × 10 ảnh khớp golden; kit = Verilator bằng tuyệt
đối; 2/2 lần đọc; đối chứng đường đo ĐẠT trước và sau từng phép đo.

### RQ3 — trả lời được
| DOT4 cho | Hệ số |
|---|---|
| PicoRV32 (PCPI, 2 chu kỳ) | **2,13×** |
| lõi tự viết (tầng thực thi, 1 chu kỳ) | **2,31×** |

**Có, và tốt hơn một chút.** Lợi ích của lệnh tùy biến chuyển giao được sang vi kiến trúc khác hẳn.
Bố cục 4 pha cũng vậy: 1,29× trên lõi tự viết so với 1,19× trên PicoRV32.

### Phân rã 18,4×, kèm giá phần cứng
1,45× phần mềm (**miễn phí**) × 4,26× vi kiến trúc (**tiết kiệm 58,8 % LUT4**) × 2,31× DOT4
(+1.122 LUT4) × 1,29× bố cục (**miễn phí**). → **Vi kiến trúc đóng góp gần gấp đôi lệnh tùy biến,
và còn rẻ hơn.** Đây là kết luận định lượng chính của nhánh B.

### Hai lỗi của chính tôi trong buổi này
1. `branch_b_measure.sh`: biến thể đo **đầu tiên** ghi CSV không `--append` nên **xoá** các dòng đã đo
   trước đó → mất dữ liệu thô của `bv0`/`bv1` (số liệu vẫn còn trong `check.log`, nhưng không còn dòng
   từng ảnh). Đã sửa: script luôn đo **đủ cả bảy** biến thể trong một lượt.
2. `bv1r` bị ghi vào CSV dù chỉ đạt **1/2** lần đọc (UART chết đúng lúc đọc lần hai). Đã xoá 10 dòng
   đó — tiêu chí dự án là 2/2, không thoả thì không ghi nhận.

Script đã làm đúng việc của nó: in `[đối chứng KHÔNG ĐẠT sau bv1r — đường UART chết, số đo sau mốc
này VÔ GIÁ TRỊ]` rồi tự dừng. Đúng như thiết kế sau bài học B3.

## 2026-10-17 — NHÁNH B cổng B3 ĐẠT: lõi tự viết chạy trên kit, 73,3 ms

Sau khi người dùng cắm lại cáp USB, đo lại trong **một lượt liên tục** với đối chứng trước/sau mỗi
phép đo (`scripts/branch_b_measure.sh`, thiết kế tối giản `top_min` phát "MIN"). Cả hai phép đo đều
có đối chứng ĐẠT (8 lần "MIN") trước và sau.

| | A-V0 | **B-V0** | A-V1 | **B-V1** |
|---|---:|---:|---:|---:|
| tổng chu kỳ | 8.987.660 | **1.978.697** | 6.217.634 | **1.459.993** |
| `instret` | 1.358.200 | **1.358.200 KHỚP** | 911.920 | **911.920 KHỚP** |
| ms @27 MHz | 332,9 | **73,3** | 230,3 | **54,1** |
| chu kỳ/MAC | 46,80 | **10,30** | 32,37 | **7,60** |
| IPC | 0,151 | **0,686** | 0,147 | **0,625** |
| nhanh hơn | — | **4,54×** | — | **4,26×** |

CRC 5 lớp × 10 ảnh khớp golden, dự đoán khớp golden, **kit = Verilator bằng tuyệt đối**, 2/2 lần đọc.

**Kết quả đáng chú ý nhất**: B-V0 (73,3 ms) **nhanh hơn A-V1+DOT4+C1 (90,8 ms) 1,24×** — kernel C
thẳng, không một lệnh tùy biến nào, trên lõi tự viết, vượt bản tối ưu hết mức *có* lệnh tùy biến trên
PicoRV32. Với khối lượng này **vi kiến trúc đáng giá hơn tập lệnh**: 4,54× từ lõi so với 2,13× từ DOT4.

**Tài nguyên**: lõi tự viết nhanh hơn 4,54× mà **nhỏ hơn 58,8 % LUT4** (3.272 so với 7.941), DFF 656
so với 1.069. Lý do: chỉ làm đúng những gì cần (RV32IM + 4 CSR đọc), không ngắt, không PCPI, và bus
1 chu kỳ đơn giản hơn máy trạng thái 2 chu kỳ.

**Lần im lặng trước đó đúng là do UART của kit chết, không phải thiết kế** — bản `FAST_ADDR=1` (địa chỉ
tổ hợp) chạy hoàn toàn đúng trên kit. Ghi nhận thêm về hiện tượng: UART chết sau mười mấy phút không
dùng cổng (trong lúc tổng hợp bitstream), đảo DTR/RTS và đổi baud không cứu được, chỉ rút/cắm lại cáp;
phần JTAG vẫn tốt. Vì vậy mọi phép đo phải gom vào một lượt liên tục ngay sau khi cắm cáp.

Tài liệu kết quả: `docs/KET_QUA_NHANH_B.md`.

## 2026-10-17 — NHÁNH B cổng B3: TẠM HOÃN, KHÔNG PHẢI KHÔNG ĐẠT — đường UART của kit đã chết

> **SỬA KẾT LUẬN.** Mục này ban đầu ghi "B3 KHÔNG ĐẠT". Sai. Sau khi khoanh vùng theo hướng người
> dùng chọn, phép **đối chứng** cho kết quả quyết định: nạp lại bitstream **nhánh A đã biết chạy**
> (`v1dc/top.fs`) thì kit **cũng không phát byte nào**, trên **cả hai** cổng serial. Vậy đường UART
> của kit đã chết, và **mọi phép đo nhánh B từ đầu buổi B3 đều vô giá trị** — không kết luận được gì
> về lõi. Cần người dùng rút/cắm lại cáp USB rồi đo lại.
>
> **Bài học phương pháp, đáng ghi vào luận văn**: khi một phép đo trả về "không có gì", việc ĐẦU TIÊN
> phải làm là chạy **đối chứng bằng một cấu hình đã biết chạy**, trước khi sửa thiết kế. Tôi đã bỏ
> qua bước đó và sửa thiết kế bốn lần trên một đường đo đã hỏng. Quy tắc "tối đa 3 hướng sửa rồi
> dừng" trong CLAUDE.md có tác dụng, nhưng nó không cứu được việc chọn SAI đối tượng để sửa.
>
> Phần ghi chép bên dưới giữ nguyên vì các bằng chứng kỹ thuật trong đó vẫn đúng và vẫn hữu ích
> (hai lỗi thật về xung nhịp, phát hiện nextpnr không ràng buộc đường tới BSRAM).

## (ghi chép gốc) NHÁNH B cổng B3 — triệu chứng và những gì đã kiểm

B2 đã ĐẠT (xem mục dưới). B3 = đưa lõi lên kit.

### Triệu chứng
Bitstream nạp thành công (`openFPGALoader`: `Done Final`, thanh ghi trạng thái `0x00006020`),
nhưng kit **không phát một byte nào** qua UART trong 5 giây (`.venv/bin/python` đọc trực tiếp:
`nhận 0 byte`). Không phải lỗi phân tích dòng — thực sự 0 byte.

### Điều làm triệu chứng này đặc biệt khó
Tôi đã thêm một **đèn hiệu phần cứng** vào `soc_b.v` (`BEACON=1`): một máy trạng thái nhỏ tự phát
`S<state><trap><8 hex PC>\n` qua UART mỗi ~0,3 s, **hoàn toàn độc lập với lõi** — nó chỉ cần xung
nhịp chạy và khối `always` hoạt động. Đã xác nhận logic này **có trong netlist**
(`grep -c bcn_div bv0/top-synth.json` = 96, `Parameter \BEACON = 1`). **Đèn hiệu cũng im.**
→ Vấn đề KHÔNG nằm ở lõi. Nó nằm ở tầng dưới: xung nhịp không tới, hoặc thiết kế bị đóng băng.

### Những gì đã kiểm và ĐÚNG (bằng chứng, không phải phỏng đoán)
| Kiểm | Kết quả |
|---|---|
| `riscv-tests` trong Verilator, cả `FAST_ADDR`=1 và 0 | 48/48 RV32IM + `fence_i` ĐẠT |
| M1-S trong Verilator, cùng file hex của nhánh A | `M1S,sum,10,10,10,10` đúng từng bit |
| Nội dung BSRAM trong netlist | **giống hệt nhánh A**: 43.925/524.288 bit khác 0 |
| Tài nguyên | BUFG 1, IOB 9, GSR 1, BSRAM 32, RAM16SDP4 32 — cùng cấu trúc nhánh A |
| IBUF xung nhịp | `u_soc.clk_IBUF_O` — **cùng tên** như nhánh A |
| `GSR.GSRI` | nối `$PACKER_VCC` (không kích hoạt) ở **cả hai** nhánh |
| Fmax nextpnr | 86,45 MHz (ràng buộc 27) |
| `openFPGALoader` | `Done Final`, `0x00006020` |

### Hai lỗi THẬT đã tìm ra trên đường đi (đều do tôi gây ra)
1. **Chia xung nhịp trên vải FPGA** → `ERROR: Hold/min time violation for clock 'posedge clk_d'`.
   Xung nhịp dẫn xuất đi đường routing thường là thực hành sai; muốn hạ tần số phải dùng rPLL.
2. **Đặt net trung gian cho xung nhịp làm MẤT ràng buộc chân.** Khi viết `wire clk_sys = clk;`,
   yosys đổi tên net nên IBUF thành `clk_sys_IBUF_O` thay vì mang tên cổng `clk`. Ràng buộc
   `IO_LOC "clk" 4` và `CLOCK_LOC "clk" BUFG` trong `.cst` **không khớp cell nào** → xung nhịp vào
   chân bất kỳ. Đây là **cạm bẫy thật của luồng mã nguồn mở**, đáng ghi vào luận văn: *đừng đặt net
   trung gian trên đường xung nhịp ở tầng top, vì ràng buộc chân khớp theo TÊN*.
   Đã sửa (nối `clk` trực tiếp, IBUF trở lại đúng tên) — **nhưng kit vẫn im**, nên đây không phải
   nguyên nhân gốc (lần dựng ĐẦU TIÊN, trước khi có `clk_sys`, cũng đã im).

### Một phát hiện độc lập, vẫn đúng và vẫn đáng ghi
`grep -c "Sink u_soc.ram\." nextpnr.log` = **0** ở **cả** nhánh A và B: nextpnr-himbaechel **không
báo đường nào kết thúc ở BSRAM**. Nhánh A không bị ảnh hưởng vì `mem_addr` của PicoRV32 là thanh ghi.
Thiết kế 1 chu kỳ/lệnh của tôi đặt cả giải mã + tệp thanh ghi + ALU lên đường vào địa chỉ BSRAM, nên
**con số Fmax mà nextpnr báo không nói gì về đường tới hạn thật của thiết kế đó**. Vì vậy tôi đã làm
sẵn biến thể `FAST_ADDR=0` (ghi thanh ghi địa chỉ, mọi đường là thanh ghi→thanh ghi): mô phỏng
3.750.362 chu kỳ, vẫn nhanh hơn A-V0 **2,40×**.

### Khoanh vùng bằng thiết kế tối giản (hướng người dùng đã chọn)
Dựng `rtl/mycore/top_min.v` — **chỉ** một bộ đếm + `uart_tx` phát "MIN\r\n" mỗi 0,2 s + một LED nhấp
nháy. Không lõi, không RAM 64 KB, không DSP; dùng đúng cùng Makefile, cùng `.cst`, cùng lệnh công cụ.
Fmax 334 MHz. Ràng buộc chân khớp hết (log nextpnr chỉ báo `btn_s1`/`btn_s2 not found`, **giống hệt**
nhánh A). **Bản tối giản cũng im.**

→ Lúc này mới chạy phép đối chứng: nạp lại `experiment/m1s/v1dc/top.fs` (bitstream nhánh A đã đo
thành công vài phút trước) → **cũng 0 byte**, trên cả `...303170` và `...303171`. Kết luận: đường UART
của kit chết, không phải thiết kế.

### Phương án đề xuất (đã không còn cần thiết — xem phần sửa kết luận ở đầu mục)
1. **Chia nhỏ để khoanh vùng**: dựng từ cùng Makefile một top **tối giản** (chỉ đèn hiệu UART, không
   có lõi). Nếu nó cũng im → lỗi ở thiết lập build trong `rtl/mycore`; nếu nó chạy → lỗi ở `soc_b`.
   Rẻ nhất (~6 phút), thu hẹp mạnh nhất.
2. **Đối chiếu bằng Gowin EDA Education** cho đúng một bitstream (CLAUDE.md đã ghi đây là phương án
   dự phòng/đối chiếu). Nếu RTL chạy với công cụ hãng thì luồng mã nguồn mở có lỗi với thiết kế này.
3. **Giữ nhánh B ở mức mô phỏng**, ghi rõ trong báo cáo là *chưa kiểm trên phần cứng*. Số liệu vẫn
   có giá trị: lõi qua `riscv-tests`, M1-S đúng từng bit, `instret` khớp tuyệt đối nhánh A, và với
   nhánh A đã chứng minh **kit = Verilator bằng tuyệt đối** ở F5–F8 và cả 5 biến thể M1-S.
4. **Chỉ báo cáo nhánh A** — phương án dự phòng ghi trong kế hoạch gốc.

Vật phẩm: `results/branch_b/B3/` (log nạp, nextpnr, yosys, so sánh netlist).

## 2026-10-17 — NHÁNH B cổng B1 ĐẠT, và SỬA SỐ LIỆU NHÁNH A (baseline sai)

### B1: lõi tự viết qua riscv-tests ngay lần đầu
`rtl/mycore/mycore.v` (478 dòng) + `rtl/mycore/soc_b.v`. Hai tầng; bộ nhớ một cổng đọc đồng bộ 1 chu kỳ.

| | PicoRV32 | **mycore** |
|---|---|---|
| RV32IM, 48 bài | 48/48 | **48/48** |
| `fence_i` | KHÔNG ĐẠT (không có Zifencei) | **ĐẠT** |
| `ma_data` | KHÔNG ĐẠT | KHÔNG ĐẠT (bắt lỗi lệch địa chỉ theo thiết kế) |

**Hai lỗi thiết kế tôi tự tìm khi rà lại TRƯỚC khi mô phỏng** — cả hai đều âm thầm, bộ kiểm đúng/sai
không bắt được:
1. `mem_addr` phải là **tổ hợp**, không phải thanh ghi. BSRAM đã có thanh ghi địa chỉ ở đầu vào; thêm
   một tầng nữa thì địa chỉ ra chậm một chu kỳ → 2 chu kỳ mỗi lệnh, IPC 0,5, mất hết mục đích. Lõi vẫn
   chạy ĐÚNG, chỉ chậm gấp đôi.
2. Hazard đọc-sau-ghi ở tệp thanh ghi: ghi qua thanh ghi trung gian thì kết quả chỉ thấy sau 2 chu kỳ,
   mà lệnh kế đã đọc ở chu kỳ sau.

Hệ quả thiết kế: **không có hình phạt rẽ nhánh** — địa chỉ lệnh kế tính xong ngay trong chu kỳ thực
thi nên lõi luôn nạp đúng, không đoán.

`rtl/mycore/tests/ipc_probe/` — 4 vòng asm có số lệnh suy ra giải tích:

| vòng | lệnh/vòng | chu kỳ/lệnh PicoRV32 | chu kỳ/lệnh mycore | nhanh hơn |
|---|---|---:|---:|---:|
| alu | 2 | 7,00 | **1,00** | 7,0× |
| mem | 5 | 7,40 | **1,40** | 5,3× |
| mul | 4 | 6,25 | **1,25** | 5,0× |
| jmp | 3 | 6,33 | **1,00** | 6,3× |

`instret` của **cả hai lõi** khớp tuyệt đối số lệnh lý thuyết → cả hai đếm đúng. Trên firmware F6 đã
hiệu chuẩn (`2n+3`), hai lõi cũng cho `instret` giống nhau từng số.

M1-S trên lõi mới, với **chính file hex của nhánh A**: `M1S,sum,10,10,10,10` ngay lần đầu.

### SỬA SỐ LIỆU NHÁNH A — baseline A-V0/A-V2 đo bằng bản nháp chưa commit
Chính phép kiểm tôi tự đặt ra cho nhánh B đã bắt được: *cùng một file hex thì `rdinstret` phải bằng
nhau tuyệt đối*. Lõi mới báo 1.358.178; số A-V0 đã công bố là 1.864.264. Chênh đó không giải thích
được bằng vi kiến trúc → chỉ còn khả năng hai số đo **không cùng firmware**. Xác nhận bằng `GIT_HASH`
nhúng trong firmware: `sim.log` của A-V0 báo `339b4fb`, hex trên đĩa báo `c718706`.

Nguyên nhân: khi thêm A-V1 tôi viết lại `conv2` *bản thẳng* (macro `MAC8` + con trỏ chạy) làm nó nhanh
hơn, nhưng **không đo lại A-V0/A-V2**. Baseline chậm hơn thực tế → mọi tỷ số bị phóng đại.

Đã **đo lại cả 5 biến thể trên kit từ một trạng thái mã nguồn duy nhất**, mỗi biến thể 2/2 lần đọc đạt:

| | A-V0 | A-V1 | A-V2 | A-V1+DOT4 | A-V1+DOT4+C1 |
|---|---:|---:|---:|---:|---:|
| tổng | **8.987.660** | 6.217.634 | **5.758.001** | 2.917.079 | **2.450.494** |
| lệnh | **1.358.200** | 911.920 | **913.105** | 460.793 | 391.278 |
| ms | **332,9** | 230,3 | **213,3** | 108,0 | **90,8** |
| so A-V0 | 1,00× | **1,45×** | **1,56×** | **3,08×** | **3,67×** |

(trước đây công bố: 12.129.818 · 1,95× · 2,11× · 4,16× · 4,95×)

### Số sửa làm ĐỔI MỘT KẾT LUẬN — và kết luận mới mạnh hơn
Trước đây tôi viết "hai tối ưu độc lập, nhân được với nhau" vì DOT4 cho 2,11× trên C thẳng và 2,13×
trên C tối ưu. Với số đúng, hai hệ số đó là **1,56×** và **2,13×** — **không** độc lập:

> **DOT4 cho lợi ích gấp 1,37 lần khi phần mềm đã được tối ưu trước.**

Lý do đọc được từ số liệu: ở C thẳng, `conv2` tốn 35,95 chu kỳ/MAC mà phần lớn là **tính chỉ số**;
DOT4 chỉ cắt phần nhân-cộng nên cắt được một phân số nhỏ. Sau khi tối ưu phần mềm, phần nhân-cộng mới
chiếm tỷ trọng lớn.

**Hệ quả cho phương pháp co-design: thứ tự có ý nghĩa.** Đo một lệnh tùy biến trên mã chưa tối ưu sẽ
**đánh giá THẤP** giá trị của nó. Và đây là câu trả lời mạnh hơn cho phản biện "tăng tốc chỉ nhờ
baseline kém": với baseline *đã tối ưu*, DOT4 vẫn cho 2,13× — **cao hơn** khi đo trên baseline kém.

Lưu ý phân rã theo chuỗi (1,4455 × 2,1315 = 3,0810 = đúng số đo tới 4 chữ số): đó **đúng do định
nghĩa**, cùng một con đường viết thành hai chặng. Nó xác nhận phép đo nhất quán, không phải phát hiện.
Trước đây tôi trình bày nó như phát hiện — đó là cách diễn giải sai, đã sửa.

### Cách chặn để không lặp lại
`GIT_HASH` không đủ. Firmware giờ in thêm **dấu vân tay NỘI DUNG**:
`SRC_HASH := $(shell cat main.c $(FWDIR)/weights.h | shasum -a 256 | cut -c1-12)`.
Kit in `M1S,src,<SRC_HASH>` và `scripts/m1s_check.py` **từ chối** ghi nhận nếu khác mã nguồn trên đĩa.
Cả 5 số đo mới mang `SRC_HASH = 647f1d071aca`.

**Điểm cốt lõi**: kiểm tính đúng đắn (CRC khớp golden) **không** bắt được lỗi này — cả hai bản firmware
đều đúng từng bit, chỉ chạy nhanh khác nhau. Một bộ số đo chỉ so sánh được khi mọi biến thể đến từ cùng
một trạng thái mã nguồn, và điều kiện đó phải do **máy** kiểm.

Không ảnh hưởng: độ chính xác 98,25 % trên 10.000 ảnh, 10.000/10.000 CRC, tài nguyên/Fmax, chi phí
requantize 49,6 chu kỳ, kết luận kit = Verilator.

## 2026-10-17 — NHÁNH B, cổng B0: hạ tầng kiểm thử riscv-tests — ĐẠT

Bắt đầu nhánh B. Kế hoạch nhánh B viết ra ở `docs/BRANCH_B_PLAN.md` (7 cổng B0–B6, tiêu chí từng
cổng, rủi ro đã nhận diện). Lý do nhánh B đáng làm, lấy từ số đo chứ không từ cảm nhận: **IPC = 0,160**
ở biến thể nhanh nhất của nhánh A, tức 6,26 chu kỳ mỗi lệnh — nguyên nhân thuộc **vi kiến trúc**
(PicoRV32 không pipeline, bus `soc.v` 2 chu kỳ mỗi truy cập), thêm lệnh tùy biến không sửa được.

### Quyết định phương pháp: kiểm hạ tầng trên lõi ĐÃ BIẾT ĐÚNG trước
Cổng B0 không viết một dòng RTL nào của lõi mới. Nó chỉ dựng bộ kiểm và **chạy trên PicoRV32**.
Lý do: nếu dùng một harness chưa được kiểm để xét lõi mới thì mỗi lần "KHÔNG ĐẠT" đều có hai cách
giải thích, và sẽ mất rất nhiều thời gian để phân biệt lỗi lõi với lỗi harness.

### Tập lệnh bắt buộc — đếm từ firmware thật
`objdump` cả 6 bản firmware nhánh A: RV32I đầy đủ + `mul` (123 lần), `mulh` (12), `mulhu` (6),
CSR `rdcycle`/`rdcycleh`/`rdinstret`, `fence` (15, coi như nop). **Không có `div`/`rem`** ở bất kỳ bản
nào. Vẫn sẽ hiện thực `div divu rem remu mulhsu` để qua *trọn bộ* `rv32um`.

### Kết quả B0
`scripts/riscv_tests.sh` + `rtl/mycore/tests/{start_test.S, link_test.ld, riscv_test.h}`:
mỗi bài kiểm là **một chương trình riêng** (`_start` → `mytest` → `mytest_ret` in "DONE"), nạp vào
`firmware.hex`, chạy trên `soc.v` của F5. PASS/FAIL báo bằng ghi ký tự vào 0x10000000 — trùng đúng
địa chỉ UART của SoC nên không phải sửa gì.

| | |
|---|---|
| **RV32IM (48 bài: 40 `rv32ui` + 8 `rv32um`)** | **ĐẠT 48/48 trên PicoRV32** → harness đúng |
| ngoài RV32IM: `ma_data` | KHÔNG ĐẠT — cần hỗ trợ truy cập lệch địa chỉ; PicoRV32 bật `CATCH_MISALIGN` |
| ngoài RV32IM: `fence_i` | KHÔNG ĐẠT — cần Zifencei |

`fence_i` không đạt **có bằng chứng từ mã nguồn**, không phải đoán: `picorv32.v:1088` giải mã
`instr_fence <= (mem_rdata_q[6:0] == 7'b0001111 && !mem_rdata_q[14:12])` — chỉ nhận `funct3 == 0`,
nên `fence.i` (`funct3 == 1`) là lệnh không hợp lệ → trap ở chu kỳ 1758.
Lõi tự viết sẽ hiện thực `fence.i` (xả lệnh đã nạp trước) nên **có thể qua được bài này**, tức hơn
PicoRV32 một bài — sẽ xác nhận bằng số đo ở B1, không hứa trước.

### Cạm bẫy
- `$CROSS gcc` trong shell script → `riscv-none-elf- gcc` (có khoảng trắng) → "command not found" cho
  cả 49 bài. Phải viết `"${CROSS}gcc"`. Triệu chứng giống hệt "toolchain hỏng", rất dễ mất thời gian.
- Lần đầu tất cả bài đều in `mytest..OK DONE` nhưng harness báo KHÔNG ĐẠT, vì tôi quên truyền
  `TEST_FUNC_TXT` nên bài nào cũng tự gọi là "mytest". Dấu hiệu nhận ra: output đúng mà kết luận sai.
- `sim_main.cpp` chỉ in khi gặp `\n`, mà `RVTEST_CODE_BEGIN` in tên bài **không có** `\n`. Nên một
  bài trap giữa đường cho log **rỗng hoàn toàn** — không phải mất output, chỉ là chưa xả bộ đệm.
  Harness của nhánh B sẽ xả phần dở khi kết thúc.

Vật phẩm: `results/branch_b/B0/` (kết quả 50 bài trên PicoRV32 + log trap của `fence_i`/`ma_data`).
Phiên bản ghim: `env/VERSIONS.md` (riscv-tests `d7e86f70`).

## 2026-10-17 — Chạy ĐỦ 10.000 ảnh test trên kit: 98,25 % là số ĐO, không phải số suy ra

Lỗ hổng duy nhất còn lại của chương nhánh A: năm biến thể chỉ chạy **10 ảnh nhúng trong firmware**,
nên 98,25 % là của golden Python, không phải của kit. RAM 64 KB không chứa nổi 10.000 ảnh (7,84 MB)
→ phải nạp ảnh qua UART.

### Giao thức, và hai tính chất làm nó tự lành
**1 byte `0xA5` + 784 byte ảnh**, host gửi theo khối 64 byte (bài học F2).
- Pixel lượng tử hoá ∈ [0,127] nên **không bao giờ** trùng `0xA5` → mất byte thì khung sau tự đồng bộ
  lại. Đây là lý do chọn đúng giá trị 0xA5 chứ không phải một byte bất kỳ.
- **Kit mời thì host mới gửi** (chỉ gửi sau một dòng hoàn chỉnh).
- Kit báo **CRC32 của chính 784 byte nó nhận được** → tách lỗi đường truyền khỏi lỗi tính toán.

### Mô phỏng trước khi tổng hợp — và nó bắt được hai lỗi
Harness Verilator cũ (F5/F8) chỉ đọc `uart_tx`, giữ `uart_rx` mức cao, nên **không kiểm được chiều
thu**. Viết `experiment/m1s/sim_main_10k.cpp` tự tạo dạng sóng 8N1 ở đúng `DIV=234` bơm vào `uart_rx`.

1. **GCC nhân bản `conv1` thành `conv1.constprop.0`** vì `conv1(img_buf)` luôn cùng một địa chỉ →
   sinh mã **khác** `v1dc`, làm bản 10k không còn so sánh được với 5 biến thể cũ.
   `scripts/cmp_layers.py` (mới) phát hiện. Sửa: `static i8 *volatile img_p = img_buf;`.
   Giá phải trả, ghi đúng: `conv1` 1.133.668 → **1.133.673** (+5 chu kỳ cho một lần đọc volatile).
2. **Thanh ghi thu chỉ giữ MỘT byte, không FIFO** (`rx_hold`/`rx_full` trong `soc.v`). Harness gửi
   ngay sau reset, trong lúc kit còn đang phát dòng `hello`, nên mọi byte bị byte sau ghi đè. Kit quét
   tìm `0xA5` mãi không thấy → mô phỏng chạy 83 triệu chu kỳ không ra phản hồi. Nếu đem thẳng lên kit
   thì chỉ thấy "treo" mà không biết vì sao. Sửa bằng quy tắc "kit mời thì host mới gửi".

Mô phỏng 3 ảnh: dự đoán 7/2/1, CRC logit `9377670B`/`3C922E73`/`46B2E0F3`, CRC ảnh
`8DF03AB1`/`317A5E14`/`C73EC552` — **khớp golden từng bit**. `make cmp-v10k`: `CMP_PASS`, cả 6 hàm
(`conv1`, `conv1_prep`, `pool1`, `conv2`, `pool2`, `dense`) trùng khít mnemonic/thanh ghi/offset.
Tài nguyên `v10k` **giống hệt** `v1dc`: LUT4 8.065, 4 MULT18X18, Fmax 71,89 MHz.

### Kết quả trên kit (30,0 phút, 27 MHz)
| | |
|---|---|
| khung nhận đúng | **10.000/10.000**, thất bại 0, **gửi lại 0 lần**, CRC ảnh lệch 0 |
| CRC32 logit = golden | **10.000/10.000 (100 %)** |
| dự đoán = golden | **10.000/10.000** |
| **độ chính xác đo trên kit** | **9.825/10.000 = 98,25 %** |

Bằng golden **tuyệt đối**. 0 lần gửi lại trên 7,85 MB cũng xác nhận lại kết luận F2.

### Hai kết quả phụ đáng giá, chỉ thấy được khi chạy 10.000 ảnh
**a) Suy luận tất định về thời gian.** Biên độ tổng chỉ **765 chu kỳ = 0,031 %**; mỗi ảnh
**90,74–90,77 ms**. `conv1` và `dense` biên độ **0** trên cả 10.000 ảnh; `conv2` lệch tối đa 2 chu kỳ
(ReLU rẽ nhánh); `pool1`/`pool2` biên độ 560/234 (maxpool rẽ nhánh theo so sánh).
→ **Phải sửa một điều đã ghi trước đây**: `pool1 = 225.600` và `pool2 = 65.921` là hằng số *với 10 ảnh
cố định*, chứ không phải vì hai lớp đó tất định. Chỉ 10.000 ảnh mới phân biệt được hai chuyện này.

**b) IPC = 0,160** (391.268 lệnh / 2.450.490 chu kỳ). Đây là lý do gốc còn 12,76 chu kỳ/MAC:
PicoRV32 không pipeline và bus RAM mất 2 chu kỳ mỗi truy cập. Nó chỉ về **nhánh B** (lõi tự viết),
không về thêm lệnh tùy biến — một lập luận định lượng cho phần sau của luận văn.

175 ảnh sai đều là lỗi *mô hình* (kit khớp golden 10.000/10.000): `4→9` 14 lần, `6→0` 11, `7→2` 11,
`8→0` 10 — đúng đặc trưng quen thuộc của CNN nhỏ trên MNIST.

### Cạm bẫy mới
- Golden từng sinh bằng `.venv-model` (numpy 1.26.4) nhưng script 10k chạy trong `.venv`
  (**numpy 2.5.4**, khác quy tắc quảng bá kiểu NEP 50). Đã kiểm: 10 CRC logit + 10 dự đoán tính lại
  trên numpy 2.5.4 **khớp từng bit** `fw/weights.h`, và đường vectorized khớp đường vô hướng. Nếu
  không khớp thì toàn bộ phép so 10.000 ảnh vô nghĩa ngay từ đầu.
- Tiến trình chạy dài ở chế độ nền có lúc bị hệ điều hành hạ ưu tiên xuống **2 % CPU** (11,5 phút
  tường chỉ dùng 14,8 s CPU). Mô phỏng nặng CPU phải chạy tiền cảnh; lần chạy 10k thì nghẽn ở UART
  nên không ảnh hưởng.
- CSV được ghi **từng dòng và flush** ngay, để 30 phút chạy không mất dữ liệu nếu bị ngắt.

Vật phẩm: `results/experiment/m1s/m1s_10k.csv` (10.000 dòng × 14 cột, 698 KB) ·
`results/experiment/m1s/v10k/` (22 file) · `experiment/m1s/v10k/stats.txt`.

## 2026-10-17 — A-V1+DOT4+C1: gỡ nút cổ chai conv1 bằng BỐ CỤC, và định lượng lệnh REQ

> **ĐÃ SỬA SỐ** — các con số của A-V0/A-V2 và mọi tỷ số so với A-V0 trong
> mục này là SAI (baseline đo bằng bản nháp chưa commit). Số đúng và cách phát hiện:
> xem mục nhật ký ngày 2026-10-17 "Sửa số liệu nhánh A" ở trên và `docs/KET_QUA_M1S.md` mục 3c.

Số liệu của bảng 2×2 chỉ đúng một chỗ để đánh tiếp: ở biến thể nhanh nhất (A-V1+DOT4), **conv1 chiếm
54,9 %** thời gian và **không dùng được DOT4** — vì `Cin=1`, 4 pixel liền nhau theo hàng thì có,
nhưng địa chỉ của chúng không chia hết 4 nên không nạp được bằng một `lw`. Nếu conv2 và dense có về 0
thì tổng cũng chỉ nhanh thêm 1,54× (Amdahl). Nên tôi làm conv1 trước REQ.

### Cách gỡ: không thêm một cổng logic nào
- Giữ **4 bản sao ảnh dịch 0/1/2/3 byte**, mỗi hàng đệm lên `PHS=32` byte:
  `ph[p][y][j] = img[y][j − p]`. Giá trị `img[y][x]` nằm ở offset `x + p`; chọn `p = (−x) & 3` thì
  `x + p` chia hết 4 → mọi lần đọc đều thẳng hàng. `x ≤ 25` nên offset xa nhất là 31 < 32, không tràn hàng.
- Trọng số conv1 nhân bản thành nhóm 4 với **tap thứ 4 = 0** (`w1x[oc][ky][0..3]`). Phép toán không
  đổi (cộng thêm `0 × pixel`), nên kết quả **vẫn khớp golden từng bit**.
- conv1 còn **3 lệnh DOT4** cho 3 hàng kernel, thay cho 9 phép nhân vô hướng.
- Chi phí: `.bss` **+3.584 byte**, sao chép **3.136 byte/ảnh** (đã tính trong số đo).

### Kết quả (trung vị 10 ảnh, kit, 27 MHz)
| | conv1 | TỔNG | ms | chu kỳ/MAC |
|---|---:|---:|---:|---:|
| A-V1+DOT4 | 1.600.258 | 2.917.102 | 108,0 | 15,19 |
| **A-V1+DOT4+C1** | **1.133.668** | **2.450.517** | **90,8** | **12,76** |

→ conv1 nhanh **1,41×**, tổng nhanh **1,19×**, tăng tốc tích luỹ so A-V0 lên **4,95×**; số lệnh
460.794 → **391.278**. Tài nguyên FPGA **không đổi** (cùng bitstream với A-V1+DOT4: LUT4 8.065,
4 MULT18X18, Fmax 71,89 MHz) — đây là lợi ích **miễn phí về phần cứng**. RAM 32.368/65.536 (49,4 %).

Kiểm tính đúng đắn: CRC32 5 lớp × 10 ảnh khớp golden, dự đoán khớp golden và khớp nhãn thật, số chu
kỳ kit = Verilator **bằng tuyệt đối** — lặp 2/2 lần đọc độc lập.

### Đo chi phí requantize (cơ sở cho lệnh REQ)
Hai vòng lặp 20.000 bước giống hệt nhau, khác đúng một thứ; toán hạng phụ thuộc biến đếm để GCC
không nhấc phép tính ra ngoài vòng (bài học từ F8):
`1.671.265 − 680.007 = 991.258` chu kỳ cho 20.000 lần → **49,6 chu kỳ/requantize**.
Mỗi ảnh requantize 7.344 giá trị (conv1 5.408 + conv2 1.936) → **363.990 chu kỳ = 14,9 %** của
A-V1+DOT4+C1. Một lệnh `REQ` ~1 chu kỳ sẽ cho **~78 ms, thêm 1,17×**.

**Kết luận cho kế hoạch**: REQ đáng làm nhưng không phải đòn lớn nhất. Đòn lớn hơn là giảm **số lệnh
trên mỗi giá trị đầu ra của conv1** (chỉ 9 MAC/đầu ra để chia sẻ chi phí cố định, so với 72 ở conv2)
— ví dụ tính nhiều kênh ra cùng lúc để dùng lại 3 từ ảnh đã nạp.

### Ghi nhận trung thực một lệch nhỏ
Thêm phần đo requantize (`REQ_BENCH`) vào bản v1dc làm mã `dense` dài thêm 4 byte (0x78 → 0x7c) và
tốn thêm **5 chu kỳ** (39.052 → 39.057). Đã kiểm `conv2`, `pool1`, `pool2` có kích thước mã **giống
hệt**, nên so sánh conv1 — thứ đang xét — không bị ảnh hưởng. Không làm tròn con số này đi.

### Cạm bẫy mới gặp
- `scripts/archive_gate.sh` ghi cứng `results/feasibility/` → thí nghiệm chính bị lưu sai chỗ; thêm
  biến môi trường `RESULTS_BASE` (thí nghiệm chính dùng `results/experiment`).
- Có lúc **hai tiến trình cùng điều khiển kit** (tôi mở vòng đo thứ hai khi vòng trước chưa xong) →
  số đọc sai. Phép kiểm nhãn biến thể trong từng block bắt được ngay ("kit báo A-V2, mong đợi A-V0").
  Quy tắc: **nạp và đo tuần tự**, không song song.

Vật phẩm: `results/experiment/m1s/` (6 archive + `m1s.csv` + log thô). Tài liệu:
`docs/KET_QUA_M1S.md`.

## 2026-10-17 — A-V1 (tối ưu phần mềm) + bảng 2×2 đầy đủ · KẾT QUẢ CHÍNH CỦA THÍ NGHIỆM

> **ĐÃ SỬA SỐ** — các con số của A-V0/A-V2 và mọi tỷ số so với A-V0 trong
> mục này là SAI (baseline đo bằng bản nháp chưa commit). Số đúng và cách phát hiện:
> xem mục nhật ký ngày 2026-10-17 "Sửa số liệu nhánh A" ở trên và `docs/KET_QUA_M1S.md` mục 3c.

Tôi tự chọn làm A-V1 trước A-V3, vì đó là khoảng trống **khoa học** lớn nhất: không có nhóm đối chứng
phần mềm thì phản biện sẽ hỏi ngay *"2,11× là nhờ lệnh tùy biến hay chỉ nhờ code tốt hơn?"* — và phát
hiện `noinline` (1,76× miễn phí) ở phiên trước cho thấy câu hỏi đó rất chính đáng.

Làm thành **bảng 2×2** trên cùng một `main.c`, hai cờ biên dịch độc lập (`OPT_KERNELS`, `USE_DOT4`):
A-V0 / A-V1 / A-V2 / A-V1+DOT4.

### Tối ưu phần mềm của A-V1 (không đổi một phép toán nào)
- **conv1**: đưa vòng kênh ra ra NGOÀI → 9 trọng số + bias nằm trong thanh ghi suốt cả mặt 26×26;
  9 phép nhân dùng **offset hằng số** (28, 56 là bước hàng ảnh) từ một con trỏ hàng; con trỏ ra chạy
  đều bước 8 byte. → 71,74 **→ 32,88** chu kỳ/MAC.
- **conv2**: bung hết 9 vị trí kernel bằng offset hằng số từ một con trỏ gốc (bước hàng `p1` = 104 byte),
  mỗi vị trí gọi macro `MAC8`. → 58,50 **→ 30,13** chu kỳ/MAC.
- **dense**: bung vòng trong bước 8. → 48,14 **→ 31,56** chu kỳ/MAC.
- `MAC8` có hai bản (8 phép nhân, hoặc 2 lệnh DOT4) nên bật/tắt DOT4 không cần sửa cấu trúc vòng lặp.

### Số đo trên kit (trung vị 10 ảnh, 27 MHz) — cả 4 biến thể ĐẠT
| Lớp | A-V0 | A-V1 | A-V2 | A-V1+DOT4 |
|---|---:|---:|---:|---:|
| conv1 | 3.491.721 | 1.600.258 | 3.491.721 | 1.600.258 |
| pool1 | 225.600 | 225.600 | 225.600 | 225.600 |
| conv2 | 8.153.979 | 4.199.609 | 1.924.815 | **986.226** |
| pool2 | 65.921 | 65.921 | 65.921 | 65.921 |
| dense | 192.552 | 126.224 | 48.552 | **39.052** |
| **TỔNG** | **12.129.818** | **6.217.657** | **5.756.654** | **2.917.102** |
| lệnh | 1.864.264 | 911.920 | 912.832 | **460.794** |
| ms @27 MHz | 449,3 | 230,3 | 213,2 | **108,0** |
| chu kỳ/MAC | 63,16 | 32,37 | 29,97 | **15,19** |
| tăng tốc so A-V0 | 1,00× | **1,95×** | **2,11×** | **4,16×** |

### KẾT QUẢ QUAN TRỌNG NHẤT: hai tối ưu nhân được với nhau
| Nguồn | Hệ số |
|---|---|
| Tối ưu phần mềm một mình (A-V0→A-V1) | **1,95×** |
| DOT4 trên C thẳng (A-V0→A-V2) | 2,11× |
| **DOT4 thêm vào C đã tối ưu** (A-V1→A-V1+DOT4) | **2,13×** |
| Cả hai | **4,16×** |
| Tích hai hệ số riêng | 1,95 × 2,13 = **4,16×** |

Tích **đúng bằng** số đo. Nghĩa là lợi ích của lệnh tùy biến **không biến mất khi phần mềm đã tối ưu**
(2,13× so với 2,11×). Lý do: hai tối ưu cắt hai phần khác nhau — phần mềm bỏ **tính chỉ số**
(thấy rõ ở conv1: 71,74 → 32,88 mà không có lệnh mới nào), DOT4 bỏ **nhân-cộng** (conv2 trên nền đã
tối ưu: 30,13 → 7,08). Đây là câu trả lời trực tiếp cho phản biện "baseline code kém".

### Tính đúng đắn
Cả 4 biến thể, 2/2 lần đọc mỗi biến thể: **CRC32 200/200 khớp golden** (5 lớp × 10 ảnh × 4 biến thể),
dự đoán **40/40** khớp golden và khớp nhãn, chu kỳ kit = Verilator **bằng tuyệt đối** cả 7 cột.
`conv1`/`pool1`/`pool2` cho **đúng cùng số chu kỳ** trong từng cặp so sánh — bằng chứng mỗi cặp chỉ
khác đúng một thứ.

### Tài nguyên
A-V0 và A-V1 dùng **cùng phần cứng** (LUT4 7.941, Fmax 71,76 MHz) — chỉ khác nội dung firmware trong
BSRAM, nên **toàn bộ 1,95× của A-V1 là miễn phí về phần cứng**. A-V2/A-V1+DOT4: LUT4 8.065
(**+124, +1,6 %**), +84 DFF, 4/48 MULT18X18, Fmax 71,89 MHz (**không giảm**).
RAM: 27,5–29,3 KB / 65,5 KB; A-V1 tốn thêm ~1,7 KB `.text` vì bung vòng.

### Nút cổ chai tiếp theo
Trong A-V1+DOT4, **conv1 chiếm 54,9 %** thời gian và không dùng được DOT4 (`Cin=1` không có 4 giá trị
liền nhau thẳng hàng 4 byte). Nếu conv2 + dense về 0 cũng chỉ nhanh thêm **1,54×**. Hướng tiếp:
một lệnh phục vụ conv1 — DOT4 bản không cần thẳng hàng, hoặc lệnh nhân-cộng 3 phần tử theo hàng ảnh,
hoặc đổi bố cục conv1 (nhân bản ảnh theo 4 pha dịch).
**→ REQ của A-V3 nên nhắm vào conv1, không phải conv2.**

### Một bài học vận hành
Lần đo đầu script báo *"kit báo biến thể A-V2, mong đợi A-V0"*: tôi đã khởi động vòng đo thứ hai khi
vòng đầu còn đang nạp kit, hai tiến trình tranh nhau cùng một kit. Phép kiểm **nhãn biến thể trong mỗi
khối dữ liệu** đã chặn được một số đo sai. → Mỗi khối số đo nên tự khai báo nó thuộc biến thể nào;
chi phí gần bằng không mà chặn được loại lỗi khó thấy nhất. Cũng đã đổi `--drain 0` → `--drain 2` cho
M1-S vì mỗi khối mất ~5 giây nên xả 2 giây là an toàn.

### Việc còn lại
- **A-V3 (+REQ)** — chưa làm; theo số liệu trên nên nhắm vào conv1.
- **Nhánh B** (lõi tự viết) — chưa làm.
- Đo trên nhiều hơn 10 ảnh trên kit; đo công suất.

## 2026-10-17 — THÍ NGHIỆM CHÍNH: M1-S chạy đầy đủ trên kit, A-V0 và A-V2

Lần đầu **một mô hình CNN hoàn chỉnh đã huấn luyện** chạy suy luận trên kit và đo được số chu kỳ.
Kết quả đầy đủ: `docs/KET_QUA_M1S.md`. Số liệu gốc: `results/experiment/m1s/m1s.csv`.

### Mô hình
- Huấn luyện M1-S bằng PyTorch (8 epoch, Adam, batch 128, seed 1234): **float 98,29 %** trên
  10.000 ảnh test. Tham số 5.258 — khớp đúng con số của kế hoạch.
- Lượng tử hoá int8 sau huấn luyện, đối xứng, zero-point = 0; hiệu chuẩn thang activation trên 512
  ảnh train. requantize gemmlowp: lớp 1 `M0=1138411053, shift=8`; lớp 2 `M0=1108363094, shift=8`.
  Dense **không** requantize (giữ int32 rồi argmax) → bỏ được một cặp (M0, shift) và một lần làm tròn.
- **int8 98,25 %**, chênh float **+0,04 điểm %** — tiêu chí kế hoạch là ≤1 điểm → ĐẠT rất rộng.

### Quyết định thiết kế quan trọng: bố cục channels-last
`DOT4` nạp 4 byte liền nhau bằng `lw` nên **cần địa chỉ thẳng hàng 4 byte** (lõi bật
`CATCH_MISALIGN`). Vì vậy activation lưu theo **[H][W][C]** và trọng số conv theo
**[Cout][ky][kx][Cin]**: conv2 có `Cin=8` nên 4 kênh vào liền nhau luôn thẳng hàng, dùng đúng
2 lệnh DOT4 cho mỗi vị trí kernel, không bỏ sót MAC nào. Hệ quả: `m1s_w3` phải **hoán vị cột** so
với PyTorch (torch làm phẳng theo (C,H,W), ta theo (H,W,C)). Golden Python viết lại theo đúng bố cục
này nên mọi CRC32 và thứ tự làm phẳng khớp firmware.

**conv1 không dùng được DOT4** vì `Cin=1`: không có 4 giá trị liền nhau để cộng dồn mà vẫn thẳng hàng.
conv1 chiếm 25,3 % số MAC nhưng 28,8 % thời gian A-V0 — và trở thành nút cổ chai của A-V2.

### Số đo trên kit (trung vị 10 ảnh, 27 MHz)
| Lớp | A-V0 | A-V2 | Tăng tốc | chu kỳ/MAC V0 → V2 |
|---|---:|---:|---:|---|
| conv1 | 3.491.721 | 3.491.721 | 1,00× | 71,74 → 71,74 |
| pool1 | 225.621 | 225.621 | 1,00× | — |
| conv2 | 8.153.979 | **1.924.815** | **4,24×** | 58,50 → 13,81 |
| pool2 | 65.924 | 65.924 | 1,00× | — |
| dense | 192.552 | **48.552** | **3,97×** | 48,14 → 12,14 |
| **TỔNG** | **12.129.818** | **5.756.654** | **2,11×** | 63,16 → **29,97** |
| thời gian | 449,3 ms | 213,2 ms | | |

Tính đúng đắn, cả hai biến thể, 2/2 lần đọc: **CRC32 50/50 khớp golden** (5 lớp × 10 ảnh),
dự đoán **10/10** khớp golden và khớp nhãn, số chu kỳ kit = Verilator **bằng tuyệt đối** cả 7 cột.

Tài nguyên: A-V0 LUT4 7.941 / Fmax 71,76 MHz; A-V2 LUT4 8.065 / Fmax 71,89 MHz →
DOT4 tốn **+124 LUT4 (+1,6 %)**, +84 DFF, 4/48 MULT18X18, **Fmax không giảm**.
RAM 27.564/65.536 byte (42,1 %).

### Ba phát hiện
1. **Tăng tốc bị chặn bởi conv1, đúng dự báo ở F8.** Trong A-V2 conv1 chiếm 60,7 % thời gian.
   Giới hạn Amdahl = 12.129.818/3.783.266 = **3,21×**; DOT4 đã cắt 6.373.164 trong 8.346.552 chu kỳ
   có thể cắt = **76,4 %**. Muốn đi xa hơn phải nhắm vào conv1.
2. **Ước tính ở F7 sát**: F7 ngoại suy ≈516 ms, thực đo A-V0 là **449,3 ms** → ước tính cao hơn 15 %,
   lệch theo hướng an toàn. Nguyên nhân đúng như F7 đã nêu: conv2 có `Cin=8` nên chi phí/MAC *thấp hơn*
   conv1 (58,50 so với 71,74) do chia sẻ được phần tính chỉ số.
3. **Một cái bẫy của trình biên dịch, không liên quan phần cứng.** Ban đầu 5 lớp là hàm `static` gọi
   một lần; GCC `-O2` nội suy hết vào `main` và tràn thanh ghi → A-V0 chạy **21.350.804** chu kỳ.
   Thêm `__attribute__((noinline))` cho mỗi lớp đưa về **12.129.818** chu kỳ — **nhanh hơn 1,76 ×
   mà không đổi một dòng thuật toán**. Tệ hơn: khi chưa có `noinline`, cấp phát thanh ghi của conv1
   **thay đổi theo** việc conv2 dùng DOT4 hay không (3.803.170 so với 4.950.316 chu kỳ), làm phép so
   sánh A-V0/A-V2 mất ý nghĩa. Sau khi sửa, conv1/pool1/pool2 có **kích thước mã giống hệt** và cho
   **đúng cùng số chu kỳ** ở hai biến thể — đó là bằng chứng phép so sánh chỉ khác một thứ.
   → **Quy tắc phương pháp: khi so hai biến thể tập lệnh, cố định ranh giới hàm và phải kiểm rằng các
   lớp KHÔNG thay đổi cho ra đúng số chu kỳ cũ.**

### Hạ tầng
- `model/`: `mnist.py` (nạp idx.gz), `train_m1s.py`, `quantize_m1s.py`, `golden_m1s.py` (golden int8
  đúng từng bit, có `test_requant_equiv()` kiểm bản vector hoá khớp bản vô hướng).
- `fw/weights.h` sinh tự động: trọng số int8, bias int32, (M0, shift), 10 ảnh thử, nhãn, dự đoán
  golden và **CRC32 golden của từng lớp** — firmware tự kiểm và host kiểm lại.
- `experiment/m1s/`: firmware 5 lớp + Makefile hai biến thể, dùng lại SoC của F5 và khối DOT4 của F8.
- `scripts/m1s_check.py`: đọc kit, đối chiếu golden (đọc lại từ `weights.h`, không hard-code) và
  Verilator, ghi CSV.
- `.venv-model` riêng (Python 3.12 + torch 2.2.2 + numpy 1.26.4): Python 3.14 không có wheel torch cho
  macOS x86_64; torch 2.2.2 là bản cuối còn wheel và nó cần numpy < 2. Ghi rõ trong `env/VERSIONS.md`.
- `scripts/archive_gate.sh` thêm `RESULTS_BASE` để lưu ra `results/experiment/`.

### Hai lỗi script của tôi, đã sửa
- `m1s_check.py` dùng regex `^M1S,([a-z]+),(.*)$` bắt buộc dấu phẩy thứ hai nên dòng `M1S,done`
  không khớp và không bao giờ nhận ra khối đã đủ. Sửa thành `,?`.
- `archive_gate.sh` hard-code `results/feasibility/` nên lưu nhầm vào
  `results/feasibility/experiment/m1s`. Sửa bằng biến `RESULTS_BASE`.

### Việc còn lại của thí nghiệm chính
- **A-V1** (chỉ tối ưu phần mềm, nhóm đối chứng) — chưa làm. Lưu ý: phát hiện `noinline` ở trên thực
  chất đã là một tối ưu phần mềm 1,76×, nên A-V1 cần định nghĩa lại cho rõ đâu là "đối chứng".
- **A-V3** (+ lệnh REQ) — chưa làm. Theo số liệu trên, REQ nên nhắm vào conv1.
- **B-V*** (lõi tự viết) — chưa làm.
- Đo trên nhiều ảnh hơn 10 trên kit; đo công suất.

## 2026-10-17 — Cổng F8 (lệnh tùy biến DOT4 qua PCPI) — ĐẠT · GIAI ĐOẠN KHẢ THI HOÀN TẤT

Cả ba tiêu chí đạt, cho **cả hai biến thể** bitstream, 3/3 lần đọc mỗi bản:
CRC bản DOT4 = bản vô hướng = Python (`3D68C1ED`), chu kỳ kit = Verilator **bằng tuyệt đối**,
và có **số tăng tốc thật: 3,985×**.

### Khối DOT4 (`rtl/ext/pcpi_dot4.v`)
- `rd = Σ_{i=0..3} int8(rs1[8i+7:8i]) · int8(rs2[8i+7:8i])`, opcode custom-0 `0001011`,
  funct3 `000`, funct7 `0000000`. Phía C: `.insn r 0x0B, 0, 0, rd, rs1, rs2`.
- Giao thức PCPI lấy **đúng dạng của `picorv32_pcpi_fast_mul`** trong chính lõi: chốt toán hạng,
  thanh ghi dịch `active[1:0]`, trả lời bằng `pcpi_wr` + `pcpi_ready` cùng một chu kỳ, `pcpi_wait = 0`.
  Độ trễ 2 chu kỳ, dưới timeout 16 chu kỳ của lõi.
- Hai đường nhân chọn bằng cờ biên dịch: `PCPI_DOT4_DSP` gọi **trực tiếp `MULT18X18`** (cách PRM đã
  ĐẠT ở F4), mặc định là nhân hành vi (cho mô phỏng và cho bản `-nodsp` nhân bằng logic).
- `soc.v` thêm tham số `WITH_DOT4` (mặc định 0). **Đã kiểm hồi quy**: với `WITH_DOT4=0`, F7 cho lại
  **y hệt** 4.921.446 / 3.533.204 chu kỳ và cùng CRC — thay đổi không ảnh hưởng F5/F6/F7.

### Testbench riêng cho khối (bước 2 của kế hoạch)
`feasibility/F8_dot4/tb_dot4.v`, Icarus: **1.000.108 phép DOT4 đúng** —
1.000.000 cặp từ LFSR + 108 giá trị biên (mọi tổ hợp của {−128, −127, −1, 0, 1, 127} trên cả 4 lane,
cộng quét từng lane trong khi ba lane còn lại giữ giá trị xấu nhất). Tham chiếu tính **độc lập** trong
testbench (tách lane sang `reg signed [7:0]`, cộng dồn trong `integer`), khác cách của DUT.
Có thêm một phép kiểm quan trọng: **khối phải IM LẶNG với lệnh không phải của nó** (thử bằng `MUL`) —
nếu không nó sẽ phá lệnh `MUL`/`DIV` mà lõi xử lý qua PCPI nội bộ.

### Số đo trên kit (bài A, 102.400 MAC, 25.600 lệnh DOT4)
| Bản | chu kỳ | lệnh | CPI | chu kỳ/MAC |
|---|---:|---:|---:|---:|
| vô hướng | 4.921.446 | 717.812 | 6,86 | 48,06 |
| **DOT4** | **1.235.011** | 180.205 | 6,85 | **12,06** |

- **Tăng tốc 3,985×**; số lệnh giảm **3,983×**.
- **Tăng tốc bằng đúng tỉ lệ giảm số lệnh** vì CPI gần như không đổi → DOT4 nhanh hơn **không** nhờ
  phép nhân nhanh hơn, mà nhờ làm 4 MAC trong một lệnh trên lõi mà mỗi lệnh tốn gần 7 chu kỳ.
- **Độ trễ DOT4 đo được: đắt hơn `ADD` đúng +1,000 chu kỳ/lệnh** (vòng DOT4 3.500.041 vs vòng ADD
  3.400.041 trên 100.000 vòng).
- **Bật PCPI tốn +0 chu kỳ**: bản vô hướng trên bitstream CÓ PCPI cho đúng 4.921.446 chu kỳ, bằng
  tuyệt đối số của F7 trên bitstream KHÔNG có PCPI.
- CSV: `results/feasibility/F8/dot4.csv`.

### Chi phí phần cứng, so với chính bản nền F5
| Thiết kế | LUT4 | ΔLUT4 | DFF | ΔDFF | MULT18X18 | Fmax | ΔFmax |
|---|---:|---:|---:|---:|---:|---:|---:|
| F5 SoC (nền, không PCPI) | 7.950 | — | 1.069 | — | 0 | 70,05 | — |
| F8 + DOT4, `MULT18X18` | 8.065 | **+115** | 1.153 | +84 | **4** | 71,89 | **+1,83** |
| F8 + DOT4, nhân bằng LUT | 9.086 | +1.136 | 1.153 | +84 | 0 | 73,83 | +3,78 |

Fmax **không giảm** ở cả hai bản (nhúc nhích lên, trong phạm vi nhiễu place & route) vì DOT4 trả lời
trong 2 chu kỳ và phép nhân int8 ngắn hơn đường tới hạn hiện có (bộ nhân 32×32 bằng LUT của lõi).

### Một lỗi đo của chính tôi, bắt được trước khi lên kit
Lần đầu viết hai vòng đo độ trễ với **toán hạng hằng số**: `dot4(0x01020304, 0x05060708)`. GCC nhấc
cả lệnh asm ra ngoài vòng lặp (asm không `volatile`, đầu vào bất biến → loop-invariant code motion),
nên hai vòng trở thành giống hệt nhau và phép đo vô nghĩa — chênh **1 chu kỳ trên 100.000 vòng**.
Phát hiện bằng cách đọc disassembly: lệnh `.insn` nằm ở `2b4`, **ngoài** thân vòng bắt đầu ở `2b8`.
Sửa: cho toán hạng phụ thuộc biến đếm (`^ i`, `+ i`) ở **cả hai** vòng, nên chúng vẫn có cùng số lệnh
chuẩn bị toán hạng. Sau khi sửa, lệnh `.insn` nằm trong thân vòng và chênh thành đúng +1,000 chu kỳ/lệnh.
**Bài học**: mọi micro-benchmark bằng inline asm phải kiểm disassembly trước khi tin số đo.

### Giới hạn của kết quả, cần nói rõ trong luận văn
3,985× là tăng tốc của **bài tích vô hướng**, không phải của cả mô hình. Bài conv1 ở F7 tốn
72,59 chu kỳ/MAC, trong đó phần chỉ số 2 chiều và requantize **không** được DOT4 cắt. Tăng tốc thật
của một lớp conv sẽ **nhỏ hơn 3,985×** và chỉ đo được ở giai đoạn thí nghiệm chính. Đây cũng là lý do
kế hoạch có thêm lệnh REQ.

### Trạng thái cuối giai đoạn khả thi
Chín cổng F0 → F8 **đã làm xong**. Kết luận: **GO CÓ ĐIỀU KIỆN**, ba điều kiện và 11 đề xuất điều chỉnh
ở `docs/FEASIBILITY_REPORT.md`. Việc duy nhất còn treo: điều kiện 4 của F6 (ba lần tắt/bật nguồn),
người thực hiện đã quyết định bỏ — báo cáo ghi rõ là "KHÔNG KIỂM", không ghi là đã đạt.

## 2026-10-17 — Cổng F7 (kernel int8 thật, đúng từng bit) — ĐẠT

Cả ba tiêu chí đều đạt: **CRC trên kit = Python** cho cả hai bài, **chu kỳ kit = Verilator bằng
tuyệt đối** (cả `cycles`, `hw_count`, `instret`), và **có số chu kỳ/MAC**. Lặp lại 3/3 lần đọc độc lập.

### Ràng buộc phải giải trước khi viết code
Kế hoạch ghi "100 cặp vector int8 dài 1.024". Lưu rời cần 100 × 2 × 1024 = **204.800 byte**, vượt RAM
64 KB tới 139.264 byte. **Sai lệch có chủ ý**: lưu một **pool 8.192 byte** int8 và lấy 100 cặp **cửa sổ**
khác offset trong pool (`off_a = (i·71) mod span`, `off_b = (i·131 + 3000) mod span`). Vẫn là 100 phép
tích vô hướng dài 1.024 trên dữ liệu khác nhau, nhưng chỉ tốn 8 KB. Chính bước 5 của F7 ("kiểm tra dung
lượng") là lý do buộc phải làm vậy.

### Dữ liệu và golden
- `scripts/gen_f7_data.py` (numpy, seed `0x5EEDF007`) sinh `f7_data.h` và in CRC32 kỳ vọng.
- Bài A: 100 × 1.024 = **102.400 MAC**; dot nhỏ/lớn = −434.947 / 403.186; **CRC32 = 64F298C2**.
- Bài B: Conv 3×3, 1→8 kênh, ảnh 28×28 int8, ra 26×26×8 (không đệm biên) = **48.672 MAC** — đúng con số
  của kế hoạch và đúng lớp conv1 của M1-S. Bias int32, **ReLU trên int32**, rồi requantize
  `(M0 int32, shift)` kiểu gemmlowp. `acc` lớn nhất sau ReLU = 31.227 → chọn `M0 = 1936565777`,
  `shift = 8` để đầu ra rơi vào **0..110** (không bão hoà, không dồn về 0). **CRC32 = 661C5304**.
- Hai hàm requantize `sat_rdhmul` (SaturatingRoundingDoublingHighMul) và `rdiv_pot`
  (RoundingDivideByPOT) được cài **y hệt** ở Python và C, nên khớp từng bit. Bản C dùng
  `(int64_t)a*(int64_t)b` → lệnh `mulh` của rv32im; CRC khớp cũng đồng thời chứng minh `mulh` đúng
  trên kit (bổ sung cho khoá `arith` của F5 chỉ kiểm `mul`/`div`/`rem`).
- CRC32 trong firmware tính **ngoài cửa sổ đo**, không tính vào số chu kỳ của kernel.

### Số đo (kit = Verilator bằng tuyệt đối, 3/3 lần)
| Bài | MAC | chu kỳ | hw_count | instret | CPI | chu kỳ/MAC | thời gian @27 MHz |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — dot int8 1024 ×100 | 102.400 | 4.921.446 | 4.921.485 | 717.812 | 6,86 | **48,06** | 182,3 ms |
| B — conv1 3×3 1→8 kênh | 48.672 | 3.533.204 | 3.533.252 | 570.232 | 6,20 | **72,59** | 130,9 ms |

CSV: `results/feasibility/F7/kernel.csv`.

**Dung lượng**: `.text` 11.296 + `.bss` 5.808 = **17.104 / 65.536 byte (26,1 %)**. Trong `.text` có
9.480 byte dữ liệu tĩnh (pool 8.192 + ảnh 784 + w 72 + bias 32 + offset 400). Còn dư 48 KB.

**Tài nguyên FPGA**: y hệt F5/F6 (RTL không đổi): BSRAM 32/46, LUT4 7.950, Fmax 70,05 MHz.

### Ước tính THÔ cho M1-S — ghi rõ là ước tính
Ngoại suy từ chu kỳ/MAC của bài B (72,59) cho 192.064 MAC: **≈ 13,94 triệu chu kỳ ≈ 516 ms @27 MHz**.
Ba lý do nó có thể lệch, đã ghi vào báo cáo: (a) MaxPool và Dense có chi phí/MAC khác conv; (b) conv2
có 16 kênh vào nên tỉ lệ nạp lại trọng số khác conv1; (c) chu kỳ/MAC của conv1 đã gồm chi phí
requantize cho 5.408 điểm đầu ra, phần này không tỉ lệ với số MAC.

### Hai nhận xét đáng ghi cho các bước sau
1. **Conv đắt hơn dot 1,51 lần trên mỗi MAC** (72,59 so với 48,06) dù cùng là nhân-cộng int8. Chênh này
   đến từ chỉ số 2 chiều, nạp lại trọng số cho từng vị trí, và requantize. **Đó chính là khoảng trống
   DOT4 ở F8 nhắm vào** — và cũng là lời cảnh báo rằng DOT4 chỉ cắt được phần nhân-cộng, không cắt
   phần chỉ số.
2. **Chênh `hw_count − cycles` ở F7 là 39 (bài A) và 48 (bài B)**, không phải 24 như F6. Không mâu thuẫn:
   F6 chứng minh chênh đó là hằng số **theo độ dài đoạn đo**; giá trị hằng số phụ thuộc chuỗi lệnh giữa
   lúc ghi `HWC_CTRL` và lúc đọc `HWC_VALUE`, mà hai bài có đoạn mã bao quanh khác nhau.
   **Kết luận thực dụng: hiệu chuẩn chênh này cho từng điểm đo, không dùng một hằng số chung.**

### Việc tiếp theo
- **F8** — lệnh tùy biến DOT4 qua PCPI. Theo F4, khối nhân phải **gọi trực tiếp `MULT18X18`** (cách PRM);
  cần giữ cả đường LUT để mô phỏng đối chiếu vì `MULT18X18` là blackbox không có mô hình mô phỏng.
  Bài A của F7 sẽ được viết lại với `dot4()` để so trực tiếp với 4.921.446 chu kỳ hiện tại.
- Không cần người dùng làm gì ở F8.

## 2026-10-17 — Cổng F6 (độ tin cậy của phép đo) — ĐANG LÀM, 4/5 bước xong

**Chưa đánh ĐẠT**: bước 4 (đo lại qua 3 lần tắt/bật nguồn kit) cần người dùng rút/cắm cáp USB,
người dùng chọn **hoãn làm sau**. Theo quy tắc 1 trong CLAUDE.md, **không sang F7** khi F6 chưa ĐẠT.

### Cách làm
- Dùng **đúng SoC của F5** (`feasibility/F5_soc/soc.v`, `top.v`), chỉ thay firmware
  (`feasibility/F6_measure/main.c`) — nên mọi kết luận vẫn áp dụng cho nền tảng đã kiểm ở F5.
- Firmware in CSV: `F6,cal,<delta>,<số lần>` cho từng giá trị overhead khác nhau;
  `F6,len,<N>,<mcycle>,<hwc>,<instret>` cho 5 độ dài; `F6,hi,...` cho bài `rdcycleh`.
- `scripts/f6_check.py` đọc kit, so với log Verilator, kiểm từng điều kiện ĐẠT và ghi
  `results/feasibility/F6/measure.csv` (cộng dồn qua các lần bật nguồn).

### Kết quả 4 điều kiện đã kiểm
1. **Overhead là hằng số**: đo `rdcycle` hai lần liên tiếp 1.000 lần → **đúng một giá trị duy nhất:
   5 chu kỳ**, xuất hiện 1000/1000 lần. Cả trên kit và trong Verilator.
2. **`hw_count − mcycle` là hằng số**: **24 chu kỳ** ở cả 5 độ dài.

   | N | mcycle | hw_count | instret | hw−mcycle |
   |---:|---:|---:|---:|---:|
   | 10 | 141 | 165 | 23 | 24 |
   | 100 | 1.401 | 1.425 | 203 | 24 |
   | 1.000 | 14.001 | 14.025 | 2.003 | 24 |
   | 10.000 | 140.001 | 140.025 | 20.003 | 24 |
   | 100.000 | 1.400.001 | 1.400.025 | 200.003 | 24 |

3. **Kit = Verilator bằng tuyệt đối** ở cả 5 độ dài, cho cả ba cột.
4. **`rdcycleh`**: `busy_loop(320.000.000)` → `rdcycleh` **0 → 1**, `rdcycle` 115.922.609 → 300.955.328.
   Tổng = 2^32 + 300.955.328 − 115.922.609 = **4.480.000.015 chu kỳ** = **165,9 s @27 MHz**.
   Mô hình 14 chu kỳ/vòng cho 4.480.000.000 → **lệch đúng 15 chu kỳ** (vào/ra vòng lặp + đọc counter).

**Mô hình chu kỳ suy ra**: `mcycle = 14·N + 1`, `instret = 2·N + 3` — đúng tuyệt đối ở cả 5 độ dài.
Mỗi vòng 2 lệnh tốn đúng 14 chu kỳ (7 chu kỳ/lệnh với bus 1 chu kỳ chờ). Đây là cơ sở để F7
ngoại suy số chu kỳ/MAC.

### Ba lỗi của chính tôi, đã sửa
1. `f6_check.py` lúc đầu **xả 1,5 s bộ đệm trước khi đọc** (cách làm đúng ở F3) nhưng ở F6 thì sai:
   khối đo đầu tiên được in ngay sau reset và nằm sẵn trong bộ đệm, nên bị xả mất; sau đó kit im
   166 s để chạy bài `rdcycleh` → không đọc được gì. Sửa: dùng `--drain 0` cho F6.
2. `parse_block` trả về cả khối **chưa đầy đủ** (chưa thấy `F6,done`) → báo thiếu độ dài 100.000.
   Sửa: chỉ trả về khối đã thấy `F6,done`.
3. Script thử cổng JTAG (`...170`) trước với timeout 12–15 s, tiêu hết cửa sổ in của kit.
   Sửa: Makefile truyền `--port /dev/cu.usbserial-20250303171` (cổng UART đã xác định ở F2).
   Thêm đích `make cycle RUN=n` (nạp lại SRAM rồi đo ngay) và `make f6check-hi`.

### Thay đổi firmware do phản hồi của người dùng
Người dùng phản hồi **"LED sáng hết chói mắt quá"**. Firmware F5/F6 trước đó bật cả 6 LED
(`LED_REG = 0x3F`) trong lúc nghỉ. Đã sửa **chính sách LED: nhiều nhất MỘT LED sáng, tắt hết khi
rảnh**, cho cả `fw/main.c` (F5) và `feasibility/F6_measure/main.c`. Đồng thời nạp ngay bitstream
F4-PRM để tắt đèn cho người dùng trong lúc sửa.
Ghi chú về F5: thay đổi này chỉ ở các lệnh ghi LED **nằm ngoài cửa sổ đo**, nên không ảnh hưởng
bất kỳ số đo nào của F5; vật phẩm đã lưu của F5 là của bản đã kiểm chứng.
Cũng vì chờ 166 s mỗi lần bật nguồn là quá lâu, firmware F6 đổi sang chạy bài `rdcycleh`
**sau 5 khối in** (`HI_AFTER=5`) thay vì sau khối đầu.

### Quyết định của người dùng (cùng ngày, sau khi đọc kết quả 4/5 bước)
Người dùng quyết định **bỏ điều kiện 4** (3 lần tắt/bật nguồn) và coi F6 là xong, rồi yêu cầu
viết tài liệu tổng kết giai đoạn khả thi.

Cách ghi nhận trong báo cáo (để trung thực): F6 ghi là **ĐẠT với 4/5 điều kiện kiểm được**, và
điều kiện 4 ghi rõ là **"KHÔNG KIỂM — bỏ theo quyết định của người thực hiện"**, chứ KHÔNG ghi là
đã kiểm và đạt. Mục 7 của `docs/FEASIBILITY_REPORT.md` nêu rủi ro còn lại, ba quan sát làm rủi ro
đó nhỏ (hơn 20 lần nạp SRAM trong F1–F6 đều cho số giống nhau; 3 lần đọc độc lập ở cả F5 và F6;
mô hình `mcycle = 14·N + 1` khớp tuyệt đối trải 4 bậc độ lớn và được xác nhận lại ở quy mô 4,48 tỷ
chu kỳ), và đề nghị chạy điều kiện 4 trước khi lấy số đo chính thức cho luận văn.

### Tài liệu đã viết
- `docs/FEASIBILITY_REPORT.md` — viết lại thành báo cáo hoàn chỉnh 8 mục, kết luận
  **GO CÓ ĐIỀU KIỆN** kèm 9 đề xuất điều chỉnh cho kế hoạch thí nghiệm chính.
- `docs/HUONG_DAN.md` — hướng dẫn dựng lại môi trường và chạy lại mọi phép đo, kèm bảng
  "những cái bẫy đã gặp".
- `README.md` — cập nhật trạng thái và ba quy tắc build bắt buộc.

### Việc tiếp theo
- F7 (kernel int8 thật) và F8 (DOT4 qua PCPI) — chưa làm.
- Nếu muốn hoàn tất điều kiện 4 của F6 về sau: rút/cắm cáp rồi
  `cd feasibility/F6_measure && make cycle RUN=2` (lặp `RUN=3`, `RUN=4`).

## 2026-10-17 — Cổng F5 (SoC PicoRV32 chạy firmware C) — ĐẠT

Tiêu chí quan trọng nhất của cổng này — **`F5,loop` trên kit bằng TUYỆT ĐỐI Verilator** — đã đạt:
**14.006 chu kỳ** cho `busy_loop(1000)`, lặp lại 3/3 lần đọc độc lập. Ngoài ra 7 khoá khác cũng
khớp tuyệt đối.

### Lõi và tham số (ghim ở env/VERSIONS.md)
- `YosysHQ/picorv32` commit **`ef203c2b0a3fb793280f5114941416c425c5b461`** (2026-09-07),
  `rtl/picorv32/picorv32.v`, sha256 `0836050971b3c6…`.
- Tham số đã **đối chiếu README của picorv32 tại chính commit đó**:
  `ENABLE_COUNTERS=1, ENABLE_COUNTERS64=1, ENABLE_REGS_16_31=1, ENABLE_REGS_DUALPORT=1,
  BARREL_SHIFTER=1, COMPRESSED_ISA=0, ENABLE_MUL=0, ENABLE_FAST_MUL=1, ENABLE_DIV=1,
  ENABLE_IRQ=0, ENABLE_PCPI=0, PROGADDR_RESET=0, STACKADDR=0x00010000`.
  README xác nhận hai điều kế hoạch đã nêu: đặt cả `ENABLE_MUL` và `ENABLE_FAST_MUL` thì
  `ENABLE_MUL` bị bỏ qua; các lõi PCPI nội bộ (mul/div) chạy không cần `ENABLE_PCPI`.

### SoC (`feasibility/F5_soc/soc.v`)
- Bản đồ bộ nhớ đúng như kế hoạch: RAM 64 KB tại 0x0000_0000; UART data 0x1000_0000,
  status 0x1000_0004 (bit0 tx_busy, bit1 rx_valid); bộ đếm phần cứng ctrl 0x1000_0010 /
  value 0x1000_0014; LED 0x1000_0020.
- RAM: `reg [31:0] ram[0:16383]` + `$readmemh`, **ghi theo byte** theo `mem_wstrb`.
  Đã kiểm trước khi viết: `share/yosys/gowin/brams.txt` khai báo `byte 9;` và `wrbe_separate;`
  nên BSRAM của Gowin hỗ trợ ghi theo byte → kết quả: **BSRAM 32/46**, không rơi xuống LUTRAM.
- Bus: mỗi truy cập **đúng 2 chu kỳ** (1 chu kỳ chờ) cho cả RAM và ngoại vi → số chu kỳ tất định,
  giống nhau giữa Verilator và kit.
- `dbg_tx_valid/dbg_tx_byte` chỉ dùng cho Verilator để in UART ra stdout ngay. **Khối `uart_tx` thật
  vẫn được dùng ở cả hai môi trường**, nên `tx_busy` diễn ra y như nhau và không làm lệch số chu kỳ.

### Firmware (`fw/`)
- `start.S` đặt `sp = 0x00010000`, xoá `.bss`, gọi `main`; `_start` nằm **đúng tại địa chỉ 0**
  (kiểm bằng `nm`: `00000000 T _start`) vì `PROGADDR_RESET = 0`.
- `link.ld`: tất cả trong RAM 64 KB, `.text.start` được `KEEP` ở đầu.
- `main.c` in các dòng CSV: `hello` (git hash nhúng lúc biên dịch), `cycle`, `loopn`, `loop`,
  `hwc`, `instret`, `arith`, `ram`, `done`.
- `busy_loop` viết bằng asm cố định (`addi` + `bnez`, đúng 2 lệnh/vòng) nên không phụ thuộc
  mức tối ưu của trình biên dịch.
- Kích thước: **`.text` = 1.220 byte**, `.bss` = 0 (log: `artifacts/firmware.size.txt`).
- `scripts/bin2hex.py`: .bin → hex từ 32 bit little-endian, đệm 0 cho đủ 16.384 từ.

### Số đo (kit = Verilator, khớp tuyệt đối 3/3 lần)
| khoá | giá trị | ý nghĩa |
|---|---|---|
| `hello` | d2a80f1 | git hash nhúng trong firmware |
| `loopn` | 1000 | số vòng của busy_loop |
| **`loop`** | **14.006** | `rdcycle` sau − trước (≈14,0 chu kỳ/vòng = 7,0 chu kỳ/lệnh với 1 chu kỳ chờ) |
| `hwc` | 14.035 | bộ đếm phần cứng cho cùng đoạn → **chênh 29 chu kỳ** so với `rdcycle` |
| `instret` | 2.004 | 2.000 lệnh của vòng lặp + 4 lệnh ngoài |
| `arith` | C91C7978 | tổng vài phép MUL/MULH/DIV/REM → **lệnh nhân/chia đúng trên kit** |
| `ram` | EFEEC031 | tổng kiểm 8 từ `.rodata` → **`$readmemh` nạp firmware đúng** |

Tài nguyên: **BSRAM 32/46** · LUT4 **7.950**/20.736 (38,3 %) · DFF 1.069 · ALU 754 ·
RAM16SDP4 32 (tệp thanh ghi) · IOB 9 · **Fmax 70,05 MHz** @ ràng buộc 27 MHz.

### Hai quyết định đáng ghi
1. **Bắt buộc `synth_gowin -nodsp` cho SoC** — hệ quả trực tiếp của F4. `ENABLE_FAST_MUL=1` tạo bộ
   nhân 32×32; nếu để yosys suy luận DSP thì lệnh `MUL` sẽ sai trên kit. Khoá `arith` khớp tuyệt đối
   chứng minh cách này đúng. Giá phải trả: LUT4 lên 7.950 (38,3 %) và Fmax 70,05 MHz (vẫn dư 2,6 lần).
   F8 vẫn dùng được DSP cho DOT4 vì đó là **gọi primitive trực tiếp**, `-nodsp` chỉ tắt phần *suy luận*.
2. UART in ra stdout trong Verilator bằng cách **bắt lệnh ghi lên bus**, không giải mã dạng sóng chân TX
   → mô phỏng nhanh mà vẫn giữ đúng thời gian của `uart_tx` thật.

### Vấn đề gặp phải
- **Verilator không biên dịch được trên máy này**: `fatal error: 'cstddef' file not found`.
  Nguyên nhân: `/Library/Developer/CommandLineTools/usr/include/c++/v1` thiếu nội dung
  (CLT 26.5.0), nên `clang++` không thấy libc++; `-isysroot` **không** cứu được vì clang chỉ tìm
  libc++ trong đường của toolchain. Thư viện vẫn có trong SDK.
  Cách khắc phục đã đưa vào `env/setup_env.sh`: tự thử biên dịch `#include <cstddef>`, nếu thất bại
  thì đặt `TN20K_CXX_INC=-I$(xcrun --show-sdk-path)/usr/include/c++/v1`; Makefile của F5 truyền cờ
  này cho verilator qua `-CFLAGS`. Các phiên sau không phải xử lý lại.
- `scripts/archive_gate.sh` ban đầu lưu cả thư mục `obj_dir` của Verilator (42 file, 3,4 MB file .o/.a).
  Đã lọc: bỏ `obj_dir/` và `*.o/*.a/*.d/*.dat`. Còn 21 file, 2,6 MB.

### Việc tiếp theo / cần người dùng
- F6 (độ tin cậy của phép đo). **Cổng này CẦN người dùng**: bước 4 của kế hoạch yêu cầu
  rút/cắm nguồn kit 3 lần rồi nạp lại SRAM, để kiểm số đo có giống hệt qua các lần bật nguồn.
  Tôi sẽ hỏi trước khi tới bước đó.
- Dữ liệu sẵn có cho F6: chênh `hwc − loop` = **29 chu kỳ** ở độ dài 1.000 vòng; F6 sẽ kiểm hằng số
  này ở các độ dài 10/100/1k/10k/100k.

## 2026-10-17 — Cổng F4 (khối nhân DSP) — ĐẠT CÓ DỰ PHÒNG

Kết luận ngắn: **phép nhân int8 có dấu do yosys tự suy luận vào DSP cho kết quả SAI trên kit này.**
Cách dùng được là **gọi trực tiếp primitive `MULT18X18` ở chế độ không dấu**. Biến thể nhân bằng
logic (`-nodsp`) cũng đúng nhưng tốn 2,2 lần LUT và Fmax thấp hơn 3,2 lần.

### Thiết kế
- Mỗi chu kỳ: hai LFSR 32 bit (cùng đa thức với F3, hạt giống 0x12345678 / 0x9ABCDEF0) sinh a, b;
  tính `dot = Σ_{i=0..3} $signed(a[8i+7:8i]) * $signed(b[8i+7:8i])`; `acc <= acc + dot` (32 bit, quấn).
  Chạy đúng 2^20 = 1.048.576 chu kỳ (≈38,8 ms @27 MHz) rồi cứ 1 giây in 8 dòng.
- `scripts/gen_f4_expect.py` tính giá trị kỳ vọng: **ACC = FEF834C3**, LFSR cuối a=BC64D7E9, b=C8B82DCC,
  dot nằm trong khoảng −52213..49098 (biên lý thuyết ±65536).
- **Bốn biến thể dùng CHUNG một `top.v`**, khác nhau bằng cờ build (nên so sánh được công bằng):
  | nhãn | cách dựng |
  |---|---|
  | DSP | `synth_gowin` (mặc định) — yosys tự ánh xạ phép nhân vào DSP |
  | D18 | như trên nhưng toán hạng mở rộng dấu lên 18 bit (`-DWIDE_MULT`) |
  | PRM | gọi trực tiếp `MULT18X18`, `ASIGN=BSIGN=0`, toán hạng mở rộng dấu 18 bit (`-DPRIM_MULT`) |
  | LUT | `synth_gowin -nodsp` — "do not infer DSP multipliers" |
- Mô phỏng Icarus chạy **đủ 2^20 chu kỳ**: `F4_SIM_PASS`, acc và cả trạng thái LFSR cuối khớp Python.

### Kết quả trên kit (cả bốn build từ cùng một top.v cuối cùng)
| Biến thể | Cách dựng | LUT4 | DFF | ALU | MULT9X9 | MULT18X18 | DUMMY | Fmax (MHz) | Trên kit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| DSP | yosys suy luận (mul2dsp → MULT9X9) | 771 | 291 | 234 | 4 | 0 | 4 | 225,28 | **SAI** |
| D18 | toán hạng 18 bit (yosys vẫn chọn MULT9X9) | 815 | 291 | 234 | 4 | 0 | 4 | 237,02 | **SAI** |
| **PRM** | **MULT18X18 trực tiếp, không dấu** | **811** | 291 | 234 | 0 | **4** | 16 | **233,64** | **ĐÚNG 3/3** |
| LUT | `-nodsp`, nhân bằng logic | 1764 | 291 | 306 | 0 | 0 | 0 | 73,08 | **ĐÚNG 3/3** |

### Chẩn đoán (trước khi sửa, theo quy tắc 3 "không bịa số")
1. Kit báo `acc = 27959EC3`, Python và Icarus đều cho `FEF834C3`. Quét Python: **không** có số chu kỳ nào
   trong 1..2^21 cho ra giá trị của kit, và **không** có cách hiểu dấu nào (có/không dấu, các kiểu cắt bit,
   mở rộng dấu ở mọi độ rộng 8..18) khớp cả bốn giá trị dot đầu — nên không phải lỗi quy ước dấu đơn giản.
2. Thêm 8 dòng chẩn đoán vào thiết kế: trạng thái LFSR cuối, 4 giá trị `dot` đầu, rồi **từng tích riêng**.
   - **LFSR cuối ĐÚNG** (a=BC64D7E9, b=C8B82DCC) → LFSR và số chu kỳ không sai.
   - **Từng tích SAI**, và **8 bit thấp của mỗi tích luôn đúng**:
     | lane | toán hạng | kỳ vọng | kit |
     |---|---|---|---|
     | P00 | 120 × −16 | −1920 (F880) | −6016 (E880) |
     | P01 | 86 × −34 | −2924 (F494) | −24428 (A094) |
     | P02 | 52 × −68 | −3536 (F230) | +23088 (5A30) |
     | P03 | 18 × −102 | −1836 (F8D4) | +7380 (1CD4) |
   - Cùng RTL đó với `-nodsp` thì **đúng** → lỗi ở đường suy luận/ánh xạ DSP, không ở RTL của tôi.

### Ba hướng sửa đã thử (quy tắc 2)
1. **Mở rộng dấu toán hạng lên 18 bit** để yosys chọn MULT18X18 → **thất bại**: `wreduce` của yosys rút
   lại toán hạng về 8 bit, report vẫn cho `MULT9X9 = 4`, kết quả sai y hệt (`27959EC3`, `D00 = 00000018`).
2. **Gọi trực tiếp primitive `MULT18X18`**, `ASIGN=BSIGN=0` (không dấu), toán hạng int8 mở rộng dấu lên
   18 bit, các tham số `AREG=BREG=OUT_REG=PIPE_REG=0` (tổ hợp) → **THÀNH CÔNG**, acc = FEF834C3, 3/3 lần.
   Lý do đúng mà không cần đường cờ dấu của DSP: với x' = x mod 2^18, y' = y mod 2^18 thì
   x'·y' ≡ x·y (mod 2^18), và |x·y| ≤ 128·128 = 16384 < 2^17, nên `DOUT[17:0]` đọc như số có dấu 18 bit
   chính là x·y. Giao diện primitive lấy từ `YosysHQ/apicula` `examples/dsp-mult18x18.v` — ví dụ mà
   Apicula tự kiểm thử trên kit thật (đích `hil-dsp-mult18x18-tangnano20k` trong examples/Makefile).
3. Hướng 3 (phương án dự phòng của kế hoạch: dùng biến thể LUT) **không cần dùng tới**, nhưng vẫn đã
   kiểm và nó đúng — giữ làm đường lùi.

### Ý nghĩa cho các cổng sau
- **F8 (DOT4 qua PCPI) nên dùng cách PRM**: tiết kiệm **953 LUT4** (811 so với 1764) và Fmax **cao hơn
  3,2 lần** (233,64 so với 73,08 MHz) so với nhân bằng logic.
- Nếu về sau có chỗ nào để yosys tự suy luận phép nhân thì **phải kiểm lại trên kit**, không tin mô phỏng:
  mô phỏng Icarus đúng trong khi phần cứng sai, vì Icarus không mô phỏng khối DSP thật.
- `MULT18X18` trong thư viện của yosys là **blackbox không có mô hình mô phỏng** → biến thể PRM chỉ kiểm
  được trên kit, không mô phỏng được. Khi dùng ở F8 cần giữ cả đường LUT để mô phỏng đối chiếu.

### Lỗi nhỏ của chính tôi, đã sửa
- `f4_check.py` dùng regex nhãn `[A-Z]{3}` nên không nhận nhãn `D18` (có chữ số) → đổi thành `[A-Z0-9]{3}`.
- Lệnh `ls -l | awk` trong Makefile bị make nuốt dấu `$` → thay bằng `wc -c`.

### Việc tiếp theo / cần người dùng
- F5 (SoC PicoRV32 chạy firmware C). Ngân sách tài nguyên sau F3/F4: BSRAM 32/46 cho RAM 64 KB,
  còn 14 khối; MULT18X18 còn 44/48. Không cần người dùng làm gì.
- Kit đang chạy biến thể LUT của F4 (bản nạp cuối cùng trong vòng kiểm).

## 2026-10-17 — Cổng F3 (BSRAM 64 KB có khởi tạo) — ĐẠT, KHÔNG cần phương án dự phòng

**Đây là rủi ro lớn nhất của cả dự án và nó đã được giải quyết.** Luồng mã nguồn mở suy luận được
64 KB BSRAM có nội dung khởi tạo, nạp được nội dung vào bitstream, và kit đọc lại đúng từng bit.

### Thiết kế
- `scripts/gen_pattern.py`: sinh `pattern.hex` = 16.384 từ 32 bit (65.536 byte) từ LFSR Fibonacci 32 bit,
  đa thức x^32+x^22+x^2+x^1+1, hạt giống **0xACE12345**. In CRC32 kỳ vọng (zlib: 0xEDB88320, init
  0xFFFFFFFF, đảo cuối) trên dòng byte **little-endian của từng từ**.
- `feasibility/F3_bsram/top.v`: `reg [31:0] mem [0:16383]` + `initial $readmemh("pattern.hex", mem)`,
  một cổng, **đọc đồng bộ 1 chu kỳ**. Máy trạng thái 3 pha chạy một lần sau khi nạp bitstream:
  (1) đọc toàn bộ → CRC32 → `crc_rom`; (2) ghi `data2(a) = a ^ 0xA5A5A5A5` vào toàn bộ;
  (3) đọc lại toàn bộ → CRC32 → `crc_rw`. Sau đó cứ 1 giây in lại hai dòng
  `F3,ROM,xxxxxxxx` và `F3,RW,xxxxxxxx` (CSV, kết thúc `\r\n`) để host bắt được bất kể lúc nào mở cổng.
- `crc32.v`: hàm CRC32 một byte, bung 8 bước thành mạng XOR tổ hợp → 1 chu kỳ/byte.
  Một lượt đọc hết 64 KB mất 6 chu kỳ/từ × 16.384 ≈ 98.304 chu kỳ ≈ 3,6 ms @27 MHz.
- UART phát: dùng lại khối **đã kiểm chứng ở F2**, đặt tại `rtl/uart/uart_tx.v` (bản sao y nguyên của
  `feasibility/F2_uart/uart_tx.v`, SHA256 giống nhau — xem `rtl/uart/README.md`). Làm vậy để F3, F5–F8
  dùng cùng một khối, tránh phân nhánh; thư mục F2 vẫn giữ bản riêng làm hồ sơ của cổng đó.

### Kết quả
- `make sim` (Icarus, **mô phỏng đủ 16.384 từ, không rút gọn**): `F3_SIM_PASS`.
  Hai dòng giải mã được: `F3,ROM,C7CD86AA` và `F3,RW,D63B5AB4`, khớp đúng CRC Python.
- Tổng hợp: **BSRAM 32/46 (69,6 %)** — đúng như kế hoạch dự đoán (~32/46). **Còn dư 14 khối (30 %)**
  cho các cổng sau. LUT4 865/20736 · DFF 207 · ALU 250 · IOB 8 (clk + TX + 6 LED) · MULT 0.
- **Fmax = 157,36 MHz** @ ràng buộc 27 MHz → ĐẠT (dư ~5,8 lần).
- Bitstream `top.fs` = 7.261.470 byte (không nén).
- **Trên kit**: `scripts/f3_check.py --repeat 3` → **F3_PASS 3/3 lần đọc độc lập**:
  `CRC_ROM=C7CD86AA`, `CRC_RW=D63B5AB4`, cả hai khớp giá trị Python tính lại tại chỗ
  (script không hard-code CRC, nó gọi lại `gen_pattern.py`).
  Log: `results/feasibility/F3/artifacts/f3_check.log`.

### Phép phản chứng (tự thêm, không có trong kế hoạch)
Vì đây là cổng quan trọng nhất, tôi kiểm thêm rằng nội dung đọc được **thật sự đến từ `pattern.hex`**
chứ không phải trùng hợp:
- Sinh lại `pattern.hex` với hạt giống **0x13572468** (CRC ROM kỳ vọng đổi thành **454701B8**,
  CRC RW kỳ vọng **giữ nguyên D63B5AB4** vì mẫu RW không phụ thuộc hạt giống), build lại, nạp lại.
- Kit báo đúng: `F3,ROM,454701B8` (đổi) và `F3,RW,D63B5AB4` (không đổi).
- ⇒ Dữ liệu khởi tạo đi đúng đường `pattern.hex → yosys → gowin_pack → bitstream → BSRAM`.
- Bằng chứng lưu ở `results/feasibility/F3/falsification/`. Sau đó đã khôi phục mẫu chuẩn
  (`sha256 pattern.hex = 86ee138c…`, đối chiếu lại bằng `cmp` với bản sinh lại) và nạp lại bitstream chuẩn.

### Vấn đề gặp phải
1. **Lỗi lệch một ô khi ghi** (bắt được khi đọc lại code trước lúc mô phỏng, chưa kịp gây hậu quả):
   ban đầu để `we`/`wdata` là thanh ghi, nên ở chu kỳ `we` có hiệu lực thì `addr` đã tăng 1 → ghi sai ô.
   Sửa: `we` và `wdata` thành **tổ hợp** theo `st` và `addr` hiện tại.
2. **Dữ liệu tồn trong bộ đệm driver khi đổi bitstream**: lần đọc đầu sau khi nạp bitstream mới vẫn trả
   về dòng của bitstream **cũ** (đã thấy cả với dòng `F2 OK ...` lẫn `F3,ROM,C7CD86AA` cũ).
   `reset_input_buffer()` của pyserial không đủ. Sửa: `f3_check.py` **đọc bỏ 1,5 s** trước khi thu
   (tham số `--drain`). Sau khi sửa: 3/3 lần đọc đạt. Ghi nhận cho các cổng sau: **mọi script đọc UART
   sau khi nạp bitstream mới phải xả bộ đệm trước.**
3. Cảnh báo của yosys: 128 cảnh báo, chỉ 4 thông điệp khác nhau, tất cả phát sinh trong file techmap
   của chính yosys (`share/yosys/gowin/brams_map.v:114`, dạng `Range select [34:27] out of bounds on
   signal PORT_A_WR_DATA`), xuất hiện 32 lần = một lần mỗi khối BSRAM. Đó là các lane bit chẵn lẻ thứ 9
   mà thiết kế 32 bit không dùng. **Không gây hậu quả**: pha RW (ghi rồi đọc lại toàn bộ 64 KB) cho CRC
   đúng từng bit, tức đường ghi 32 bit hoàn toàn nguyên vẹn.

### Nguồn đã đối chiếu
- Chân cắm: đã đối chiếu ở F1, không làm lại.
- Khả năng khởi tạo BSRAM của luồng: `YosysHQ/apicula` có sẵn các ví dụ `bsram-pROM-tangnano20k`,
  `bsram-SP-tangnano20k`, `bsram-SDPB`, `bsram-DPB` trong `examples/Makefile` (đã xem ở F1) → luồng
  được thiết kế để làm việc này. Ở đây ta dùng cách **để yosys tự suy luận** từ `$readmemh`
  (phương án chính của kế hoạch), nên không cần tới phương án dự phòng (b) là gọi primitive SP/SDPB
  trực tiếp.

### Việc tiếp theo / cần người dùng
- F4 (khối nhân DSP): hai biến thể DSP và LUT, so với giá trị Python, ghi LUT/FF/MULT/Fmax từng biến thể.
  Chip có sẵn MULT18X18 48, MULT9X9 96 (số từ report.json của F1). Không cần người dùng làm gì.
- Kit đang chạy bitstream F3 chuẩn, mỗi giây in hai dòng CRC.

## 2026-10-17 — Cổng F2 (UART hai chiều) — ĐẠT

- **Làm gì**: viết UART TX/RX 8N1 tự chia nhịp, testbench Icarus, build, nạp SRAM, kiểm 10.240 byte echo
  qua cổng serial thật. Phát sinh hai vấn đề phải chẩn đoán, cả hai đã kết luận bằng số đo.

### Thiết kế
- `uart_tx.v`: thanh ghi dịch 10 bit (start + 8 dữ liệu LSB trước + stop), bộ chia DIV chu kỳ/bit.
  Khoảng nghỉ giữa hai khung = 2 chu kỳ → chu kỳ khung 2.342 chu kỳ, **nhanh hơn** host (2.343,75) nên
  không dồn ứ.
- `uart_rx.v`: máy trạng thái IDLE→START→DATA→STOP, đồng bộ hoá chân vào 2 tầng, **kiểm lại bit start
  ở giữa bit** (chống nhiễu), kiểm bit stop; byte sai bit stop bị bỏ và đếm vào `err_cnt`.
- `top.v`: FIFO 64 byte cho echo (yosys ánh xạ thành 8× RAM16SDP4), trọng tài phát **ưu tiên echo**
  rồi mới tới dòng định kỳ.
- **Sai số baud**: DIV = round(27.000.000/115.200) = **234** → baud thực **115.384,62** (**+0,1603 %**).
  Lệch tích luỹ tới giữa bit stop = 0,0152 bit (ngưỡng an toàn 0,5 bit). Chi tiết: `artifacts/baud_calc.txt`.
- **Cửa sổ im lặng (khác kế hoạch, có chủ ý)**: dòng định kỳ chỉ phát khi đường RX im >125 ms.
  Lý do: nếu dòng thông báo chen vào giữa luồng echo thì phía PC không thể tách byte echo khỏi byte
  thông báo, phép kiểm "10.240 byte không sai byte nào" sẽ mất nghĩa. Nhờ vậy bài kiểm chia hai pha sạch.
- **Dòng định kỳ mang theo chẩn đoán** (thêm vào khi gỡ lỗi, giữ lại vì rất hữu ích):
  `F2 OK dddd rx=hhhh tx=hhhh dr=hhhh er=hh ov=h hw=hh` — số byte thu, số byte phát, số byte bị bỏ vì
  FIFO đầy, số lỗi bit stop, cờ FIFO từng tràn, mức FIFO cao nhất. Vẫn bắt đầu bằng `F2 OK ` như kế hoạch.

### Kết quả
- `make sim` (Icarus): `F2_SIM_PASS` — 3 bài: giải mã đúng dòng định kỳ; echo 300 byte liên tục không sai
  byte nào; dòng định kỳ quay lại sau khi RX im (kiểm cửa sổ QUIET).
- Tổng hợp: **Fmax 187,48 MHz** @ ràng buộc 27 MHz. LUT4 883/20736 · DFF 236/15552 · ALU 386 ·
  IOB 9/384 (clk + TX + RX + 6 LED) · **RAM16SDP4 8/648** (FIFO) · BSRAM 0. Không warning nào từ yosys/nextpnr.
- **Cổng UART của FPGA = `/dev/cu.usbserial-20250303171`** (interface B của FT2232).
  `...170` không trả dữ liệu — đó là interface A, dành cho JTAG. Quy tắc 9 (thử cả hai cổng) đã trả lời.
- `scripts/uart_check.py` — ĐẠT cả ba pha, chạy lại 2/2 lần:
  - Pha 1: nhận dòng `F2 OK 0085 rx=3C00 tx=4DB2 dr=0000 er=00 ov=0 hw=01` sau 0,20 s.
  - Pha 2: **10.240 byte echo khớp 100 %, 0 byte sai**, khối 64 byte, 1,951 s → 5.248 byte/s
    (≈52.485 bit/s; thấp hơn trần 115.200 bit/s vì theo nhịp gửi-rồi-chờ-echo từng khối).
  - Pha 3: bộ đếm trong FPGA **rx tăng đúng 10.240**, `dr=0`, `er=0`, `ov=0`, FIFO cao nhất **1/63**.
  - Log: `results/feasibility/F2/artifacts/uart_check.log` và `uart_check_sweep.log`.

### Vấn đề 1 — bitstream nén không nạp được
- Triệu chứng: `openFPGALoader -b tangnano20k build/top.fs` → `FsParser: checksum data is truncated`,
  `Error: Failed to claim FPGA device: can't parse file`.
- Đã thử: (a) sinh lại file nén hai lần → cùng kích thước 1.130.734 byte, cùng lỗi (tái lập 2/2);
  (b) sinh bản **không nén** (`gowin_pack -d GW2A-18C` không có `-c`) → 4.618.782 byte, **nạp bình thường**.
- Kết luận: `gowin_pack -c` của apycula 0.35.dev5 sinh file mà openFPGALoader v1.1.1 không parse được cho
  thiết kế này (F1 nén lại nạp được → lỗi phụ thuộc thiết kế). **Đã bỏ `-c` khỏi Makefile của mọi cổng.**
- Hệ quả: bitstream F1 cũng được build lại không nén và nạp SRAM 3/3 lần OK
  (`results/feasibility/F1/load_3times_uncompressed.txt`); cùng `pnr.json` với bản nén mà người dùng
  đã xác nhận LED chạy đúng.

### Vấn đề 2 — mất byte khi host ghi khối lớn (lỗi NGOÀI FPGA)
- Triệu chứng ban đầu: với khối 256 byte, echo sai từ offset 32; 10.240 byte chỉ về 833.
- Chẩn đoán (3 hướng, theo quy tắc 2):
  1. **Thêm bộ đếm vào FPGA** rồi đo: FPGA báo `rx` tăng ĐÚNG số byte đã gửi (67/128/256/1024/10240),
     `dr=0` (không bỏ byte vì FIFO đầy), `er=0` (không lỗi bit stop), `ov=0`, mức FIFO cao nhất **1**.
     Với n=67: `tx` tăng 120 = 67 byte echo + 53 byte một dòng thông báo → **FPGA phát đủ cả 67 byte**.
     Kiểm tra nội dung: chỉ thiếu đúng byte thứ 33, các byte khác đúng thứ tự → mất byte, không sai khung.
     ⇒ Lỗi nằm ở cầu USB/driver, không phải ở FPGA.
  2. **Luồng đọc riêng trên host** (ghi 10.240 byte một lần, thread khác đọc liên tục):
     host chỉ nhận 1.151/10.240 → **không cứu được**, nên nguyên nhân không phải host đọc chậm.
  3. **Chia khối ghi**: quét 16/32/64/65/66/67/68/96/128/256 byte →
     **≤66 byte nguyên vẹn, ≥67 byte mất byte**. Với khối 64: 10.240 byte, 0 sai.
- Kết luận: giới hạn của cầu FT2232 + driver macOS khi host `write()` vượt một gói USB (64 byte).
  Luồng đo chốt ở **khối 64 byte**.
- **Ảnh hưởng tới các cổng sau**: kênh thu số đo của dự án là FPGA→PC (dòng CSV) — không bị ảnh hưởng.
  Mọi script gửi dữ liệu PC→FPGA phải chia khối ≤64 byte. Cần ghi nhận: bài kiểm hiện tại chạy theo
  nhịp gửi-chờ nên chỉ đạt ~53 kbit/s; **chưa đo thông lượng FPGA→PC liên tục ở full baud** — việc này
  sẽ tự nhiên được kiểm ở F5–F7 khi firmware in dòng log dài.

### Lỗi của chính tôi, đã sửa
- Lần đầu đặt mốc bộ đếm `rx` cho pha 3 **trước** phần quét ngưỡng, nên pha 3 báo "rx tăng 15360,
  kỳ vọng 10240" (đúng = 10.240 + 5.120 byte của phần quét). Đã sửa: lấy lại mốc ngay trước pha 2.
- `msg_req` ban đầu bị hai `always` block cùng ghi (xung đột driver) → tách thành xung `msg_tick`
  ở block hẹn giờ, còn `msg_req` thuộc block trọng tài.

### Nguồn đã đối chiếu
- Chân cắm: đã đối chiếu ở F1 (`uart_tx`=69, `uart_rx`=70 khớp giữa `uart/src/top.cst` của Sipeed và
  `examples/tangnano20k.cst` của Apicula). Không đối chiếu lại.
- `gowin_pack -h` cho ý nghĩa `-c, --compress`.

### Việc tiếp theo / cần người dùng
- Kit hiện đang chạy lại **F1 blinky** (bản không nén). Nếu anh nhìn thấy 6 LED vẫn đếm nhị phân như cũ
  thì bản không nén cũng đã được xác nhận bằng mắt — chỉ cần nói "LED vẫn chạy", không phải làm gì thêm.
- F3 (BSRAM 64 KB có khởi tạo) — đây là **rủi ro lớn nhất** của cả dự án. Không cần người dùng làm gì
  ngoài giữ kit cắm nguyên.

## 2026-10-17 — Cổng F1 (Blinky bằng luồng mã nguồn mở) — ĐẠT
- **Làm gì**: đối chiếu chân cắm với nguồn chính thức, viết `hw/tangnano20k.cst` và
  `feasibility/F1_blinky/` (top.v, tb_top.v, Makefile), mô phỏng, build, nạp SRAM, nhờ người dùng xem LED.
- **Nguồn đã đối chiếu** (quy tắc 6, làm TRƯỚC lần build đầu):
  - `sipeed/TangNano-20K-example` @ main: `led/blink_leds/src/blink_leds.cst` (clk=4, leds[0..5]=15..20),
    `uart/src/top.cst` (uart_tx=69, uart_rx=70, rst=88), `hdmi/src/hdmi.cst` (I_key=87, I_rst=88),
    `picorv32/src/fpga_project.cst` (ser_tx=69, resetn=88, Part Number GW2AR-LV18QN88C8/I7).
  - `YosysHQ/apicula` @ master, `examples/tangnano20k.cst`: clk=4 + `CLOCK_LOC "clk" BUFG`,
    led[0..5]=15..20, key_i=87, rst_i=88, TXD=69, RXD=70.
  - **Hai nguồn khớp nhau trên mọi chân dự án cần** → mọi giá trị "phải xác minh" trong FEASIBILITY_PLAN
    đều đúng: clock 27 MHz chân 4; LED0–LED5 chân 15–20; UART TX 69 / RX 70; S1 88 / S2 87; LVCMOS33.
  - LED **tích cực mức thấp**: xác nhận bằng `led/blink_leds/src/blink_leds.v` của Sipeed —
    dòng cuối là `assign leds = ~leds_value;`.
  - `YosysHQ/apicula` @ master, `examples/Makefile` — tham số luồng:
    `synth_gowin -json $@ -family gw2a -setundef`;
    `nextpnr-himbaechel --json $< --write $@ --device GW2AR-LV18QN88C8/I7 --vopt family=GW2A-18C --vopt cst=...`;
    `gowin_pack -c -d GW2A-18C -o $@ $<`.
- **Hai khác biệt so với Makefile phác trong kế hoạch** (đều lấy từ nguồn chính thức, không đoán):
  1. **`synth_gowin -family gw2a` là BẮT BUỘC** — `help synth_gowin` nói mặc định là `gw1n`.
     Thiếu cờ này thì tổng hợp cho sai họ chip.
  2. `gowin_pack -c` (`--compress`) — dùng theo examples/Makefile của Apicula (đó cũng là tham số
     họ chạy trong các bài kiểm thử trên kit thật). Không bắt buộc, nhưng theo nguồn cho chắc.
  Cố ý **không** dùng `--timing-allow-fail` (Apicula đặt mặc định cờ này) vì dự án cần biết timing
  thật có đạt 27 MHz hay không.
- **Thiết kế**: bộ đếm nhị phân 6 bit, tăng mỗi `TICK_DIV = 13_500_000` chu kỳ = 0,5 s @27 MHz
  → LED0 nháy 1 Hz, LED5 đổi mỗi 16 s, một vòng 32 s. `assign led = ~cnt` (tích cực mức thấp).
- **Kết quả / output quan trọng**:
  - `make sim` (Icarus 14.0): `F1_SIM_PASS: bo dem 6 bit tang dung nhip, dau ra LED dao dung`
    (testbench chạy 70 lần tăng, quá một vòng 64, với TICK_DIV=10).
  - `make build`: yosys + nextpnr + gowin_pack chạy sạch, **không có warning/error** trong nextpnr.log.
  - **Fmax = 347,58 MHz** cho `clk_IBUF_I_O`, ràng buộc 27 MHz → PASS (dư ~12,9 lần).
  - Tài nguyên: LUT4 30/20736 · DFF 30/15552 · ALU 34/15552 · MUX2_LUT5 2 · IOB **7**/384
    (6 LED + 1 clk, đúng số chân mong đợi) · BUFG 1/24 · BSRAM 0/46.
  - Bitstream `build/top.fs` = **730.982 byte**.
  - Ràng buộc chân có hiệu lực: trong `pnr.json` cả 7 IOB và BUFG đều có
    `BEL_STRENGTH = 5` (STRENGTH_LOCKED), tức nextpnr đã khóa vị trí theo .cst chứ không tự đặt.
  - `make load` → `openFPGALoader -b tangnano20k build/top.fs` (KHÔNG có `-f`, chỉ SRAM):
    **3/3 lần đều thành công**, mỗi lần kết thúc bằng `DONE`, exit=0
    (log: `results/feasibility/F1/load_3times.txt`).
  - **Người dùng xác nhận**: LED chạy đúng pattern và đúng tốc độ (bộ đếm nhị phân, LED0 ~1 Hz).
- **Số liệu phụ thu được cho các cổng sau** (từ report.json, hữu ích để lập ngân sách tài nguyên):
  chip có **BSRAM 46** khối, **MULT18X18 48**, MULT9X9 96, MULT36X36 12, MULTALU18X18 24,
  MULTADDALU18X18 24, ALU54D 24, LUT4 20.736, DFF 15.552, rPLL 2, RAM16SDP4 648.
  → F3 kỳ vọng dùng ~32/46 BSRAM là hợp lý; F4 có sẵn khối nhân để ánh xạ.
- **Vấn đề, đã thử**: chỉ một lỗi nhỏ của riêng tôi: Makefile ban đầu đặt đích `.PHONY: build` trùng tên
  thư mục `build/` → make báo "Circular build/top-synth.json <- build dependency dropped". Sửa bằng cách
  bỏ rule tạo thư mục và dùng `mkdir -p` trong từng recipe. Không liên quan tới phần cứng hay luồng công cụ.
- **Việc tiếp theo / cần người dùng**:
  - F2 (UART hai chiều): viết UART TX/RX 115200 8N1, mô phỏng, nạp, rồi chạy `scripts/uart_check.py`
    (10.240 byte echo). Chưa biết trong hai cổng `cu.usbserial-2025030317{0,1}` cổng nào là UART của FPGA —
    script sẽ thử cả hai, như quy tắc 9.
  - Không cần người dùng làm gì ở F2 ngoài việc giữ kit cắm nguyên.
- **Bổ sung sau F2**: bitstream của F1 đã được build lại **không nén** (xem mục F2, vấn đề 1) và
  nạp SRAM 3/3 lần OK; số byte bitstream trong báo cáo đổi từ 730.982 (nén) sang 4.618.782 (không nén).

## 2026-10-17 — Cổng F0 (Môi trường trên Mac) — ĐẠT
- **Làm gì**: dựng toàn bộ môi trường công cụ mã nguồn mở trên máy Mac, `git init`, xác nhận kit được nhận.
- **Máy**: `uname -m` = x86_64 (Intel), macOS 26.6.2 build 25G83 → tải bản **darwin-x64** (không phải arm64).
- **Kết quả / lệnh / output quan trọng**:
  - OSS CAD Suite `2026-10-16` (`oss-cad-suite-darwin-x64-20261016.tgz`) → `~/tools/oss-cad-suite`.
    Gỡ quarantine bằng `./activate` theo README của gói ("Removing quarantine flag from all files and directories... Done").
  - Phiên bản (log: `results/feasibility/F0/tool_versions.txt`): yosys 0.70+145 (a31d95ea0) ·
    nextpnr-himbaechel 0.11.1-63-g44a6c739 · openFPGALoader v1.1.1 · verilator 5.053 devel · iverilog 14.0 devel ·
    `gowin_pack` có sẵn trong gói (apycula 0.35.dev5+g2db53c01c) → **không cần** `pip install apycula`.
  - `nextpnr-himbaechel --list-uarch` → `gatemate, gowin`. Với `--device GW2AR-LV18QN88C8/I7` nó in
    "Using uarch 'gowin' for device 'GW2AR-LV18QN88C8/I7'" → **chuỗi device trong kế hoạch là đúng**.
    `--vopt help` liệt kê `family=`, `cst=`, `ireg_in_iob`, ... đúng như Makefile dự kiến ở F1.
    Có `share/nextpnr/himbaechel/gowin/chipdb-GW2A-18C.bin` → family `GW2A-18C` dùng được.
    (Log: `results/feasibility/F0/uarch_and_synth.txt`, gồm cả `yosys -p 'help synth_gowin'`.)
  - `yosys help synth_gowin`: **CÓ** tùy chọn `-family <gw1n|gw2a|gw5a>`, **mặc định là `gw1n`**.
    (Ghi chú sửa lỗi: trong lần ghi đầu tiên của mục F0 tôi kết luận sai là "không có tùy chọn họ chip"
    vì đã đọc thiếu phần cuối của `help synth_gowin`. Đã kiểm lại: tùy chọn tồn tại và **bắt buộc**
    phải truyền `-family gw2a` cho GW2AR-18, đúng như examples/Makefile của Apicula.)
  - riscv-none-elf-gcc **15.2.0** (xPack v15.2.0-1, darwin-x64) → `~/tools/xpack-riscv-none-elf-gcc-15.2.0-1`.
    Biên dịch thử `-march=rv32im -mabi=ilp32 -O2`: sinh đúng `mul a0,a0,a1` → nhánh M hoạt động
    (log: `results/feasibility/F0/gcc_test.txt`).
  - `.venv` (python 3.14.7) + numpy 2.5.4 + pyserial 3.5.
  - `env/setup_env.sh`: export PATH cho 3 bộ công cụ + biến dùng chung `TN20K_DEVICE/FAMILY/BOARD/FREQ/CST`.
  - **Kit được nhận**: `openFPGALoader --detect -b tangnano20k` → `idcode 0x81b`, Gowin, family GW2A,
    model **GW2A(R)-18(C)**, irlength 8. `--scan-usb` → `0403:6010 FTDI2232 SIPEED "USB Debugger" serial 2025030317`.
    (Log: `results/feasibility/F0/openfpgaloader_detect.txt`.)
  - **Cổng serial**: `/dev/cu.usbserial-20250303170` và `/dev/cu.usbserial-20250303171` (cùng VID:PID 0403:6010,
    hai interface của FT2232). Cả hai mở được @115200, chưa có dữ liệu (đúng, vì FPGA chưa có bitstream).
    (Log: `results/feasibility/F0/serial_ports.txt`.)
  - `git init` xong, `.gitignore` loại `.venv/`, `build/`, `obj_dir/`, `*.fs`, tarball công cụ.
- **Nguồn đã đối chiếu**:
  - README trong gói OSS CAD Suite (`~/tools/oss-cad-suite/README`) — cách gỡ quarantine trên macOS bằng `./activate`.
  - `nextpnr-himbaechel --help`, `--list-uarch`, `--vopt help` (nguồn chính thức của công cụ, thay cho đoán tham số).
  - `yosys -p 'help synth_gowin'`.
  - Chưa đối chiếu chân cắm với repo ví dụ của Sipeed, và chưa đối chiếu Makefile với `examples/himbaechel/`
    của Apicula — **việc này thuộc F1, làm trước lần build đầu** (quy tắc 6 trong CLAUDE.md).
- **Vấn đề, đã thử**: không có lỗi nào phải xử lý. Ghi nhận khác biệt so với kế hoạch:
  máy là **Intel x86_64**, không phải arm64; `gowin_pack` đã có trong gói nên bỏ bước `pip install apycula`.
  Phần cứng USB báo FTDI FT2232 (`0403:6010`) chứ không phải BL616 như CLAUDE.md ghi — không ảnh hưởng,
  JTAG và UART vẫn hiện thành hai cổng `cu.usbserial-*` như mong đợi.
- **Việc tiếp theo / cần người dùng**:
  - F1 (Blinky): đối chiếu `.cst` với ví dụ chính thức của Sipeed, build bằng yosys/nextpnr/gowin_pack,
    nạp SRAM, rồi **cần người dùng xác nhận LED có chạy và chạy đúng tốc độ**.
  - Kit đang cắm và nhận được — giữ nguyên dây/cổng USB này.
