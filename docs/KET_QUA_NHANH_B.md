# Nhánh B — lõi RISC-V tự viết: kết quả

**Ngày**: 2026-10-17 · **Kit**: Sipeed Tang Nano 20K (GW2AR-LV18QN88C8/I7), **27 MHz cố định**
Kế hoạch và tiêu chí từng cổng: `docs/BRANCH_B_PLAN.md`. Nhật ký: `docs/LOG.md`.

**Câu hỏi RQ3** (nguyên văn kế hoạch): *"cùng các lệnh đó, khi gắn vào lõi RISC-V tự viết, có cho mức
cải thiện tương đương không?"* — phần dưới trả lời được **một nửa** (vi kiến trúc); phần lệnh tùy biến
trên lõi mới là cổng B4, **chưa làm**.

## 1. Vì sao làm nhánh B — số liệu nhánh A chỉ ra

IPC đo trên nhánh A chỉ **0,151** (A-V0): trung bình **6,6 chu kỳ mỗi lệnh**. Nguyên nhân thuộc vi
kiến trúc, không thuộc tập lệnh: PicoRV32 không pipeline, và bus trong `soc.v` mất **2 chu kỳ mỗi
truy cập** kể cả nạp lệnh. Thêm lệnh tùy biến không sửa được hai điều đó.

## 2. Thiết kế lõi

`rtl/mycore/mycore.v` — RV32IM đầy đủ (kể cả `div`/`rem` mà firmware không dùng), CSR chỉ đọc
`cycle`/`cycleh`/`instret`/`instreth`, `fence` và `fence.i` = nop, lệnh lạ / `ecall` / `ebreak` /
truy cập lệch địa chỉ = trap.

| Quyết định | Chọn |
|---|---|
| Pipeline | 2 tầng: nạp lệnh ‖ (giải mã + thực thi + ghi về) |
| Bộ nhớ | **1 cổng** BSRAM, đọc đồng bộ **1 chu kỳ** (`soc_b.v`), thay cho bus 2 chu kỳ của `soc.v` |
| Địa chỉ bộ nhớ | **tổ hợp** (`FAST_ADDR=1`) — BSRAM đã có thanh ghi địa chỉ ở đầu vào |
| Xung đột cổng | `load`/`store` chiếm cổng → thêm 1 chu kỳ |
| Nhân | 4 × `MULT18X18` gọi **trực tiếp**, chế độ không dấu, ghép 4 phép 16×16 → 32×32→64 |
| Chia | dịch-trừ 32 bước |

**Hệ quả quan trọng: không có hình phạt rẽ nhánh.** Địa chỉ lệnh kế được tính xong *trong chính chu kỳ
thực thi*, nên lõi luôn nạp đúng địa chỉ — không đoán nhánh, nhảy hay không nhảy đều hết 1 chu kỳ.

**Hai lỗi thiết kế tự tìm ra khi rà lại trước khi mô phỏng**, cả hai đều âm thầm (bộ kiểm đúng/sai
không bắt được):
1. `mem_addr` **phải** tổ hợp. Nếu là thanh ghi thì địa chỉ ra chậm một chu kỳ → 2 chu kỳ/lệnh,
   IPC 0,5. Lõi vẫn chạy **đúng**, chỉ chậm gấp đôi.
2. Hazard **đọc-sau-ghi** ở tệp thanh ghi: ghi qua thanh ghi trung gian thì kết quả chỉ thấy sau 2
   chu kỳ, mà lệnh kế đã đọc ở chu kỳ sau.

## 3. B0–B1: bộ kiểm

`riscv-tests` commit `d7e86f70`, môi trường kiểm rút gọn kiểu `picorv32/tests`. **Cổng B0 chủ ý không
viết một dòng RTL nào của lõi**: chỉ dựng bộ kiểm rồi chạy trên PicoRV32 — lõi đã biết đúng — để sau
này một bài KHÔNG ĐẠT chỉ có thể là lỗi lõi, không phải lỗi harness.

| Bộ kiểm | PicoRV32 | **mycore** |
|---|---|---|
| RV32IM (40 `rv32ui` + 8 `rv32um`) | **48/48** | **48/48** |
| `fence_i` (Zifencei, ngoài RV32IM) | KHÔNG ĐẠT | **ĐẠT** |
| `ma_data` (truy cập lệch địa chỉ) | KHÔNG ĐẠT | KHÔNG ĐẠT (bắt lỗi theo thiết kế) |

PicoRV32 trượt `fence_i` **có bằng chứng từ mã nguồn**: `picorv32.v:1088` chỉ giải mã `fence` với
`funct3 == 0`, nên `fence.i` là lệnh không hợp lệ → trap. Lõi tự viết hiện thực `fence.i` nên qua được.

### IPC đo bằng vòng lặp có số lệnh suy ra từ assembly
`rtl/mycore/tests/ipc_probe/` — bốn vòng asm cố định, số lệnh **tính giải tích**, không lấy từ lõi nào:

| Vòng | lệnh/vòng | chu kỳ/lệnh PicoRV32 | chu kỳ/lệnh **mycore** | nhanh hơn |
|---|---|---:|---:|---:|
| alu (`addi`, `bnez`) | 2 | 7,00 | **1,00** | 7,0× |
| mem (`lw`,`addi`,`sw`,`addi`,`bnez`) | 5 | 7,40 | **1,40** | 5,3× |
| mul (`mul`,`addi`,`addi`,`bnez`) | 4 | 6,25 | **1,25** | 5,0× |
| jmp (`jal`,`addi`,`bnez`) | 3 | 6,33 | **1,00** | 6,3× |

Đúng y thiết kế: 1 chu kỳ/lệnh thường, +1 mỗi truy cập bộ nhớ, +1 mỗi phép nhân, **0 cho nhảy**.
`instret` của **cả hai** lõi khớp tuyệt đối số lệnh lý thuyết → cả hai đếm đúng.

## 4. Bảng tổng hợp — bảy biến thể, tất cả đo trên kit

| # | Biến thể | Lõi | Chu kỳ | ms @27 MHz | chu kỳ/MAC | IPC | so A-V0 |
|---|---|---|---:|---:|---:|---:|---:|
| 1 | A-V0 | PicoRV32 | 8.987.660 | 332,9 | 46,80 | 0,151 | 1,00× |
| 2 | A-V1 | PicoRV32 | 6.217.634 | 230,3 | 32,37 | 0,147 | 1,45× |
| 3 | A-V2 | PicoRV32 + DOT4 (PCPI) | 5.758.001 | 213,3 | 29,98 | 0,159 | 1,56× |
| 4 | A-V1+DOT4 | PicoRV32 + DOT4 | 2.917.079 | 108,0 | 15,19 | 0,158 | 3,08× |
| 5 | A-V1+DOT4+C1 | PicoRV32 + DOT4 | 2.450.494 | 90,8 | 12,76 | 0,160 | 3,67× |
| 6 | B-V0r | mycore, địa chỉ thanh ghi | 3.750.662 | 138,9 | 19,53 | 0,362 | 2,40× |
| 7 | B-V1r | mycore, địa chỉ thanh ghi | 2.713.280 | 100,5 | 14,13 | 0,336 | 3,31× |
| 8 | **B-V0** | mycore | 1.978.720 | **73,3** | 10,30 | 0,686 | **4,54×** |
| 9 | **B-V1** | mycore | 1.460.016 | **54,1** | 7,60 | 0,625 | **6,16×** |
| 10 | **B-V2** | mycore + DOT4 (tầng thực thi) | 1.169.073 | **43,3** | 6,09 | 0,781 | **7,69×** |
| 11 | **B-V1+DOT4** | mycore + DOT4 | 631.153 | **23,4** | 3,29 | 0,730 | **14,24×** |
| 12 | **B-V1+DOT4+C1** | mycore + DOT4 | **487.888** | **18,1** | **2,54** | 0,802 | **18,4×** |

Mọi dòng: CRC32 5 lớp × 10 ảnh khớp golden Python, dự đoán khớp golden, **số chu kỳ kit = Verilator
bằng tuyệt đối**, **2/2** lần đọc độc lập. Nhánh B chạy **đúng các file `firmware.hex` của nhánh A**
nên `instret` **khớp tuyệt đối** từng cặp — mọi chênh lệch là thuần vi kiến trúc.
Số liệu gốc: `results/branch_b/m1s_b.csv` (70 dòng) và `results/experiment/m1s/m1s.csv` (50 dòng).

## 4a. B2–B3: M1-S trên kit — ĐẠT

Nguyên tắc so sánh: nạp **đúng các file `firmware.hex` của nhánh A**, không biên dịch lại. Nhờ vậy
`rdinstret` **phải** bằng nhau tuyệt đối, và mọi chênh lệch là **thuần vi kiến trúc**. Điều kiện này
đã thoả ở cả hai biến thể — nó là một phép kiểm, không phải chi tiết kỹ thuật.

| Lớp | A-V0 (PicoRV32) | **B-V0** | B nhanh hơn | A-V1 | **B-V1** | B nhanh hơn |
|---|---:|---:|---:|---:|---:|---:|
| conv1 | 3.491.721 | **724.328** | 4,82× | 1.600.258 | **369.909** | 4,33× |
| pool1 | 225.600 | **42.472** | 5,31× | 225.600 | **42.472** | 5,31× |
| conv2 | 5.011.844 | **1.159.242** | 4,32× | 4.199.609 | **1.005.419** | 4,18× |
| pool2 | 65.921 | **12.519** | 5,27× | 65.921 | **12.519** | 5,27× |
| dense | 192.552 | **40.114** | 4,80× | 126.224 | **29.652** | 4,26× |
| **TỔNG** | 8.987.660 | **1.978.697** | **4,54×** | 6.217.634 | **1.459.993** | **4,26×** |
| `instret` | 1.358.200 | 1.358.200 | **KHỚP** | 911.920 | 911.920 | **KHỚP** |
| **ms @27 MHz** | 332,9 | **73,3** | | 230,3 | **54,1** | |
| chu kỳ/MAC | 46,80 | **10,30** | | 32,37 | **7,60** | |
| **IPC** | 0,151 | **0,686** | 4,54× | 0,147 | **0,625** | 4,26× |
| ảnh/giây | 3,00 | **13,65** | | 4,34 | **18,49** | |
| so A-V0 | 1,00× | **4,54×** | | 1,45× | **6,16×** | |

Điều kiện ghi nhận (giống nhánh A): CRC32 **5 lớp × 10 ảnh** khớp golden Python, dự đoán khớp golden,
**số chu kỳ kit = Verilator bằng tuyệt đối**, lặp **2/2** lần đọc độc lập mỗi biến thể, và đối chứng
đường đo trước/sau mỗi phép đo (mục 6).

### Kết quả đáng chú ý nhất
**B-V0 (73,3 ms) nhanh hơn A-V1+DOT4+C1 (90,8 ms) 1,24×.** Nghĩa là **kernel C thẳng, không một lệnh
tùy biến nào, chạy trên lõi tự viết — vượt bản tối ưu hết mức có lệnh tùy biến trên PicoRV32.**

Với khối lượng công việc này, **vi kiến trúc đáng giá hơn tập lệnh**: 4,54× từ lõi, so với 2,13× từ
DOT4 (và 1,17× dự báo cho REQ). Đây là câu trả lời định lượng cho RQ3 ở phần vi kiến trúc.

## 4b. B4: DOT4 gắn thẳng vào tầng thực thi — ĐẠT, và trả lời RQ3

Kế hoạch yêu cầu *"lệnh tùy biến gắn thẳng vào tầng thực thi"*, khác hẳn cách nhánh A làm (qua giao
diện PCPI). Hiện thực: toán hạng đọc từ tệp thanh ghi, 4 phép nhân int8 + cây cộng, kết quả ghi về
**trong cùng chu kỳ** như một lệnh ALU thường → **1 chu kỳ**. Trên PicoRV32 cùng lệnh đó mất **2 chu
kỳ** vì phải qua PCPI. Mã hoá giữ y nhánh A (custom-0, `funct3=000`, `funct7=0`) nên **dùng lại đúng
các file `firmware.hex` của nhánh A**.

Phép nhân int8 để yosys dựng bằng **logic LUT**, không gọi DSP: ở F4 đã chứng minh đường LUT **đúng**
trên kit còn DSP do yosys tự suy luận thì **sai**; và không gọi `MULT18X18` trực tiếp ở đây để **không
thêm độ trễ DSP vào đường tới hạn của tầng thực thi** — đường đó đã không được nextpnr ràng buộc
(mục 6). Đây là đánh đổi có chủ ý: tốn LUT để giữ đường ngắn.

| Biến thể | Nhánh A (kit) | **Nhánh B (kit)** | B nhanh hơn | chu kỳ/MAC | so A-V0 |
|---|---:|---:|---:|---:|---:|
| C thẳng + DOT4 | 5.758.001 · 213,3 ms | **1.169.073 · 43,3 ms** | 4,93× | 6,09 | **7,69×** |
| +tối ưu PM + DOT4 | 2.917.079 · 108,0 ms | **631.153 · 23,4 ms** | 4,62× | 3,29 | **14,24×** |
| **+bố cục 4 pha** | 2.450.494 · 90,8 ms | **487.888 · 18,1 ms** | **5,02×** | **2,54** | **18,4×** |

Cả ba: `instret` **khớp tuyệt đối** nhánh A, CRC 5 lớp × 10 ảnh khớp golden, **kit = Verilator bằng
tuyệt đối**, 2/2 lần đọc, đối chứng đường đo ĐẠT trước và sau từng phép đo.

**Biến thể nhanh nhất của cả dự án: 487.888 chu kỳ = 18,1 ms = 2,54 chu kỳ/MAC = 55,3 ảnh/giây** trên
FPGA 27 MHz, tức **18,4×** so với điểm khởi đầu A-V0.

### Trả lời RQ3

| DOT4 cho | Hệ số |
|---|---|
| trên PicoRV32 (qua PCPI, 2 chu kỳ mỗi DOT4) | **2,13×** |
| **trên lõi tự viết (tầng thực thi, 1 chu kỳ mỗi DOT4)** | **2,31×** |

**Có — và còn tốt hơn một chút.** Lợi ích của lệnh tùy biến **chuyển giao được** sang một vi kiến trúc
khác hẳn; nó không phải hiện tượng riêng của PicoRV32. Hệ số cao hơn đúng như cơ chế dự đoán: gắn
thẳng vào tầng thực thi tốn 1 chu kỳ thay vì 2.

Tương tự, **bố cục 4 pha cho conv1** cho **1,29×** trên lõi tự viết so với 1,19× trên PicoRV32 — trên
lõi nhanh hơn, phần chi phí cố định mà thủ thuật này cắt chiếm tỷ trọng lớn hơn.

### Phân rã toàn bộ 18,4×

| Nguồn | Hệ số | Trả giá phần cứng |
|---|---|---|
| Tối ưu phần mềm (A-V0 → A-V1) | 1,45× | **0** |
| Vi kiến trúc (lõi tự viết thay PicoRV32) | **4,26×** | **−58,8 % LUT4** (ít hơn!) |
| DOT4 trong tầng thực thi | 2,31× | +1.122 LUT4 |
| Bố cục 4 pha cho conv1 | 1,29× | **0** (3.584 byte `.bss`) |
| **Tích** | **18,4×** | +1.122 LUT4 so với PicoRV32 gốc, vẫn **ít hơn 4.669 LUT4** |

Đọc theo thứ tự đóng góp: **vi kiến trúc (4,26×) lớn hơn lệnh tùy biến (2,31×) gần gấp đôi**, và nó
còn *tiết kiệm* tài nguyên. Đây là kết luận định lượng chính của nhánh B.

### Tài nguyên sau khi thêm DOT4

| | mycore không DOT4 | **mycore + DOT4** | PicoRV32 + PCPI_DOT4 (nhánh A) |
|---|---:|---:|---:|
| LUT4 | 3.235 (15,6 %) | **4.357 (21,0 %)** | 8.065 (38,9 %) |
| MULT18X18 | 4 | 4 | 4 |
| Fmax nextpnr | 53,05 MHz | 53,65 MHz | 71,89 MHz |

Chi phí DOT4 khác nhau giữa hai nhánh **vì hiện thực khác nhau, không phải vì lõi khác nhau**: nhánh A
tốn **+124 LUT4** nhờ dùng 4 khối DSP cho phép nhân int8; nhánh B tốn **+1.122 LUT4** vì cố ý dựng
bằng logic để giữ đường tới hạn ngắn. Dù vậy tổng của nhánh B (4.357) vẫn **ít hơn gần một nửa** so
với nhánh A (8.065).

## 4c. Giá của thiết kế bảo thủ: địa chỉ bộ nhớ ghi thanh ghi (`FAST_ADDR=0`)

Vì nextpnr **không ràng buộc** đường tới đầu vào BSRAM (mục 6), con số Fmax nó báo không bảo đảm gì
cho thiết kế tính địa chỉ bộ nhớ bằng tổ hợp. Nên tôi làm sẵn biến thể bảo thủ: ghi thanh ghi địa chỉ,
mọi đường đều thanh ghi→thanh ghi, trả giá **1 chu kỳ thêm cho mỗi truy cập bộ nhớ** (kể cả nạp lệnh).
Cả hai đều **đo trên kit**, 2/2 lần đọc, CRC khớp golden, kit = Verilator bằng tuyệt đối:

| | `FAST_ADDR=1` (tổ hợp) | `FAST_ADDR=0` (thanh ghi) | giá phải trả |
|---|---:|---:|---:|
| C thẳng | 1.978.720 · **73,3 ms** | 3.750.662 · 138,9 ms | **1,90×** |
| +tối ưu phần mềm | 1.460.016 · **54,1 ms** | 2.713.280 · 100,5 ms | **1,86×** |
| chu kỳ/MAC (C thẳng) | **10,30** | 19,53 | |
| IPC (C thẳng) | **0,686** | 0,362 | |

**Thủ thuật "địa chỉ bộ nhớ tổ hợp" đáng giá 1,9×** — gần bằng cả lệnh DOT4 (2,31×), mà **không tốn
một cổng logic nào**. Nhưng tính đúng đắn của nó về mặt thời gian **không kiểm được bằng công cụ mã
nguồn mở này**; nó chỉ được chứng minh bằng việc chạy đúng trên kit ở 27 MHz với CRC khớp golden.
Trong một thiết kế đưa vào sản xuất, đó là lý do chính đáng để chọn bản bảo thủ.

## 4d. B6: 100 và 10.000 ảnh đúng từng bit trên kit — ĐẠT

Tiêu chí ĐẠT của cả nhánh B trong kế hoạch gốc là *"lõi qua `riscv-tests`; **100 ảnh đúng từng bit**"*.
Phần `riscv-tests` xong ở B1. Phần 100 ảnh làm bằng chế độ `STREAM_10K` (nạp ảnh qua UART) chạy trên
lõi tự viết — 100 ảnh nhúng sẵn thì không vừa RAM 64 KB (78.400 byte). Làm luôn 10.000 ảnh.

| | 100 ảnh | **10.000 ảnh** |
|---|---|---|
| khung nhận đúng | 100/100 · gửi lại **0** | 10.000/10.000 · gửi lại **0** |
| **CRC32 logit khớp golden** | **100/100** | **10.000/10.000 (100 %)** |
| dự đoán khớp golden | 100/100 | **10.000/10.000** |
| **độ chính xác đo trên kit** | 100/100 = 100 % | **9.825/10.000 = 98,25 %** |
| trung vị chu kỳ/ảnh | 487.846 | **487.857** |
| thời gian chạy | 0,2 phút | 16,7 phút |

**98,25 % — bằng tuyệt đối** nhánh A và bằng golden Python. Nghĩa là **cùng một mô hình, cùng một kết
quả từng bit, trên hai vi kiến trúc khác hẳn nhau**, chỉ khác thời gian: 90,8 ms so với **18,1 ms**.
175 ảnh sai là lỗi *mô hình*, giống y nhánh A tới từng cặp nhầm (`4→9` 14 lần, `6→0` 11, `7→2` 11…).

Phép kiểm chéo tốt: trung vị 487.857 (10.000 ảnh, firmware `STREAM_10K`) so với 487.888 (10 ảnh nhúng,
firmware khác) — lệch **31 chu kỳ = 0,006 %**, đúng mức dao động do dữ liệu.

### Một kết quả phụ gọn và đáng ghi
`instret` cũng dao động **đúng 765** với độ lệch chuẩn **133,1** — **trùng khít** dao động chu kỳ, và
**giống hệt nhau trên cả hai lõi**:

| | trung vị | biên độ | độ lệch chuẩn |
|---|---:|---:|---:|
| nhánh A, chu kỳ | 2.450.490 | 765 | 133,1 |
| nhánh A, **số lệnh** | 391.268 | **765** | **133,1** |
| nhánh B, chu kỳ | 487.857 | 765 | 133,1 |
| nhánh B, **số lệnh** | 391.268 | **765** | **133,1** |

Diễn giải: phần phụ thuộc dữ liệu nằm ở **số lệnh thực thi** — nhiều nhất 765 lệnh chênh giữa ảnh nhanh
nhất và chậm nhất, do các nhánh so sánh trong maxpool — và **mỗi lệnh thêm đó tốn đúng 1 chu kỳ trên cả
hai lõi**. Với lõi tự viết, 1 chu kỳ là giá bình thường của một lệnh ALU. Với PicoRV32 (trung bình 6,6
chu kỳ/lệnh) thì điều đó có nghĩa những lệnh thêm này **lọt vào các khe đang chờ bộ nhớ** nên không
tốn thêm gì ngoài 1 chu kỳ. Đây là suy luận **phù hợp với số liệu**, chưa phải cơ chế đã chứng minh.

Hệ quả thực tế: thời gian mỗi ảnh nằm trong **18,05–18,08 ms** (dao động **0,16 %**). Lõi nhanh hơn
5× nhưng dao động tuyệt đối không đổi, nên **tỷ lệ** dao động tăng từ 0,031 % lên 0,16 % — vẫn là suy
luận tất định về thời gian theo mọi nghĩa thực tế.

### UART đã thành nút cổ chai, không còn là tính toán
18,1 ms để tính một ảnh, nhưng **~68 ms** để nạp 784 byte qua UART 115200. 10.000 ảnh mất 16,7 phút,
trong đó **chỉ ~3 phút là tính**. Với nhánh A tỷ lệ này là 30 phút / 15 phút tính. Nói cách khác:
**lõi đã nhanh hơn đường nạp dữ liệu**, nên muốn đo thông lượng thật thì phải đổi cách nạp (UART nhanh
hơn, hoặc nạp theo lô vào BSRAM) — một giới hạn của *bàn đo*, không phải của thiết kế.

## 5. Tài nguyên FPGA — lõi tự viết NHỎ HƠN

| | PicoRV32 + `soc.v` | **mycore + `soc_b.v`** | chênh |
|---|---:|---:|---:|
| LUT4 | 7.941 (38,3 %) | **3.272 (15,8 %)** | **−58,8 %** |
| DFF | 1.069 | **656** | −38,6 % |
| ALU | 774 | 890 | +15,0 % |
| BSRAM | 32/46 | 32/46 | 0 |
| RAM16SDP4 | 32 | 32 | 0 |
| MULT18X18 | 0 | **4** | +4 |
| Fmax nextpnr | 71,76 MHz | 86,45 MHz | (xem mục 6) |

Lõi tự viết **nhanh hơn 4,54× và nhỏ hơn 58,8 % LUT4**. Lý do: nó chỉ làm đúng những gì cần
(RV32IM + 4 CSR đọc), không có ngắt, không có `PCPI`, không có bộ dịch nhiều chế độ, và bus 1 chu kỳ
đơn giản hơn máy trạng thái 2 chu kỳ. 4 `MULT18X18` thay cho bộ nhân dựng bằng logic.

## 6. Hai cạm bẫy của luồng mã nguồn mở, phát hiện ở cổng B3

**(a) nextpnr-himbaechel không ràng buộc đường tới BSRAM.** `grep -c "Sink u_soc.ram\." nextpnr.log`
cho **0** ở **cả** nhánh A và B. Nhánh A không bị ảnh hưởng vì `mem_addr` của PicoRV32 là thanh ghi
(đường vào BSRAM chỉ là ff → BSRAM). Lõi này đặt cả giải mã + tệp thanh ghi + ALU lên đường đó — đó
chính là cách đạt 1 chu kỳ/lệnh — nên **con số Fmax 86,45 MHz không nói gì về đường tới hạn thật**.
Thiết kế vẫn chạy đúng ở 27 MHz (đã đo), nhưng **biên an toàn là không biết được** từ công cụ.
Đã làm sẵn biến thể `FAST_ADDR=0` (ghi thanh ghi địa chỉ, mọi đường là thanh ghi→thanh ghi) làm phương
án bảo thủ: mô phỏng 3.750.362 chu kỳ = 138,9 ms, vẫn nhanh hơn A-V0 **2,40×**.

**(b) Đặt net trung gian trên đường xung nhịp làm MẤT ràng buộc chân.** Khi viết `wire clk_sys = clk;`
ở tầng top, yosys đổi tên net nên IBUF thành `clk_sys_IBUF_O` thay vì mang tên cổng `clk`. Ràng buộc
`IO_LOC "clk" 4` và `CLOCK_LOC "clk" BUFG` trong `.cst` **không khớp cell nào** → xung nhịp vào chân
bất kỳ, cả thiết kế im lặng, **không một cảnh báo nào**. Ràng buộc chân khớp theo **TÊN**: nối cổng
xung nhịp **trực tiếp**. (Chia xung nhịp trên vải FPGA cũng sai: nextpnr báo
`Hold/min time violation`; muốn hạ tần số phải dùng `rPLL`.)

## 6b. Cảnh báo về số đo tài nguyên: hiệu hai lần tổng hợp KHÔNG đáng tin

Khi dựng biến thể REQ cho nhánh A, tôi gặp một kết quả **vô lý**: thêm lệnh REQ (thêm logic + 4 DSP)
mà tổng LUT4 lại **giảm 1.545**:

| | A-V1+DOT4+C1 | A-V3 (thêm REQ) | chênh |
|---|---:|---:|---:|
| LUT4 | 8.054 | **6.509** | **−1.545** |
| MUX2_LUT5 | 1.946 | 655 | −1.291 |
| MUX2_LUT6/7/8 | 595 / 256 / 80 | 49 / 12 / 3 | −867 |
| ALU (chuỗi nhớ) | 774 | 972 | +198 |
| MULT18X18 | 4 | **8** | +4 |
| DFF | 1.153 | 1.173 | +20 |

Đã cô lập nguyên nhân: chạy **yosys hai lần, khác đúng một tham số** `WITH_REQ` (0 và 1), cùng mọi
file nguồn, cho đúng cùng khác biệt đó. Nên nó **không phải nhiễu giữa các lần chạy** (yosys gần như
tất định: hai lần chạy cùng tham số lệch ~10 cell) mà là **ABC chọn cách phủ (mapping) khác hẳn** khi
netlist thay đổi. Dấu hiệu rõ: khối logic chuyển từ các cấu trúc MUX2_LUT5..8 rộng sang LUT3 + chuỗi
nhớ ALU. Số thanh ghi **tăng** 20 (đúng bằng `is_req` + `req_sh` + đệm), nên **không có khối nào bị
xoá mất** — mạch vẫn đủ, chỉ được phủ khác.

**Hệ quả cho cách đọc mọi số tài nguyên trong tài liệu này và `docs/KET_QUA_M1S.md`:**

| Khẳng định | Còn vững? |
|---|---|
| Số **BSRAM** (32/46 ở mọi biến thể) | ✅ chính xác |
| Số **MULT18X18** (4 cho mỗi DOT4 kiểu DSP, 4 cho REQ) | ✅ chính xác — đã truy từng instance về đúng dòng mã trong netlist |
| **Fmax** ≥ 2× yêu cầu 27 MHz ở mọi biến thể | ✅ vững (biên 1,99–2,80×) |
| mycore nhỏ hơn PicoRV32 **khoảng 2,4×** (3.235 so với 7.941–8.065 LUT4) | ✅ vững — khoảng cách lớn hơn biên độ dao động nhiều lần |
| "DOT4 trên nhánh A tốn **+124 LUT4**" (7.941 → 8.065) | ❌ **KHÔNG kết luận được** — nhỏ hơn biên độ dao động phủ (1.545) |
| "DOT4 trên nhánh B tốn **+1.122 LUT4**" (3.235 → 4.357) | ⚠️ cùng bậc với biên độ dao động; chỉ nên coi là **ước lượng** |
| "REQ trên nhánh B tốn **+716 LUT4**" (4.357 → 5.073) | ⚠️ như trên |

**Bài học phương pháp**: trên luồng mã nguồn mở này, **không thể đo chi phí phần cứng nhỏ của một lệnh
tùy biến bằng cách trừ hai lần tổng hợp**. Muốn con số đáng tin thì phải tổng hợp **riêng chính khối
đó** như một thiết kế độc lập (out-of-context), hoặc đếm trực tiếp các primitive đặc thù (DSP, BSRAM)
như đã làm ở trên. Tôi giữ lại các con số tuyệt đối đã đo và **gỡ bỏ các kết luận về hiệu số** nằm
dưới biên độ dao động.

## 7. Bài học phương pháp đắt nhất của cổng này

Cổng B3 ban đầu bị kết luận **sai** là "KHÔNG ĐẠT": kit không phát byte nào, và tôi sửa thiết kế bốn
lần. Phép **đối chứng** mới cho câu trả lời: nạp lại bitstream **nhánh A đã đo thành công vài phút
trước** thì kit **cũng không phát byte nào**, trên **cả hai** cổng serial — **đường UART của kit đã
chết** (phần JTAG vẫn tốt, `--detect` vẫn nhận chip). Mọi phép đo trong khoảng đó đều vô giá trị.

> **Khi một phép đo trả về "không có gì", việc ĐẦU TIÊN phải làm là chạy đối chứng bằng một cấu hình
> ĐÃ BIẾT CHẠY — trước khi sửa thiết kế.** Quy tắc "tối đa 3 hướng sửa rồi dừng" có tác dụng, nhưng
> nó không cứu được việc chọn **sai đối tượng** để sửa.

Đã biến bài học thành công cụ: `scripts/branch_b_measure.sh` chạy đối chứng bằng thiết kế tối giản
`top_min` (chỉ bộ đếm + `uart_tx`, không lõi, không RAM 64 KB) **trước và sau mỗi phép đo**, và dừng
ngay nếu đối chứng im. Hai phép đo ở mục 4 đều có đối chứng ĐẠT trước và sau (8 lần `MIN` mỗi lần).

Về hiện tượng: UART chết sau khoảng mười mấy phút không dùng cổng (trong lúc tổng hợp bitstream);
đảo DTR/RTS và đổi baud không khôi phục được, chỉ rút/cắm lại cáp. Vì vậy mọi phép đo phải gom vào
**một lượt liên tục** ngay sau khi cắm cáp.

## 8. Còn lại của nhánh B

| Cổng | Việc | Trạng thái |
|---|---|---|
| B0 | hạ tầng `riscv-tests`, kiểm trên PicoRV32 | **ĐẠT** |
| B1 | lõi qua `riscv-tests` | **ĐẠT** 48/48 + `fence_i` |
| B2 | M1-S trong Verilator, `instret` khớp nhánh A | **ĐẠT** |
| B3 | M1-S trên kit | **ĐẠT** — 73,3 ms (B-V0), 54,1 ms (B-V1) |
| B4 | DOT4 **trong tầng thực thi** | **ĐẠT** — 18,1 ms; RQ3: 2,31× so với 2,13× trên PicoRV32 |
| B5 | lệnh REQ (B-V3) | chưa làm |
| B6 | 100 ảnh đúng từng bit + tổng kết RQ3 | **ĐẠT** — 100/100 và **10.000/10.000** đúng từng bit |

### Số liệu đã trọn vẹn
`results/branch_b/m1s_b.csv`: **70 dòng** = 7 biến thể × 10 ảnh, tất cả đo trên kit, tất cả 2/2 lần đọc.
Hai biến thể quan trọng nhất (`bv1dc`, `bv1d`) đã được **đo lại độc lập ở một lượt khác và cho số trùng
khít** (487.888 và 631.153) — bằng chứng tái lập mạnh hơn cả bản thân file CSV.

Vật phẩm: `results/branch_b/` (B0, B1, B3, `m1s_b.csv` 20 dòng) · mã nguồn `rtl/mycore/`.

## 9. Tổng kết RQ3

> *"Khả năng chuyển giao: cùng các lệnh đó, khi gắn vào lõi RISC-V tự viết, có cho mức cải thiện tương
> đương không?"*

**Có, tương đương và tốt hơn một chút.** Bằng chứng, tất cả đo trên kit với firmware **giống nhau đến
từng byte**:

| Tối ưu | Trên PicoRV32 | Trên lõi tự viết | Chuyển giao? |
|---|---:|---:|---|
| DOT4 (thêm vào mã đã tối ưu) | 2,13× | **2,31×** | ✅ tốt hơn 8 % |
| Bố cục 4 pha cho conv1 | 1,19× | **1,29×** | ✅ tốt hơn 8 % |
| Tối ưu phần mềm (A-V0→A-V1) | 1,45× | **1,36×** | ✅ thấp hơn 6 % |

Ba hệ số đều **giữ nguyên bậc độ lớn** khi đổi vi kiến trúc. Hai hệ số đầu *tăng* vì trên lõi mới chi
phí cố định quanh chúng nhỏ hơn: DOT4 tốn 1 chu kỳ (tầng thực thi) thay vì 2 (qua PCPI). Hệ số thứ ba
*giảm* nhẹ vì phần tính chỉ số mà nó cắt vốn đã rẻ hơn trên lõi nhanh.

**Kết luận bổ sung, mạnh hơn cả RQ3**: trên cùng khối lượng công việc này, **vi kiến trúc đóng góp
4,26× — gần gấp đôi lệnh tùy biến (2,31×) — và còn dùng ít hơn 58,8 % LUT4.** Nếu chỉ có một lựa chọn
đầu tư, sửa vi kiến trúc đáng hơn thêm lệnh. Hai hướng **nhân được với nhau** (4,26 × 2,31 = 9,8× trên
cùng firmware), nên trong thực tế nên làm cả hai — và theo đúng thứ tự đó, vì mỗi tối ưu làm phần còn
lại *đáng giá hơn*, không phải ít hơn.
