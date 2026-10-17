# F2 — UART hai chiều 115200 8N1 trên Tang Nano 20K
#
# Tham số luồng: xem feasibility/F1_blinky/Makefile (đã đối chiếu Apicula examples/Makefile).
# DIV baud: 27 MHz / 115200 = 234,375 -> DIV = 234 -> baud thực 115.384,62 (+0,1603 %).
#
# Đích: sim build load check uartcheck uartcheck-sweep clean
# Cần: source ../../env/setup_env.sh

TOP        := top
SRC        := top.v uart_tx.v uart_rx.v
TB         := tb_top.v
BUILD      := build
RESULTS    := ../../results/feasibility/F2

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst

.PHONY: all sim build load check uartcheck uartcheck-sweep clean
all: build

# ---------- mô phỏng ----------
sim: $(BUILD)/tb_top.vvp
	@echo "=== Icarus Verilog ==="
	vvp $< 2>&1 | tee $(BUILD)/sim.log
	@grep -q F2_SIM_PASS $(BUILD)/sim.log || (echo "SIM KHONG DAT"; exit 1)

$(BUILD)/tb_top.vvp: $(SRC) $(TB)
	@mkdir -p $(BUILD)
	iverilog -g2012 -o $@ $(TB) $(SRC)

# ---------- tổng hợp / place&route / đóng gói ----------
build: $(BUILD)/$(TOP).fs

$(BUILD)/$(TOP)-synth.json: $(SRC)
	@mkdir -p $(BUILD)
	yosys -l $(BUILD)/yosys.log \
	      -p "read_verilog $(SRC); synth_gowin -top $(TOP) -family $(YOSYS_FAM) -json $@ -setundef"

$(BUILD)/pnr.json: $(BUILD)/$(TOP)-synth.json $(CST)
	nextpnr-himbaechel -l $(BUILD)/nextpnr.log \
	      --json $< --write $@ \
	      --device "$(DEVICE)" \
	      --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) \
	      --report $(BUILD)/report.json

$(BUILD)/$(TOP).fs: $(BUILD)/pnr.json
	# KHÔNG dùng -c (--compress): openFPGALoader v1.1.1 không parse được file .fs nén
	# do apycula 0.35.dev5 sinh ra cho thiết kế F2 ("FsParser: checksum data is truncated",
	# tái lập 2/2 lần). Bản không nén nạp bình thường. Xem docs/LOG.md mục F2.
	gowin_pack -d $(FAMILY) -o $@ $<

# ---------- nạp (CHỈ SRAM, không ghi flash) ----------
load: $(BUILD)/$(TOP).fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a $(BUILD)/load.log

# ---------- kiểm tra qua cổng serial thật ----------
# khối 64 byte = một gói USB. Khối >=67 byte làm cầu FT2232/driver macOS mất byte
# ở chiều FPGA->PC (bộ đếm trong FPGA chứng minh FPGA vẫn nhận/phát đủ). Xem docs/LOG.md.
uartcheck:
	python3 ../../scripts/uart_check.py --bytes 10240 --block 64 \
	        --log $(BUILD)/uart_check.log 2>&1 | tee $(BUILD)/uart_check_stdout.log

# bản chạy kèm quét ngưỡng kích thước khối (chậm, ~4 phút)
uartcheck-sweep:
	python3 ../../scripts/uart_check.py --bytes 10240 --block 64 --sweep \
	        --log $(BUILD)/uart_check_sweep.log 2>&1 | tee $(BUILD)/uart_check_sweep_stdout.log

# ---------- thu kết quả + lưu toàn bộ vật phẩm ----------
check: $(BUILD)/$(TOP).fs
	@mkdir -p $(RESULTS)
	@echo "--- tài nguyên & Fmax (từ report.json) ---"
	@python3 ../../scripts/pnr_report.py $(BUILD)/report.json | tee $(BUILD)/resources.txt
	@ls -l $(BUILD)/$(TOP).fs | awk '{print "bitstream: "$$NF" ("$$5" byte)"}' | tee $(BUILD)/bitstream_size.txt
	@sh ../../scripts/archive_gate.sh F2 $(BUILD)

clean:
	rm -rf $(BUILD)
