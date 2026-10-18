# Kết quả tổng hợp — TinyML trên lõi RISC-V, Tang Nano 20K

**Ngày**: 2026-10-17 · **Kit**: Sipeed Tang Nano 20K (GW2AR-LV18QN88C8/I7) · **Xung nhịp cố định 27 MHz**
Mô hình: M1-S (CNN int8, MNIST, 192.064 MAC) · Kế hoạch gốc: xem `CLAUDE.md`

Tài liệu này là bảng tổng kết. Chi tiết: `docs/FEASIBILITY_REPORT.md` (F0–F8),
`docs/KET_QUA_M1S.md` (nhánh A), `docs/KET_QUA_NHANH_B.md` (nhánh B), `docs/LOG.md` (nhật ký).

## 1. Mười lăm cấu hình, tất cả đo trên phần cứng thật

| # | Biến thể | Phần cứng | Chu kỳ/ảnh | ms | chu kỳ/MAC | IPC | ảnh/s | so A-V0 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | A-V0 | PicoRV32 | 8.987.660 | 332,9 | 46,80 | 0,151 | 3,0 | 1,00× |
| 2 | A-V1 | PicoRV32 | 6.217.634 | 230,3 | 32,37 | 0,147 | 4,3 | 1,45× |
| 3 | A-V2 | PicoRV32 + DOT4 | 5.758.001 | 213,3 | 29,98 | 0,159 | 4,7 | 1,56× |
| 4 | A-V1+DOT4 | PicoRV32 + DOT4 | 2.917.079 | 108,0 | 15,19 | 0,158 | 9,3 | 3,08× |
| 5 | A-V1+DOT4+C1 | PicoRV32 + DOT4 | 2.450.494 | 90,8 | 12,76 | 0,160 | 11,0 | 3,67× |
| 6 | **A-V3** | PicoRV32 + DOT4 + REQ | 1.842.219 | 68,2 | 9,59 | 0,151 | 14,7 | **4,88×** |
| 7 | B-V0r | mycore (địa chỉ ghi thanh ghi) | 3.750.617 | 138,9 | 19,53 | 0,362 | 7,2 | 2,40× |
| 8 | B-V1r | mycore (địa chỉ ghi thanh ghi) | 2.713.235 | 100,5 | 14,13 | 0,336 | 10,0 | 3,31× |
| 9 | B-V0 | mycore | 1.978.697 | 73,3 | 10,30 | 0,686 | 13,6 | 4,54× |
| 10 | B-V1 | mycore | 1.459.993 | 54,1 | 7,60 | 0,625 | 18,5 | 6,16× |
| 11 | B-V2 | mycore + DOT4 | 1.169.050 | 43,3 | 6,09 | 0,781 | 23,1 | 7,69× |
| 12 | B-V1+DOT4 | mycore + DOT4 | 631.130 | 23,4 | 3,29 | 0,730 | 42,8 | 14,24× |
| 13 | B-V1+DOT4+C1 | mycore + DOT4 | 487.865 | 18,1 | 2,54 | 0,802 | 55,3 | 18,42× |
| 14 | **B-V3** | mycore + DOT4 + REQ | **365.992** | **13,6** | **1,91** | 0,759 | **73,8** | **24,56×** |
| 16 | **B-V4** † | mycore + DOT4 + REQ + PMAX4 + bộ nhớ hai cổng | **243.641** | **9,0** | **1,27** | **0,970** | **110,8** | **36,89×** |

**Từ 332,9 ms xuống 13,6 ms — 24,6× — trên cùng một FPGA, cùng một xung nhịp 27 MHz, cùng một mô
hình, và mọi lớp vẫn đúng từng bit so với golden Python.** 73,8 ảnh/giây. Đó là kết quả của hai
nhánh A và B (dòng 1–14).

† **Dòng 16 đến từ giai đoạn sau**: pipeline đồng thiết kế có AI hỗ trợ (bước S7). Nó đẩy tiếp
xuống **9,0 ms — 36,89× — 110,8 ảnh/giây**, và là ứng viên đầu tiên có **dự báo đúng tuyệt đối**
(mức A: dự báo 243.641, đo 243.641, sai số 0,00 %). Dòng 15 (PMAX4, 317.878 chu kỳ, 28,27×) đã đo
trên kit nhưng chưa thoả đủ tiêu chí trong **một** run — xem mục dưới. Vì B-V4 **bao gồm** PMAX4,
phép đo ĐẠT của dòng 16 đã xác nhận lệnh PMAX4 chạy đúng trên phần cứng thật; chỉ riêng **con số
317.878 của dòng 15** là còn thiếu một run sạch.

### Điều kiện để một dòng được ghi nhận
Mọi dòng đều thoả **tất cả**: CRC32 của **cả 5 tensor trung gian** × 10 ảnh khớp golden Python ·
dự đoán khớp golden · **số chu kỳ trên kit = số chu kỳ trong Verilator, bằng tuyệt đối** · lặp
**2/2** lần đọc độc lập · firmware tự khai báo dấu vân tay nội dung mã nguồn (`SRC_HASH`) và script
kiểm **từ chối** ghi nhận nếu lệch.

Nhánh B chạy **đúng các file `firmware.hex` của nhánh A, không biên dịch lại**, nên `rdinstret` khớp
**tuyệt đối** từng cặp — mọi chênh lệch giữa hai nhánh là **thuần vi kiến trúc**.

### Hai dòng của pipeline đồng thiết kế: một đã vào bảng, một còn thiếu một run sạch

Pipeline đồng thiết kế (S5–S7) đã đề xuất, dự báo, hiện thực và kiểm hai thay đổi phần cứng
tiếp theo. **Dòng 16 (B-V4) đã thoả đủ tiêu chí và đã vào bảng chính** (run
`pipeline/runs/20261018-214712-kit`). **Dòng 15 (PMAX4) chưa** — thiếu đúng một run gộp cả
2/2 lần đọc và chốt `SRC_HASH`.

#### Dòng 15: B-V3+PMAX4 — 317.878 chu kỳ, 28,27× (đã đo trên kit, chưa đủ trong một run)

Lệnh thứ ba (`PMAX4`, lấy max gói 4 làn int8 cho pooling) do pipeline đồng thiết kế S5/S6 đề xuất,
đã hiện thực và **đo trên kit thật**:

| # | Biến thể | Phần cứng | Chu kỳ/ảnh | ms | chu kỳ/MAC | IPC | ảnh/s | so A-V0 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| (15) | B-V3+PMAX4 | mycore + DOT4 + REQ + PMAX4 | 317.878 | 11,8 | 1,66 | 0,743 | 84,9 | 28,27× |

Hai lớp pooling: 54.991 → 6.899 chu kỳ. Giá phần cứng **+148 LUT4** (+3,5 %), Fmax 65,89 → 55,26 MHz
(vẫn ĐẠT ràng buộc 27 MHz). Dự báo ghi **trước** khi viết RTL: 316.695 chu kỳ — **sai số +0,37 %**.

**Vì sao chưa vào bảng trên.** Tiêu chí ghi nhận đòi **đồng thời** 2/2 lần đọc **và** chốt `SRC_HASH`
trong **một** phép đo. Đã có **ba** run, mọi tiêu chí đều có bằng chứng nhưng **rải ra**:

| run | nội dung (CRC, dự đoán, kit=Verilator) | 2/2 lần đọc | chốt `SRC_HASH` |
|---|---|---|---|
| `190740` | ĐẠT | **2/2** | không |
| `190840` | ĐẠT ở lần đọc 1 | 1/2 | **có** |
| `214915` | ĐẠT ở lần đọc 1 | 1/2 | **có** |

Cả ba nạp **cùng một tệp nhị phân giống từng bit**. Hai run sau chết ở lần đọc 2 vì **UART của kit
chết** (đối chứng sau cho 0 byte ở cả hai cổng, JTAG vẫn nạp được).

**Quy luật đã thấy được** (ghi trong `results/pipeline/S6/kit/README.md`): sau mỗi lần cắm lại cáp
USB, kênh UART chịu được khoảng **ba lần truyền dài** (~5–9 KB mỗi lần) rồi chết; chuỗi ngắn không
làm nó chết. Phiên 2026-10-18 kiểm chứng đúng điều này: đo B-V4 **trước** thì B-V4 đạt 2/2 trọn vẹn,
còn PMAX4 đo ngay sau đó chết đúng ở lần đọc 2. **Cách làm từ nay**: mỗi lần cắm lại cáp chỉ đo
**một** cấu hình. Dòng 15 vào bảng chính sau một lần cắm lại cáp mà **PMAX4 được đo trước tiên**.

Chi tiết và log thô: `results/pipeline/S6/kit/README.md`.

#### Dòng 16: B-V4 = + bộ nhớ hai cổng — 243.641 chu kỳ, 36,89× (**đã đo trên kit, ĐẠT đủ tiêu chí**)

Dòng này **đã nằm trong bảng chính ở trên**. Run `pipeline/runs/20261018-214712-kit`:
CRC 5 tensor × 10 ảnh = golden 10/10 · dự đoán khớp golden 10/10 · chu kỳ kit = Verilator
**bằng tuyệt đối từng ảnh** (10/10 ảnh đều 243.641) · **2/2 lần đọc độc lập** · chốt `SRC_HASH`
= `a7dca19c8cec` · 10/10 dòng CSV.

Bộ nhớ hai cổng kiểu Harvard: cổng lệnh riêng nên load/store hết **1 chu kỳ** thay vì 2.
Không sửa một dòng mã phần mềm, không thêm lệnh — chỉ hạ λ. **IPC = 0,970**, gần một lệnh
mỗi chu kỳ (nhánh A trên PicoRV32: 0,151); `conv2` xuống 0,89 chu kỳ/MAC, dưới 1.

**Dự báo mức A ghi trước khi viết RTL: 243.641 chu kỳ. Đo được: 243.641. Sai số 0,00 %** —
phép kiểm K2 của mô hình chi phí. Mức A là đẳng thức chứ không phải ước lượng, vì `n_c` giữ
nguyên từng con số (`instret` giống hệt 236.313).

**Giá phần cứng thì đắt, và mô hình λ không thấy được**: LUT4 4.459 → **15.736** (×3,5;
75,9 % chip), Fmax 59,08 → 53,01 MHz (vẫn ĐẠT 27 MHz), BSRAM không tăng (32 khối).
Truy ra: **+8.724 LUT là của riêng cổng ghi thứ hai** — tệp thanh ghi một cổng ghi được map
vào 32 khối `RAM16SDP4` (RAM phân tán), thêm cổng thứ hai thì không map được nữa. Hiệu quả
diện tích: PMAX4 tốn **9,8** LUT4 cho mỗi 1 % tăng tốc, bộ nhớ hai cổng tốn **370** — chênh
38 lần.

Đã kiểm: **kit = ISS = Verilator bằng tuyệt đối** · CRC 5 tensor × 10 ảnh = golden ·
`instret` giống hệt bản một cổng (236.313) · riscv-tests 48/48 · Fmax ĐẠT · firmware 32 KB trên
lõi một cổng cho đúng 317.878 (nên chênh lệch là thuần vi kiến trúc).

**Một điều cần biết trước khi dùng B-V4 cho mô hình khác**: RAM còn 32 KB, và firmware M1-S đã
chiếm **31.588/32.768 byte = 96,4 %**, chỉ còn **1.180 byte cho ngăn xếp**. Mô hình lớn hơn
(M1-L ở bước S8) gần như chắc chắn **không vừa** — nên B-V4 và mô hình giữ lại có thể xung đột.

Chi tiết và log thô: `results/pipeline/S7/README.md`.

## 2. Phân rã 24,6×: mỗi hướng đóng góp bao nhiêu, trả giá gì

| Hướng | Hệ số | Giá phần cứng | Giá phần mềm |
|---|---|---|---|
| Tối ưu phần mềm (bung vòng, con trỏ chạy, trọng số trong thanh ghi) | **1,45×** | **0** | — |
| **Vi kiến trúc** (lõi tự viết thay PicoRV32) | **4,26×** | **ít LUT4 hơn ~2,4 lần** | 0 |
| Lệnh **DOT4** trong tầng thực thi | **2,31×** | 4 × MULT18X18 | 0 |
| **Bố cục 4 pha** cho conv1 | **1,29×** | **0** | 3.584 byte `.bss` |
| Lệnh **REQ** | **1,33×** | 4 × MULT18X18 | 0 |
| **Tích** | **24,6×** | 8 DSP (của 48) | ~3,6 KB |

**Vi kiến trúc là hướng đóng góp lớn nhất (4,26×) — gần gấp đôi lệnh tùy biến mạnh nhất (2,31×) — và
là hướng duy nhất vừa nhanh hơn vừa RẺ hơn.** Nếu chỉ được chọn một việc, hãy sửa vi kiến trúc.
Nhưng các hướng **nhân được với nhau**, nên trong thực tế làm cả bốn, và theo đúng thứ tự đó.

## 3. Ba câu hỏi nghiên cứu

### RQ1 — baseline và profile từng lớp
Xong. A-V0 = 332,9 ms, 46,80 chu kỳ/MAC, IPC **0,151**. Phân tích từng lớp chỉ ra nút cổ chai dịch
dần: conv2 (C thẳng) → conv1 (sau khi có DOT4) → requantize (sau khi gỡ conv1).
Độ chính xác **98,25 % đo trực tiếp trên kit với đủ 10.000 ảnh**, **10.000/10.000** CRC khớp golden —
trên **cả hai** lõi, cho **cùng kết quả từng bit**.

### RQ2 — lệnh tùy biến có giúp gì, và giúp bao nhiêu
| | trên C thẳng | trên C đã tối ưu |
|---|---|---|
| DOT4 (nhánh A) | 1,56× | **2,13×** |

**Lệnh tùy biến cho lợi ích LỚN HƠN khi phần mềm đã được tối ưu** (gấp 1,37 lần). Hai tối ưu **không
độc lập**, và tương tác **thuận lợi**: ở mã chưa tối ưu, phần lớn chu kỳ là **tính chỉ số** — thứ mà
DOT4 không cắt được. **Hệ quả cho phương pháp co-design: đo một lệnh tùy biến trên mã chưa tối ưu sẽ
ĐÁNH GIÁ THẤP giá trị của nó.**

### RQ3 — khả năng chuyển giao sang lõi tự viết
| Tối ưu | PicoRV32 | mycore | Chuyển giao? |
|---|---:|---:|---|
| DOT4 (trên mã đã tối ưu) | 2,131× | **2,313×** | ✅ tốt hơn 8,5 % |
| Bố cục 4 pha | 1,190× | **1,294×** | ✅ tốt hơn 8,7 % |
| **REQ** | 1,330× | **1,333×** | ✅ **tương đương tới 0,2 %** |

**Có.** Cả ba tối ưu giữ nguyên bậc độ lớn; hai cái đầu *tăng* vì trên lõi mới chi phí cố định quanh
chúng nhỏ hơn (DOT4 tốn 1 chu kỳ ở tầng thực thi thay vì 2 qua PCPI). **REQ chuyển giao gần như chính
xác** — bằng chứng mạnh nhất cho RQ3, vì REQ là khối tính toán thuần, ít phụ thuộc vi kiến trúc.

## 4. Những gì đã kiểm, và những gì KHÔNG kết luận được

| Khẳng định | Mức tin cậy |
|---|---|
| Số chu kỳ từng lớp, từng biến thể | **đo**, kit = Verilator bằng tuyệt đối, 2/2 lần đọc |
| Đúng từng bit: CRC 5 lớp × 10 ảnh, và **10.000/10.000** CRC logit | **đo** trên cả hai lõi |
| Độ chính xác 98,25 % | **đo trên kit**, đủ 10.000 ảnh test |
| `riscv-tests` RV32IM 48/48 + `fence_i` cho lõi tự viết | **đo** (PicoRV32: 48/48, trượt `fence_i`) |
| Số BSRAM (32/46) và số MULT18X18 từng khối | **chính xác** — truy từng instance về dòng mã trong netlist |
| Fmax ≥ 2× yêu cầu 27 MHz ở mọi biến thể | **đo** từ báo cáo nextpnr |
| Chi phí LUT4 **gia tăng** của một lệnh tùy biến | ❌ **không kết luận được** — xem `KET_QUA_NHANH_B.md` mục 6b |
| Fmax của thiết kế tính địa chỉ bộ nhớ bằng tổ hợp | ⚠️ nextpnr **không ràng buộc** đường tới BSRAM |
| Công suất | chưa đo (chưa có thiết bị) |

## 5. Bảy cạm bẫy đáng ghi vào luận văn

1. **DSP do yosys suy luận cho kết quả SAI trên kit** (F4), mô phỏng vẫn đúng. Phải gọi `MULT18X18`
   trực tiếp. Mọi build đều bắt buộc `-nodsp`.
2. **`gowin_pack -c`** sinh bitstream không nạp được ("checksum data is truncated").
3. **`wire clk_sys = clk;` ở tầng top làm MẤT ràng buộc chân** — yosys đổi tên net nên `IO_LOC "clk"`
   không khớp cell nào; thiết kế im lặng hoàn toàn, **không một cảnh báo**. Ràng buộc chân khớp theo TÊN.
4. **nextpnr-himbaechel không ràng buộc đường tới BSRAM** (0 đường kết thúc ở `ram` ở cả hai nhánh),
   nên Fmax báo cáo không nói gì về thiết kế tính địa chỉ bộ nhớ bằng tổ hợp.
5. **Hiệu hai lần tổng hợp không đo được chi phí phần cứng nhỏ**: đổi một tham số làm tổng LUT4 xê
   dịch 1.545 vì ABC chọn cách phủ khác.
6. **Phép đo vi mô cho giới hạn DƯỚI của lợi ích**: `REQ_BENCH` báo 9,56 chu kỳ/requantize, thực tế
   tiết kiệm 16,6 — thấp hơn 1,74 lần, vì vòng lặp vi mô không có áp lực thanh ghi và nạp hằng số.
7. **GCC nội suy hàm làm sai phép so sánh**: để `-O2` nội suy cả 5 lớp vào `main` thì cấp phát thanh
   ghi của conv1 **đổi theo việc conv2 có dùng DOT4 hay không** (3.803.170 so với 4.950.316 chu kỳ)
   dù mã nguồn y hệt. `__attribute__((noinline))` từng lớp là bắt buộc để so sánh công bằng.

## 6. Ba bài học phương pháp

1. **Khi một phép đo trả về "không có gì", việc ĐẦU TIÊN là chạy đối chứng bằng một cấu hình ĐÃ BIẾT
   CHẠY** — trước khi sửa thiết kế. Tôi đã sửa thiết kế bốn lần trên một đường đo đã hỏng (UART của
   kit chết). Quy tắc "tối đa 3 hướng sửa rồi dừng" có tác dụng, nhưng không cứu được việc chọn **sai
   đối tượng** để sửa. Đã biến thành công cụ: `scripts/branch_b_measure.sh` bắt buộc đối chứng.
2. **Một bộ số đo chỉ so sánh được khi mọi biến thể đến từ cùng một trạng thái mã nguồn, và điều đó
   phải do MÁY kiểm.** A-V0/A-V2 từng được đo bằng một bản `main.c` chưa commit → mọi tỷ số bị phóng
   đại (4,95× thành 3,67×). Kiểm tính đúng đắn **không** bắt được: cả hai bản firmware đều đúng từng
   bit, chỉ chạy nhanh khác nhau. Đã chặn bằng dấu vân tay nội dung `SRC_HASH`.
3. **Kiểm hạ tầng đo trên một đối tượng đã biết đúng trước khi dùng nó để xét đối tượng mới.** Cổng B0
   chủ ý không viết một dòng RTL nào của lõi: chỉ dựng bộ `riscv-tests` rồi chạy trên PicoRV32. Nhờ
   vậy khi lõi mới trượt một bài, chỉ còn một cách giải thích.

## 7. Còn lại

| Việc | Ghi chú |
|---|---|
| Đo công suất | chưa có thiết bị đo dòng |
| F6 điều kiện 4 (3 lần bật/tắt nguồn) | cần người dùng rút/cắm cáp, ~5 phút |
| Mô hình lớn hơn (M1-L ≈ 663 nghìn MAC, KWS DS-CNN) | kế hoạch gốc xếp là mở rộng |
| Đo 10.000 ảnh cho các biến thể còn lại | đã làm cho biến thể nhanh nhất của mỗi nhánh |
