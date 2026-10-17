# Hướng dẫn dựng lại và chạy lại toàn bộ (F0 → F6)

Tài liệu này để một người khác (hoặc chính mình sau vài tháng) dựng lại môi trường và chạy lại
mọi phép đo trong `docs/FEASIBILITY_REPORT.md` từ đầu.

Mọi lệnh dưới đây chạy từ gốc repo, trừ khi ghi khác.

---

## 1. Cài môi trường (một lần)

Máy đã kiểm: **macOS, Intel x86_64**. Máy Apple Silicon thì đổi `darwin-x64` thành `darwin-arm64`.

```bash
mkdir -p ~/tools && cd ~/tools

# OSS CAD Suite: yosys, nextpnr-himbaechel, gowin_pack (apycula), openFPGALoader, verilator, iverilog
curl -LO https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-10-16/oss-cad-suite-darwin-x64-20261016.tgz
tar -xzf oss-cad-suite-darwin-x64-20261016.tgz
cd oss-cad-suite && ./activate && cd ..     # gỡ quarantine của macOS, theo README của gói

# Toolchain RISC-V
curl -LO https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases/download/v15.2.0-1/xpack-riscv-none-elf-gcc-15.2.0-1-darwin-x64.tar.gz
tar -xzf xpack-riscv-none-elf-gcc-15.2.0-1-darwin-x64.tar.gz
```

Rồi trong repo:

```bash
python3 -m venv .venv
.venv/bin/pip install numpy pyserial
```

**Không cần** `pip install apycula`: `gowin_pack` đã có trong OSS CAD Suite.

Phiên bản chính xác của mọi công cụ: `env/VERSIONS.md`.

## 2. Mỗi phiên làm việc

```bash
source env/setup_env.sh
```

Script này export PATH cho ba bộ công cụ, đặt các biến dùng chung
(`TN20K_DEVICE`, `TN20K_FAMILY`, `TN20K_BOARD`, `TN20K_FREQ`, `TN20K_CST`), và **tự xử lý lỗi libc++
của Command Line Tools** (xem mục 6 của báo cáo) bằng cách đặt `TN20K_CXX_INC`.

Kiểm nhanh môi trường và kit:

```bash
yosys -V && nextpnr-himbaechel --version && openFPGALoader -V
openFPGALoader --detect -b tangnano20k      # phải thấy idcode 0x81b, model GW2A(R)-18(C)
ls /dev/cu.usbserial*                        # hai cổng: ...170 = JTAG, ...171 = UART
```

---

## 3. Chạy lại từng cổng

Mọi Makefile đều có các đích `sim`, `build`, `load`, `check`, `clean`.
**`load` chỉ nạp SRAM** (`openFPGALoader -b tangnano20k`), không bao giờ ghi flash.
`check` thu kết quả và lưu vật phẩm + manifest SHA256 vào `results/feasibility/F<n>/`.

| Cổng | Lệnh | Thời gian | Cần người |
|---|---|---|---|
| F1 Blinky | `cd feasibility/F1_blinky && make sim build load check` | ~1 phút | **có** — xem 6 LED có đếm nhị phân, LED0 nháy ~1 Hz |
| F2 UART | `cd feasibility/F2_uart && make sim build load uartcheck check` | ~2 phút | không |
| F3 BSRAM | `cd feasibility/F3_bsram && make pattern sim build load f3check check` | ~5 phút | không |
| F4 DSP | `cd feasibility/F4_dsp && make sim build check` rồi với từng biến thể `make load-prm f4check-prm` | ~12 phút | không |
| F5 SoC | `cd feasibility/F5_soc && make fw sim build load f5check check` | ~6 phút | không |
| F6 Đo lường | `cd feasibility/F6_measure && make fw sim build` rồi `make cycle RUN=1` | ~6 phút | **có** nếu làm điều kiện 4 |

Ghi chú từng cổng:

- **F2**: `make uartcheck` dùng khối 64 byte. `make uartcheck-sweep` chạy thêm phần quét ngưỡng
  kích thước khối (chậm, ~4 phút) — kết quả: khối ≤ 66 byte nguyên vẹn, ≥ 67 byte mất byte.
- **F3**: `make pattern` sinh `pattern.hex` (64 KB) và in CRC32 kỳ vọng. `f3_check.py` **không**
  hard-code CRC, nó gọi lại `scripts/gen_pattern.py` để tự tính.
  Muốn làm lại phép phản chứng: `python3 ../../scripts/gen_pattern.py --out pattern.hex --seed 0x13572468`
  rồi build lại và `python3 ../../scripts/f3_check.py --seed 0x13572468`.
- **F4**: bốn biến thể dùng **chung một `top.v`**, khác nhau bằng cờ build:
  `build-dsp` (yosys suy luận), `build-dsp18`, `build-prm` (gọi MULT18X18 trực tiếp — **đúng**),
  `build-lut` (`-nodsp` — **đúng**). `make check` sinh bảng so sánh ở
  `results/feasibility/F4/comparison.md`.
- **F5/F6**: firmware build bằng `riscv-none-elf-gcc`, chuyển sang hex 32 bit bằng
  `scripts/bin2hex.py`, nạp vào BSRAM qua `$readmemh`. **Mỗi lần đổi firmware là phải build lại
  bitstream** (firmware nằm trong nội dung khởi tạo BSRAM), mất ~4 phút.
- **F6 điều kiện 4** (3 lần tắt/bật nguồn): rút cáp USB, chờ ~2 giây, cắm lại, rồi
  `cd feasibility/F6_measure && make cycle RUN=2` (lặp với `RUN=3`, `RUN=4`).
  Số đo cộng dồn vào `results/feasibility/F6/measure.csv`.
- **F6 bài `rdcycleh`**: `make f6check-hi` — chờ ~166 giây (vòng lặp vượt 2³² chu kỳ).

---

## 4. Ba quy tắc build bắt buộc (lý do: mục 4 của báo cáo)

```bash
# 1. PHẢI có -family gw2a (mặc định của synth_gowin là gw1n)
yosys -p "read_verilog top.v; synth_gowin -top top -family gw2a -nodsp -json out.json -setundef"

# 2. PHẢI có -nodsp cho thiết kế có phép nhân mà yosys có thể tự suy luận
#    (DSP do yosys suy luận cho kết quả SAI trên kit — xem mục 4.3 của báo cáo)

# 3. KHÔNG dùng gowin_pack -c (bitstream nén không nạp được)
gowin_pack -d GW2A-18C -o top.fs pnr.json
```

Khối nhân int8 trong thiết kế mới: **gọi trực tiếp `MULT18X18`** theo mẫu trong
`feasibility/F4_dsp/top.v` (phần `ifdef PRIM_MULT`) — chế độ không dấu, toán hạng mở rộng dấu lên
18 bit, đọc `DOUT[17:0]` như số có dấu 18 bit.

---

## 5. Script dùng chung (`scripts/`)

| Script | Việc |
|---|---|
| `pnr_report.py` | đọc `report.json` của nextpnr → bảng tài nguyên + Fmax |
| `archive_gate.sh` | lưu toàn bộ vật phẩm của một cổng vào `results/feasibility/<GATE>/` + `MANIFEST.md` (SHA256 nội dung gốc; file > 512 KB lưu dạng `.gz`) |
| `gen_pattern.py` | sinh mẫu 64 KB cho F3 + CRC32 kỳ vọng (`--seed` để làm phản chứng) |
| `bin2hex.py` | `.bin` → hex từ 32 bit little-endian cho `$readmemh` |
| `uart_check.py` | F2: kiểm UART hai chiều 3 pha, đối chiếu cả bộ đếm trong FPGA |
| `f3_check.py` | F3: đọc CRC từ kit, so với Python tính lại |
| `f4_check.py` | F4: đọc acc từ kit, so với Python tính lại |
| `f5_check.py` | F5: so từng khoá giữa kit và log Verilator |
| `f6_check.py` | F6: kiểm 4 điều kiện + ghi `measure.csv` |
| `f4_table.py` | F4: lập bảng so sánh bốn biến thể |

Hai điểm chung của mọi script đọc UART:
- **Luôn có timeout và luôn đóng cổng** (quy tắc 9 trong `CLAUDE.md`).
- **Giá trị kỳ vọng không hard-code**: script gọi lại chính module Python đã sinh dữ liệu.

---

## 6. Những cái bẫy đã gặp (để không mất thời gian lại)

| Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `FsParser: checksum data is truncated` khi nạp | `gowin_pack -c` | bỏ `-c` |
| Lệnh `MUL` hoặc phép nhân int8 cho số sai **chỉ trên kit**, mô phỏng vẫn đúng | yosys suy luận DSP | `-nodsp`, hoặc gọi `MULT18X18` trực tiếp |
| Verilator: `fatal error: 'cstddef' file not found` | CLT thiếu `usr/include/c++/v1` | `source env/setup_env.sh` (tự đặt `TN20K_CXX_INC`) |
| Script đọc UART thấy dữ liệu của **bitstream cũ** sau khi nạp bitstream mới | driver macOS/FT2232 còn giữ bộ đệm; `reset_input_buffer()` không đủ | đọc bỏ ~1,5 giây trước khi thu (`--drain`) |
| Ngược lại: đọc không thấy gì vì khối dữ liệu đầu **nằm sẵn trong bộ đệm** rồi bị xả mất | xả bộ đệm quá sớm | `--drain 0` (F6) |
| Script treo 12 giây rồi báo không có dữ liệu | thử cổng JTAG `...170` trước | chỉ định `--port /dev/cu.usbserial-20250303171` |
| Mất byte khi host gửi khối lớn xuống FPGA | cầu FT2232 + driver macOS, không phải FPGA | chia khối ghi ≤ 64 byte |
| LED chói mắt | firmware bật cả 6 LED | chính sách hiện tại: **nhiều nhất 1 LED sáng**, tắt hết khi rảnh |

---

## 7. Cấu trúc thư mục

```
CLAUDE.md                     hướng dẫn cho trợ lý AI + quy tắc làm việc
README.md                     giới thiệu ngắn
docs/
  FEASIBILITY_PLAN.md          kế hoạch các cổng F0–F8 (việc cần làm)
  FEASIBILITY_REPORT.md        báo cáo kết quả  <-- tài liệu chính
  HUONG_DAN.md                 tài liệu này
  LOG.md                       nhật ký từng cổng, có cả các lỗi đã gặp
env/
  setup_env.sh                 nạp môi trường
  VERSIONS.md                  phiên bản mọi công cụ + commit hash mã ngoài
hw/tangnano20k.cst            ràng buộc chân, đã đối chiếu 2 nguồn chính thức
rtl/
  picorv32/picorv32.v          lõi RISC-V (commit đã ghim)
  uart/{uart_tx,uart_rx}.v     UART đã kiểm chứng ở F2, dùng lại cho F3, F5–F8
fw/                           firmware của F5 (start.S, link.ld, soc.h, main.c)
feasibility/
  F1_blinky/ F2_uart/ F3_bsram/ F4_dsp/ F5_soc/ F6_measure/
scripts/                      script dùng chung (xem mục 5)
results/feasibility/F<n>/     vật phẩm + log thô + MANIFEST.md
```
