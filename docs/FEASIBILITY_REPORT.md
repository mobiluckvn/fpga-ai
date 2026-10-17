# Báo cáo kiểm chứng tính khả thi trên phần cứng — TinyML trên lõi RISC-V, Tang Nano 20K

**Ngày thực hiện**: 2026-10-17 · **Người thực hiện**: Vũ Trí Công (học viên cao học PTIT)
**Máy**: Mac Intel — x86_64, macOS 26.6.2 (build 25G83)
**Kit**: Sipeed Tang Nano 20K, FPGA GW2AR-LV18QN88C8/I7 (họ GW2A-18C), thạch anh 27 MHz
**Phạm vi**: **toàn bộ** các cổng F0 → F8 của `docs/FEASIBILITY_PLAN.md`.

**Bản chia sẻ/xuất PDF**: https://claude.ai/code/artifact/bb8b43e4-8aaf-4a75-94c3-ea4ab6ea5834
(bản rút gọn của tài liệu này; file trong repo là bản gốc đầy đủ).

Mọi con số trong báo cáo này lấy từ output thật của công cụ hoặc của kit. Log thô và vật phẩm
(bitstream, netlist, firmware, CSV) lưu ở `results/feasibility/F<n>/`, kèm `MANIFEST.md` ghi
SHA256 của từng file để truy nguyên. Nhật ký chi tiết từng cổng: `docs/LOG.md`.

---

## 1. Tổng hợp cổng

| Cổng | Rủi ro được kiểm | Kết quả | Dự phòng đã phải dùng |
|---|---|---|---|
| F0 | Công cụ chạy được trên Mac, nhận được kit | **ĐẠT** | không |
| F1 | Luồng mã nguồn mở sinh bitstream chạy thật | **ĐẠT** | bỏ `gowin_pack -c` |
| F2 | Liên lạc UART hai chiều với Mac | **ĐẠT** | khối ghi của host ≤ 64 byte |
| F3 | BSRAM 64 KB có khởi tạo sẵn nội dung | **ĐẠT** | **không** |
| F4 | Khối nhân DSP suy luận đúng | **ĐẠT có dự phòng** | **có** — phải gọi primitive `MULT18X18` trực tiếp |
| F5 | SoC PicoRV32 chạy firmware C; mô phỏng = kit | **ĐẠT** | `synth_gowin -nodsp` |
| F6 | Phép đo chu kỳ tất định, ba nguồn khớp | **ĐẠT** (4/5 điều kiện kiểm được; xem mục 7) | không |
| F7 | Kernel int8 thật chạy đúng từng bit | **ĐẠT** | không |
| F8 | Lệnh tùy biến DOT4 qua PCPI | **ĐẠT** | không |

### Số đo chính từng cổng

| Cổng | Số đo | Vật phẩm |
|---|---|---|
| F0 | OSS CAD Suite 20261016 · yosys 0.70+145 · nextpnr-himbaechel 0.11.1-63 · apycula 0.35.dev5 · openFPGALoader 1.1.1 · verilator 5.053 · iverilog 14.0 · riscv-none-elf-gcc 15.2.0. JTAG idcode `0x81b` = GW2A(R)-18(C). Hai cổng serial. | `results/feasibility/F0/` |
| F1 | Fmax **347,58 MHz** @ ràng buộc 27 · LUT4 30 · DFF 30 · IOB 7/384 · nạp SRAM **3/3** lần OK · người dùng xác nhận LED chạy đúng tốc độ | `results/feasibility/F1/` |
| F2 | Sai số baud **+0,1603 %** (DIV=234 → 115.384,62) · **0/10.240 byte sai** · cổng UART `/dev/cu.usbserial-20250303171` · Fmax 187,48 MHz · bộ đếm trong FPGA: rx +10.240, dr=0, er=0, ov=0, FIFO hwm 1/63 · 5.248 B/s | `results/feasibility/F2/` |
| F3 | **BSRAM 32/46 (69,6 %)** · Fmax **157,36 MHz** · CRC32 ROM `C7CD86AA`, RW `D63B5AB4` **khớp Python 3/3 lần** · phép phản chứng: đổi hạt giống → ROM đổi đúng thành `454701B8`, RW giữ nguyên | `results/feasibility/F3/` |
| F4 | acc `FEF834C3` khớp Python **3/3 lần** với biến thể PRM và LUT; **sai** với cả hai biến thể để yosys suy luận DSP. LUT4 PRM 811 / LUT 1764; Fmax PRM 233,64 / LUT 73,08 MHz | `results/feasibility/F4/` |
| F5 | `F5,loop` kit = Verilator **bằng tuyệt đối**: **14.006** chu kỳ; thêm 7 khoá khác cũng khớp tuyệt đối, 3/3 lần · `.text` **1.220 byte** · BSRAM 32/46 · LUT4 7.950 · Fmax 70,05 MHz | `results/feasibility/F5/` |
| F6 | Overhead **5 chu kỳ** (hằng số 1000/1000) · `hw_count − mcycle` = **24** (hằng số ở 5 độ dài) · kit = Verilator **bằng tuyệt đối** cả 5 độ dài · `rdcycleh` 0→1 sau **4.480.000.015** chu kỳ (165,9 s) | `results/feasibility/F6/` |

---

## 2. Tài nguyên và timing (từ `report.json` của nextpnr)

| Thiết kế | LUT4 | FF | BSRAM | DSP/MULT | Fmax (MHz) |
|---|---:|---:|---|---|---:|
| F1 Blinky | 30 | 30 | 0 | 0 | 347,58 |
| F2 UART | 883 | 236 | 0 (8× RAM16SDP4 cho FIFO) | 0 | 187,48 |
| F3 BSRAM 64 KB | 865 | 207 | **32/46** | 0 | 157,36 |
| F4-DSP (yosys suy luận — **SAI**) | 771 | 291 | 0 | 4× MULT9X9 | 225,28 |
| F4-D18 (toán hạng 18 bit — **SAI**) | 815 | 291 | 0 | 4× MULT9X9 | 237,02 |
| **F4-PRM (MULT18X18 trực tiếp — ĐÚNG)** | **811** | 291 | 0 | **4× MULT18X18** | **233,64** |
| F4-LUT (`-nodsp` — ĐÚNG) | 1764 | 291 | 0 | 0 | 73,08 |
| **F5/F6/F7 SoC PicoRV32 + RAM 64 KB** | **7950** | **1069** | **32/46** | 0 (nhân 32×32 bằng LUT vì `-nodsp`) | **70,05** |
| F8 SoC + DOT4, nhân bằng `MULT18X18` | 8065 (**+115**) | 1153 (+84) | 32/46 | **4× MULT18X18** | 71,89 (**+1,83**) |
| F8 SoC + DOT4, nhân bằng LUT | 9086 (**+1136**) | 1153 (+84) | 32/46 | 0 | 73,83 (+3,78) |

**Tài nguyên tổng của chip** (dùng để lập ngân sách): LUT4 20.736 · DFF 15.552 · ALU 15.552 ·
IOB 384 · **BSRAM 46** · MULT9X9 96 · **MULT18X18 48** · MULT36X36 12 · MULTALU18X18 24 ·
MULTADDALU18X18 24 · ALU54D 24 · rPLL 2 · BUFG 24 · RAM16SDP4 648.

**Còn dư sau F8 (bản DSP)**: LUT4 **12.671** (61,1 %) · BSRAM **14** (30,4 %) · MULT18X18 **44** (91,7 %) ·
biên Fmax **2,66 lần** so với 27 MHz.

Chi phí thật của DOT4, đo bằng cách so với chính bản nền F5: **+115 LUT4 (+1,4 %) và +84 DFF** nếu dùng
`MULT18X18`, hoặc **+1.136 LUT4 (+14,3 %)** nếu nhân bằng logic. Fmax **không giảm** ở cả hai bản
(thậm chí nhúc nhích lên, trong phạm vi nhiễu của place & route) vì DOT4 trả lời trong 2 chu kỳ và
phép nhân int8 ngắn hơn đường tới hạn hiện có.

---

## 3. Phương pháp đo chu kỳ (kết quả F5 + F6)

Ba nguồn số đo đã được đối chiếu trên cùng một đoạn code `busy_loop(N)` (2 lệnh/vòng, viết bằng
asm cố định nên không phụ thuộc mức tối ưu của trình biên dịch):

| N | `rdcycle` | bộ đếm phần cứng | `rdinstret` | hiệu (hw − rdcycle) |
|---:|---:|---:|---:|---:|
| 10 | 141 | 165 | 23 | 24 |
| 100 | 1.401 | 1.425 | 203 | 24 |
| 1.000 | 14.001 | 14.025 | 2.003 | 24 |
| 10.000 | 140.001 | 140.025 | 20.003 | 24 |
| 100.000 | 1.400.001 | 1.400.025 | 200.003 | 24 |

Số liệu gốc: `results/feasibility/F6/measure.csv`. **Kit và Verilator khớp bằng tuyệt đối ở cả ba cột,
cả 5 độ dài.**

**Mô hình chu kỳ rút ra**: `mcycle = 14·N + 1` và `instret = 2·N + 3`. Tức mỗi vòng 2 lệnh tốn đúng
**14 chu kỳ** (7 chu kỳ/lệnh với bus 1 chu kỳ chờ). Bài `rdcycleh` tự xác nhận lại mô hình này ở quy mô
lớn: 320.000.000 vòng × 14 = 4.480.000.000, đo thực được **4.480.000.015** — lệch đúng 15 chu kỳ cho
chi phí vào/ra vòng lặp.

**Overhead của chính phép đo**: đọc `rdcycle` hai lần liên tiếp cho **đúng 5 chu kỳ, 1000/1000 lần**,
chỉ một giá trị duy nhất — nên có thể trừ overhead này một cách xác định.

---

## 4. Ba phát hiện về công cụ, bắt buộc phải tuân theo

Đây là kết quả quan trọng nhất của giai đoạn khả thi: ba cái bẫy của luồng mã nguồn mở trên chip này,
phát hiện bằng đo thật trên kit, kèm cách xử lý đã kiểm chứng.

### 4.1. `synth_gowin` mặc định là `-family gw1n`
`yosys -p 'help synth_gowin'` nói rõ: mặc định `gw1n`. Với GW2AR-18 **bắt buộc** truyền
`-family gw2a`, nếu không sẽ tổng hợp cho sai họ chip. Phát hiện khi đối chiếu `examples/Makefile`
của Apicula trước lần build đầu (quy tắc 6).

### 4.2. Bitstream nén (`gowin_pack -c`) không nạp được
apycula 0.35.dev5 sinh file `.fs` nén mà openFPGALoader v1.1.1 không parse được cho thiết kế F2:
`FsParser: checksum data is truncated` (tái lập 2/2 lần). Bản **không nén** nạp bình thường.
Lỗi phụ thuộc thiết kế (F1 nén thì nạp được). → **Đã bỏ `-c` khỏi luồng của mọi cổng.**
Giá phải trả: bitstream 4,6–7,3 MB thay vì 0,7–1,1 MB; thời gian nạp vẫn ~1 giây.

### 4.3. Yosys suy luận DSP cho phép nhân int8 có dấu → **kết quả SAI trên kit**
Với `synth_gowin` mặc định, yosys ánh xạ `$signed(a8) * $signed(b8)` vào `MULT9X9`, và trên kit
**byte cao của từng tích bị sai** (8 bit thấp vẫn đúng). Cùng RTL đó với `-nodsp` cho kết quả đúng,
nên lỗi nằm ở đường suy luận/ánh xạ DSP, không ở RTL. Mô phỏng Icarus **không** phát hiện được
(nó không mô phỏng khối DSP thật) — đây là bài học phương pháp: **phép nhân phải kiểm trên kit.**

Hai cách dùng được, cả hai đã kiểm trên kit (3/3 lần):

| Cách | Mô tả | LUT4 | Fmax |
|---|---|---:|---:|
| **PRM** | Gọi trực tiếp `MULT18X18`, `ASIGN=BSIGN=0` (không dấu), toán hạng int8 mở rộng dấu lên 18 bit, đọc `DOUT[17:0]` như số có dấu 18 bit | **811** | **233,64 MHz** |
| LUT | `synth_gowin -nodsp`, nhân bằng logic | 1764 | 73,08 MHz |

Cách PRM đúng về số học mà **không phụ thuộc đường cờ dấu của khối DSP**: với x′ = x mod 2¹⁸ và
y′ = y mod 2¹⁸ thì x′·y′ ≡ x·y (mod 2¹⁸), và |x·y| ≤ 128·128 = 16.384 < 2¹⁷, nên 18 bit thấp đọc như
số có dấu chính là x·y. Giao diện primitive lấy từ `apicula/examples/dsp-mult18x18.v` — ví dụ mà
Apicula tự kiểm thử trên kit thật (`hil-dsp-mult18x18-tangnano20k`).

**Quy tắc cho các giai đoạn sau**: SoC build với `-nodsp`; khối DOT4 của F8 dùng cách PRM.
`-nodsp` chỉ tắt phần *suy luận*, không ảnh hưởng primitive gọi trực tiếp, nên hai điều này
dùng chung được trong một thiết kế.

---

## 5. Giới hạn của kênh liên lạc (kết quả F2)

Chiều **FPGA → PC** (kênh thu số đo của dự án) hoạt động nguyên vẹn. Chiều **PC → FPGA** có giới hạn
**không nằm ở FPGA**:

- Nếu host ghi **≥ 67 byte trong một `write()`**, chiều FPGA→PC bị mất byte.
- Bộ đếm bên trong FPGA chứng minh FPGA **nhận đủ** (rx tăng đúng số byte đã gửi) và **phát đủ**
  (tx = số byte echo + số byte thông báo), với `dr=0` (không bỏ byte vì FIFO đầy), `er=0`
  (không lỗi bit stop), mức FIFO cao nhất chỉ **1/63**.
- Dùng luồng đọc riêng trên host **không** cứu được → không phải host đọc chậm.
- Khối ghi lớn nhất còn nguyên vẹn: **66 byte**. Luồng đo chốt ở **64 byte** (một gói USB).

→ Kết luận: giới hạn của cầu FT2232 + driver macOS. **Mọi script gửi dữ liệu PC→FPGA phải chia khối
≤ 64 byte.** Kênh thu số đo không bị ảnh hưởng.

**Chưa đo**: thông lượng FPGA→PC liên tục ở full baud (bài kiểm F2 theo nhịp gửi-rồi-chờ nên chỉ đạt
~53 kbit/s). Việc này sẽ tự nhiên được kiểm ở F7 khi firmware in dòng log dài.

---

## 6. Lỗi môi trường trên máy này (kết quả F5)

Verilator không biên dịch được: `fatal error: 'cstddef' file not found`. Nguyên nhân: Command Line
Tools 26.5.0 thiếu nội dung `/Library/Developer/CommandLineTools/usr/include/c++/v1`, nên `clang++`
không thấy libc++. `-isysroot` **không** cứu được vì clang chỉ tìm libc++ trong đường của toolchain.
Thư viện vẫn có trong SDK.

`env/setup_env.sh` tự phát hiện và đặt `TN20K_CXX_INC=-I$(xcrun --show-sdk-path)/usr/include/c++/v1`;
Makefile truyền cờ này cho verilator qua `-CFLAGS`. Các phiên sau không phải xử lý lại.

---

## 7. Điều kiện của F6 chưa kiểm — và ý nghĩa của nó

Năm điều kiện ĐẠT của F6:

| Điều kiện | Trạng thái |
|---|---|
| 1. Overhead của phép đo là một hằng số | **ĐẠT** — đúng 5 chu kỳ, 1000/1000 lần |
| 2. `hw_count − mcycle` là hằng số ở mọi độ dài | **ĐẠT** — 24 chu kỳ ở cả 5 độ dài |
| 3. Kit = mô phỏng | **ĐẠT** — bằng tuyệt đối, cả 3 cột × 5 độ dài |
| 5. `rdcycleh` tăng khi vượt 2³² chu kỳ | **ĐẠT** — 0 → 1, lệch 15 chu kỳ so với mô hình |
| 4. Ba lần tắt/bật nguồn cho số giống hệt | **KHÔNG KIỂM** — bỏ theo quyết định của người thực hiện, 2026-10-17 |

Điều kiện 4 **không được kiểm**, không phải "đã kiểm và đạt". Ghi rõ như vậy để báo cáo trung thực.

**Rủi ro còn lại và cách giảm**: điều kiện 4 nhằm bắt loại lỗi "số đo phụ thuộc trạng thái sau khi bật
nguồn" (ví dụ thanh ghi không được khởi tạo, hoặc cấu hình SRAM còn sót từ bitstream trước). Ba quan sát
làm rủi ro này nhỏ:
- Mỗi lần nạp SRAM trong suốt F1–F6 (tổng **trên 20 lần nạp**) đều cho số đo giống nhau, trong đó có
  những lần nạp tiếp ngay sau một bitstream khác hẳn.
- F6 đã chạy 3 lần đọc độc lập (mở/đóng cổng) và F5 cũng vậy, luôn ra số giống hệt.
- Mô hình `mcycle = 14·N + 1` khớp tuyệt đối ở 5 độ dài trải 4 bậc độ lớn và được xác nhận lại ở
  quy mô 4,48 tỷ chu kỳ — một lỗi phụ thuộc trạng thái bật nguồn khó mà cho ra mô hình sạch như vậy.

**Đề nghị**: chạy điều kiện 4 trước khi lấy số đo chính thức cho luận văn. Quy trình đã làm sẵn, mỗi
lần mất ~15 giây: rút/cắm cáp USB rồi
`cd feasibility/F6_measure && make cycle RUN=2` (rồi `RUN=3`, `RUN=4`).

---

## 8. Kết luận

### **GO CÓ ĐIỀU KIỆN**

**Toàn bộ chín rủi ro kỹ thuật (F0–F8) đều có lời giải đã chứng minh trên phần cứng thật.**
Rủi ro lớn nhất của dự án — **BSRAM 64 KB có khởi tạo sẵn nội dung qua luồng mã nguồn mở** — đã
giải quyết xong **không cần tới bất kỳ phương án dự phòng nào** trong bốn phương án (a)–(d) của kế hoạch.
Nền tảng đo lường cũng đã chứng minh được điều quan trọng nhất cho một luận văn đo hiệu năng:
**số chu kỳ trên kit bằng tuyệt đối số chu kỳ trong mô phỏng**, và chênh giữa hai nguồn đếm độc lập
là một hằng số.

Và quan trọng nhất về mặt khoa học: **ý tưởng trung tâm của luận văn đã có bằng chứng số.** Một lệnh
tùy biến duy nhất (DOT4) cho **tăng tốc 3,985× đo trên kit**, kết quả đúng từng bit, với chi phí phần
cứng **+115 LUT4 (+1,4 %)** và **không giảm Fmax**. Giả thuyết "thêm lệnh tùy biến làm giảm số chu kỳ
suy luận" không còn là giả thuyết.

Ba điều kiện kèm theo, tất cả đã có cách xử lý đã kiểm chứng:

1. **Không dùng DSP do yosys suy luận.** SoC build với `synth_gowin -nodsp`; khối DOT4 gọi trực tiếp
   primitive `MULT18X18` theo cách PRM (mục 4.3).
2. **Không dùng `gowin_pack -c`.** Bitstream không nén (mục 4.2).
3. **Script PC→FPGA chia khối ≤ 64 byte** (mục 5).

### Điều chỉnh đề xuất cho kế hoạch thí nghiệm chính

| # | Đề xuất | Lý do |
|---|---|---|
| 1 | Giữ nguyên mục tiêu 64 KB RAM cho firmware + trọng số | F3/F5 chứng minh xếp được, dùng 32/46 BSRAM, còn dư 14 khối |
| 2 | **Biến thể A-V2/A-V3 (DOT4, REQ) dùng cách PRM** cho mọi phép nhân int8 | F4: cách này đúng trên kit, tiết kiệm 953 LUT4 và Fmax cao hơn 3,2 lần so với nhân bằng logic |
| 3 | **Mọi khối nhân mới phải có bài kiểm trên kit, không tin mô phỏng** | F4: Icarus đúng trong khi phần cứng sai |
| 4 | Giữ `-nodsp` cho lõi PicoRV32 ở mọi biến thể | F5: `arith` khớp tuyệt đối chứng minh MUL/DIV đúng; nếu đổi phải kiểm lại |
| 5 | Dùng `rdcycle` làm số đo chính, bộ đếm phần cứng làm đối chứng, trừ overhead 5 chu kỳ | F6: cả hai nguồn tất định, chênh nhau một hằng số |
| 6 | Mỗi biến thể phải chạy cùng firmware trong Verilator và trên kit, và **chỉ ghi nhận số đo khi hai bên bằng tuyệt đối** | F5/F6: đã chứng minh làm được, nên đây là tiêu chí thực tế chứ không phải lý tưởng |
| 7 | Thêm vào kế hoạch: đo thông lượng FPGA→PC liên tục ở full baud | F2 chưa đo phần này |
| 8 | Chạy điều kiện 4 của F6 (3 lần bật nguồn) trước khi lấy số đo chính thức | Mục 7 |
| 9 | Ngân sách Fmax **không còn là rủi ro**: thêm DOT4 cho Fmax 71,89 MHz, *cao hơn* bản nền 70,05 MHz | F8 đã đo; biên 2,66 lần so với 27 MHz |
| 10 | **Hướng tối ưu nên nhắm vào số lệnh, không phải độ trễ phép toán** | F8: tăng tốc (3,985×) bằng đúng tỉ lệ giảm số lệnh (3,983×), CPI gần như không đổi (6,86→6,85); DOT4 chỉ đắt hơn `ADD` 1 chu kỳ |
| 11 | Khi mở rộng sang conv, **đừng kỳ vọng 3,985×**: phần chỉ số 2 chiều và requantize của conv1 (72,59 chu kỳ/MAC ở F7) không được DOT4 cắt. Cân nhắc thêm lệnh cho phần địa chỉ/requantize (đó chính là vai trò của REQ trong kế hoạch) | F7 + F8 |

### Giai đoạn khả thi đã hoàn tất

Cả chín cổng F0 → F8 đã làm xong. Không còn việc nào của giai đoạn này, ngoài điều kiện 4 của F6
(ba lần tắt/bật nguồn) mà người thực hiện đã quyết định bỏ — xem mục 7.

| Bài | Biến thể | MAC | Chu kỳ | hw_count | instret | CPI | chu kỳ/MAC | CRC khớp Python |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A dot 1024 ×100 | C thẳng (A-V0) | 102.400 | 4.921.446 | 4.921.485 | 717.812 | 6,86 | **48,06** | **có** (`64F298C2`) |
| A dot 1024 ×100 (offset ⊥4) | C thẳng | 102.400 | 4.921.446 | 4.921.485 | 717.812 | 6,86 | 48,06 | **có** (`3D68C1ED`) |
| A dot 1024 ×100 (offset ⊥4) | **DOT4** | 102.400 | **1.235.011** | 1.235.050 | 180.205 | 6,85 | **12,06** | **có** (`3D68C1ED`) |
| B conv1 28×28×8 | C thẳng (A-V0) | 48.672 | 3.533.204 | 3.533.252 | 570.232 | 6,20 | **72,59** | **có** (`661C5304`) |

**Tăng tốc của DOT4 trên bài A: 3,985×** (số lệnh giảm 3,983×). Số liệu gốc:
`results/feasibility/F7/kernel.csv` và `results/feasibility/F8/dot4.csv`.

Số liệu gốc: `results/feasibility/F7/kernel.csv`. Chu kỳ kit = Verilator **bằng tuyệt đối** ở cả ba cột
(cycles, hw_count, instret), lặp lại 3/3 lần đọc độc lập.

**Ước tính THÔ thời gian suy luận M1-S** (192.064 MAC), ngoại suy từ chu kỳ/MAC của bài B (72,59):
**≈ 13,94 triệu chu kỳ ≈ 516 ms @27 MHz**.

Đây là **ước tính, không phải số đo**. Ba lý do nó có thể lệch: (a) M1-S còn MaxPool và Dense với chi phí
trên mỗi MAC khác conv; (b) conv2 có 16 kênh vào nên tỉ lệ nạp lại trọng số/activation khác conv1;
(c) chu kỳ/MAC của conv1 đo được đã bao gồm chi phí requantize cho 5.408 điểm đầu ra, phần này không
tỉ lệ với số MAC. Con số thật chỉ có khi chạy cả mô hình ở giai đoạn thí nghiệm chính.
