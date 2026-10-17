# Kế hoạch kiểm chứng tính khả thi trên phần cứng (F0 → F8)

Mục đích: trả lời có/không cho từng rủi ro kỹ thuật TRƯỚC khi đầu tư vào thí nghiệm chính.
Mỗi cổng kiểm một rủi ro cụ thể. Làm đúng thứ tự. Một cổng = một thư mục `feasibility/F<n>_<tên>/`.

| Cổng | Rủi ro được kiểm | Kết luận nếu ĐẠT |
|---|---|---|
| F0 | Công cụ chạy được trên Mac, nhận được kit | Môi trường dùng được |
| F1 | Luồng mã nguồn mở sinh bitstream chạy thật | Nạp kit được từ Mac |
| F2 | Liên lạc UART hai chiều với Mac | Có kênh thu số đo |
| F3 | BSRAM 64 KB có khởi tạo sẵn nội dung | Chứa được firmware + trọng số |
| F4 | Khối nhân DSP suy luận đúng | Làm được lệnh DOT4 bằng DSP |
| F5 | SoC PicoRV32 chạy firmware C; mô phỏng = kit | Có nền tảng CPU |
| F6 | Phép đo chu kỳ tất định, ba nguồn khớp | Phương pháp đo tin cậy |
| F7 | Kernel int8 thật chạy đúng từng bit, đo được | Đường ống đo hoạt động trọn vẹn |
| F8 | Lệnh tùy biến DOT4 qua PCPI chạy đúng, có tăng tốc | Ý tưởng tối ưu tập lệnh khả thi |

---

## F0 — Môi trường trên Mac

**Việc làm**
1. `uname -m`, `sw_vers` → ghi vào `env/VERSIONS.md`.
2. Cài OSS CAD Suite (bản phát hành mới nhất cho darwin-arm64 hoặc darwin-x64, từ GitHub
   YosysHQ/oss-cad-suite-build) vào `~/tools/oss-cad-suite`. Làm theo README của gói cho macOS
   (Gatekeeper: nếu bị chặn, gỡ thuộc tính quarantine theo hướng dẫn của gói). Kích hoạt bằng
   `source ~/tools/oss-cad-suite/environment`.
3. Kiểm tra có đủ: `yosys -V`, `nextpnr-himbaechel --version`, `gowin_pack -h`, `openFPGALoader -V`,
   `verilator --version`, `iverilog -V`. Thiếu `gowin_pack` → `pip install apycula` trong `.venv`.
   Xác nhận nextpnr-himbaechel có uarch gowin (`nextpnr-himbaechel --help` hoặc thử build ở F1).
4. Cài xPack `riscv-none-elf-gcc` (tarball từ GitHub xpack-dev-tools/riscv-none-elf-gcc-xpack) vào
   `~/tools/`. Kiểm tra `riscv-none-elf-gcc --version` và biên dịch thử một file C với
   `-march=rv32im -mabi=ilp32`.
5. `python3 -m venv .venv && .venv/bin/pip install numpy pyserial`.
6. Viết `env/setup_env.sh` (export PATH cho mọi công cụ) để các phiên sau chỉ cần `source env/setup_env.sh`.
7. Nhờ người dùng cắm kit. Chạy `openFPGALoader --detect -b tangnano20k` (hoặc `--scan-usb`).
8. `ls /dev/cu.usbserial*` → ghi tên các cổng.
9. `git init`, tạo `.gitignore` (.venv, build/, *.fs, *.json của nextpnr, obj_dir/).

**ĐẠT khi**: mọi lệnh ở bước 3–4 chạy; `--detect` thấy chip GW2A(R)-18; có ít nhất một cổng serial.
**Dự phòng**: nếu openFPGALoader không thấy kit → thử cáp khác/cổng USB khác (nhờ người dùng),
cập nhật openFPGALoader; ghi LOG và hỏi người dùng.

---

## F1 — Blinky bằng luồng mã nguồn mở

**Việc làm**
1. Tạo `hw/tangnano20k.cst`. ĐỐI CHIẾU với ví dụ chính thức của Sipeed trước khi dùng. Giá trị tham khảo
   (phải xác minh): clock 27 MHz chân 4; LED0–LED5 chân 15–20 (tích cực mức thấp); UART TX (FPGA→PC)
   chân 69, RX chân 70; nút S1 chân 88, S2 chân 87; IO_TYPE LVCMOS33.
2. `feasibility/F1_blinky/top.v`: bộ đếm 27 MHz, 6 LED chạy nhị phân ~1–2 Hz cho bit thấp nhất.
3. Makefile (đối chiếu tham số với `examples/himbaechel/` của Apicula):
   - `yosys -p "read_verilog top.v; synth_gowin -top top -json build/top.json"` (thêm tùy chọn họ chip
     nếu `help synth_gowin` có, ví dụ cho GW2A)
   - `nextpnr-himbaechel --json build/top.json --write build/pnr.json --device GW2AR-LV18QN88C8/I7
      --vopt family=GW2A-18C --vopt cst=../../hw/tangnano20k.cst --freq 27 --report build/report.json`
   - `gowin_pack -d GW2A-18C -o build/top.fs build/pnr.json`
   - `openFPGALoader -b tangnano20k build/top.fs`
4. Nạp, hỏi người dùng LED có chạy không, chạy có đúng tốc độ không.
5. Lưu `report.json` và log vào `results/feasibility/F1/`.

**ĐẠT khi**: người dùng xác nhận LED chạy đúng; nạp lại 3 lần đều được.
**Dự phòng**: lỗi `--device`/`family` → xem Makefile ví dụ của Apicula, thử bản Apicula/nextpnr mới hơn;
vẫn hỏng → build cùng top.v bằng Gowin EDA Education để tách lỗi luồng hay lỗi kit.

---

## F2 — UART hai chiều

**Việc làm**
1. `feasibility/F2_uart/`: UART TX/RX 115200 8N1 tự viết (bộ chia từ 27 MHz; ghi sai số baud thực tế).
2. Hành vi: cứ 1 giây gửi `F2 OK <bộ đếm>\r\n`; byte nhận được thì gửi lại (echo).
3. Testbench Icarus/Verilator cho UART trước khi nạp.
4. `scripts/uart_check.py`: mở cổng, chờ dòng `F2 OK` (timeout 5 s), rồi gửi 10.240 byte ngẫu nhiên
   theo khối 256 byte, so sánh echo.

**ĐẠT khi**: nhận dòng `F2 OK`; 10.240 byte echo không sai byte nào.
**Dự phòng**: không thấy dữ liệu → thử cổng serial còn lại; kiểm tra chân TX/RX bị đảo; kiểm tra cầu BL616
có cần chuyển sang chế độ UART không (tra tài liệu Sipeed/kinh nghiệm cộng đồng); thử 9600 baud.

---

## F3 — BSRAM 64 KB có khởi tạo (rủi ro lớn nhất)

**Việc làm**
1. `scripts/gen_pattern.py`: sinh `pattern.hex` 16.384 từ 32 bit (64 KB) từ LFSR có hạt giống cố định;
   in CRC32 kỳ vọng (theo thứ tự byte little-endian của từng từ).
2. `feasibility/F3_bsram/top.v`: mảng `reg [31:0] mem [0:16383]` khởi tạo bằng `$readmemh("pattern.hex")`,
   đọc đồng bộ 1 chu kỳ. Máy trạng thái đọc toàn bộ, tính CRC32 phần cứng, gửi qua UART:
   `F3,ROM,<crc hex>`. Sau đó: ghi một mẫu thứ hai (vd. địa chỉ XOR 0xA5A5A5A5) vào toàn bộ, đọc lại,
   gửi `F3,RW,<crc hex>`.
3. Script so sánh với CRC kỳ vọng từ Python.
4. Từ báo cáo nextpnr: số khối BSRAM đã dùng (kỳ vọng ~32/46), Fmax.

**ĐẠT khi**: cả hai CRC khớp; 64 KB được xếp; Fmax ≥ 27 MHz.
**Dự phòng (thử theo thứ tự)**: (a) cập nhật Apicula/nextpnr bản mới; (b) khởi tạo trực tiếp primitive BSRAM
của Gowin (SP/SDPB) thay vì để Yosys suy luận; (c) giảm còn 32 KB; (d) dùng Gowin EDA Education cho bước
tổng hợp. Ghi rõ phương án nào thành công — đây là thông tin quyết định cho toàn dự án.

---

## F4 — Khối nhân DSP

**Việc làm**
1. `feasibility/F4_dsp/`: hai LFSR sinh a, b 32 bit mỗi chu kỳ. Tính
   `dot = Σ_{i=0..3} int8(a[8i+7:8i]) * int8(b[8i+7:8i])` (có dấu), cộng dồn vào thanh ghi 32 bit trong
   1.048.576 chu kỳ. Gửi `F4,<biến thể>,<acc hex>`.
2. Hai biến thể: (DSP) để Yosys ánh xạ phép nhân vào khối MULT của Gowin; (LUT) ép dùng logic
   (vd. thuộc tính/cờ yosys, hoặc nhân bằng cộng dịch).
3. Python tính giá trị kỳ vọng với cùng LFSR.
4. Ghi LUT, FF, số khối DSP/MULT, Fmax của từng biến thể.

**ĐẠT khi**: giá trị khớp cho cả hai biến thể; báo cáo cho thấy biến thể DSP thật sự dùng khối MULT.
**Dự phòng**: nếu DSP sai hoặc không ánh xạ được → ghi lại, dùng biến thể LUT cho các bước sau
(dự án vẫn khả thi, chỉ tốn LUT hơn).

---

## F5 — SoC PicoRV32 chạy firmware C

**Việc làm**
1. Lấy `picorv32.v` từ YosysHQ/picorv32, ghi commit hash vào `env/VERSIONS.md`.
   Tham số: `ENABLE_COUNTERS=1, ENABLE_COUNTERS64=1, ENABLE_MUL=0, ENABLE_FAST_MUL=1, ENABLE_DIV=1,
   BARREL_SHIFTER=1, COMPRESSED_ISA=0, ENABLE_PCPI=0` (F8 mới bật PCPI). Kiểm tra lại ý nghĩa tham số
   trong README của picorv32 (FAST_MUL và MUL loại trừ nhau).
2. `feasibility/F5_soc/`: SoC với bản đồ bộ nhớ:
   - `0x0000_0000–0x0000_FFFF`: RAM 64 KB (BSRAM, như F3), nạp firmware bằng `$readmemh`
   - `0x1000_0000`: UART data (ghi = gửi; đọc = byte nhận), `0x1000_0004`: UART status (bit0 tx_busy, bit1 rx_valid)
   - `0x1000_0010`: bộ đếm phần cứng điều khiển (ghi 1 = xóa và chạy, ghi 0 = dừng), `0x1000_0014`: giá trị
   - `0x1000_0020`: LED
3. Firmware `fw/`: `start.S` (đặt sp ở đỉnh RAM, xóa .bss, gọi main), `link.ld`, `main.c` in
   `F5,hello,<git hash ngắn>`, in giá trị `rdcycle`. Makefile: gcc → elf → bin → hex từ 32 bit cho
   `$readmemh`. Ghi kích thước `.text`.
4. Mô phỏng Verilator cùng top (mô hình UART in ra stdout), chạy cùng file hex.
5. Bài thử chu kỳ: hàm `busy_loop(1000)` viết bằng asm cố định, đo bằng `rdcycle` trước/sau, in
   `F5,loop,<cycles>`.

**ĐẠT khi**: kit in `F5,hello,...`; `F5,loop` trên kit = trong Verilator (bằng nhau tuyệt đối).
**Dự phòng**: firmware không chạy → kiểm tra thứ tự byte của file hex, địa chỉ reset (PROGADDR_RESET=0),
STACKADDR; so dạng sóng Verilator. Nếu F3 phải giảm còn 32 KB thì RAM 32 KB.

---

## F6 — Độ tin cậy của phép đo

**Việc làm** (firmware trên SoC F5)
1. Hiệu chuẩn: đo `rdcycle` hai lần liên tiếp 1.000 lần → phân phối (kỳ vọng một hằng số duy nhất).
2. Đo cùng lúc bằng `rdcycle` và bộ đếm phần cứng cho 5 đoạn code dài khác nhau (busy_loop 10, 100, 1k, 10k,
   100k). Kỳ vọng: hiệu số giữa hai nguồn là một hằng số.
3. Kiểm `rdcycleh`: một vòng lặp vượt 2^32 chu kỳ (~159 s ở 27 MHz) — chỉ chạy một lần, xác nhận phần cao tăng.
4. Lặp bước 2 qua 3 lần tắt/bật nguồn kit (nhờ người dùng rút/cắm, rồi nạp lại SRAM).
5. Đối chiếu với Verilator cho bước 2.
6. Ghi CSV `results/feasibility/F6/measure.csv`: `run,length,mcycle,hw_count,sim_cycles`.

**ĐẠT khi**: overhead là một hằng số; hw_count − mcycle là hằng số ở mọi độ dài; kit = mô phỏng;
3 lần bật nguồn cho số giống hệt.

---

## F7 — Kernel int8 thật, đúng từng bit

**Việc làm**
1. `scripts/gen_f7_data.py` (numpy, hạt giống cố định) sinh `f7_data.h`:
   - Bài A: 100 cặp vector int8 dài 1.024 → tích vô hướng int32.
   - Bài B: một lớp Conv 3×3, 1 kênh vào, 8 kênh ra, ảnh 28×28 int8 (giống lớp conv1 của mô hình M1-S),
     trọng số int8 ngẫu nhiên, bias int32, ReLU, requantize về int8 bằng (M0 int32, shift) kiểu gemmlowp.
   - Python tính kết quả chuẩn và CRC32 của từng đầu ra.
2. Firmware: kernel C thẳng (vòng lặp đơn giản, `-O2`), đo chu kỳ từng bài bằng `rdcycle` và bộ đếm phần cứng,
   in `F7,<bài>,<cycles>,<hw_count>,<instret>,<crc>`.
3. Chạy trong Verilator và trên kit.
4. Tính chu kỳ/MAC cho bài B (48.672 MAC). Ngoại suy THÔ thời gian M1-S (192.064 MAC) — ghi rõ là ước tính.
5. Kiểm tra dung lượng: firmware + dữ liệu vẫn vừa RAM.

**ĐẠT khi**: CRC trên kit = Python cho cả hai bài; chu kỳ kit = mô phỏng; có số chu kỳ/MAC.

---

## F8 — Lệnh tùy biến DOT4 qua PCPI (kiểm tra ý tưởng)

**Việc làm**
1. Bật `ENABLE_PCPI=1`. Viết `rtl/ext/pcpi_dot4.v`: nhận lệnh opcode custom-0 (`0001011`), funct3=000,
   funct7=0000000; `rd = Σ int8(rs1[i]) * int8(rs2[i])`, i=0..3. Dùng biến thể nhân đã ĐẠT ở F4.
2. Testbench riêng cho khối: 1.000.000 cặp ngẫu nhiên + giá trị biên (−128, 127, 0) so với mô hình Python.
3. Firmware: macro `dot4()` dùng `.insn r 0x0B, 0, 0, rd, rs1, rs2`; bài A của F7 viết lại với `lw` 4 byte + DOT4.
   Chọn bằng cờ `-DUSE_DOT4` để chỉ khác một điểm.
4. Chạy cả hai bản (không DOT4 / có DOT4) trên cùng bitstream có PCPI, và bản không DOT4 trên bitstream F5.
5. Ghi: chu kỳ, tăng tốc, LUT/DSP/Fmax tăng thêm so với F5. Ghi độ trễ PCPI quan sát được (chu kỳ/lệnh DOT4).

**ĐẠT khi**: CRC khớp; kit = mô phỏng; có số tăng tốc thật (bất kể lớn hay nhỏ — đây là dữ liệu).

---

## Kết thúc giai đoạn khả thi
Điền phần "Kết luận" trong `docs/FEASIBILITY_REPORT.md`: Go / Go có điều kiện / No-Go, kèm phương án
dự phòng đã phải dùng (nếu có) và đề xuất điều chỉnh kế hoạch thí nghiệm chính. Sau đó DỪNG và báo người dùng.
