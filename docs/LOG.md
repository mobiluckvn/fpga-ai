# Nhật ký làm việc

Mỗi phiên một mục, mới nhất ở trên cùng:

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
