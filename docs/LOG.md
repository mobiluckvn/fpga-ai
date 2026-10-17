# Nhật ký làm việc

Mỗi phiên một mục, mới nhất ở trên cùng:

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
