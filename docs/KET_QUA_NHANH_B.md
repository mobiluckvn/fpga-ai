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

## 4. B2–B3: M1-S trên kit — ĐẠT

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
| B6 | 100 ảnh đúng từng bit + tổng kết RQ3 | chưa làm |

### Số đo còn thiếu trong CSV
`m1s_b.csv` hiện có 40 dòng (4 biến thể × 10 ảnh): `bv1dc`, `bv1d`, `bv2`, `bv0r`.
Thiếu `bv0`, `bv1` (đã đo xong, số đã dùng trong mục 4; **mất dữ liệu thô** vì một lỗi trong
`branch_b_measure.sh` — biến thể đo đầu tiên ghi CSV mới nên xoá các dòng trước đó; đã sửa để script
luôn đo đủ cả bảy biến thể trong một lượt) và `bv1r` (chỉ đạt **1/2** lần đọc vì UART chết đúng lúc
đó → **không ghi nhận**, đã xoá 10 dòng đã lọt vào CSV; tiêu chí của dự án là 2/2).

Vật phẩm: `results/branch_b/` (B0, B1, B3, `m1s_b.csv` 20 dòng) · mã nguồn `rtl/mycore/`.
