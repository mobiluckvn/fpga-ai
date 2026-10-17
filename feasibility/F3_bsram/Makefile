# F3 — BSRAM 64 KB có khởi tạo sẵn nội dung (rủi ro lớn nhất của dự án)
#
# Tham số luồng: như F1/F2 (đã đối chiếu Apicula examples/Makefile), KHÔNG dùng gowin_pack -c.
# UART dùng khối đã kiểm chứng ở F2: ../../rtl/uart/uart_tx.v
#
# Đích: pattern sim build load check f3check clean
# Cần: source ../../env/setup_env.sh

TOP        := top
SRC        := top.v ../../rtl/uart/uart_tx.v
TB         := tb_top.v
HEX        := pattern.hex
BUILD      := build
RESULTS    := ../../results/feasibility/F3

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst

.PHONY: all pattern sim build load check f3check clean
all: build

# ---------- mẫu 64 KB ----------
pattern: $(HEX)

$(HEX):
	python3 ../../scripts/gen_pattern.py --out $(HEX)

# ---------- mô phỏng (đủ 16.384 từ, không rút gọn) ----------
sim: $(BUILD)/tb_top.vvp
	@echo "=== Icarus Verilog (mô phỏng toàn bộ 64 KB) ==="
	vvp $< 2>&1 | tee $(BUILD)/sim.log
	@grep -q F3_SIM_PASS $(BUILD)/sim.log || (echo "SIM KHONG DAT"; exit 1)

$(BUILD)/tb_top.vvp: top.v crc32.v ../../rtl/uart/uart_tx.v $(TB) $(HEX)
	@mkdir -p $(BUILD)
	iverilog -g2012 -I. -o $@ $(TB) $(SRC)

# ---------- tổng hợp / place&route / đóng gói ----------
build: $(BUILD)/$(TOP).fs

$(BUILD)/$(TOP)-synth.json: top.v crc32.v ../../rtl/uart/uart_tx.v $(HEX)
	@mkdir -p $(BUILD)
	yosys -l $(BUILD)/yosys.log \
	      -p "read_verilog -I. $(SRC); synth_gowin -top $(TOP) -family $(YOSYS_FAM) -json $@ -setundef"

$(BUILD)/pnr.json: $(BUILD)/$(TOP)-synth.json $(CST)
	nextpnr-himbaechel -l $(BUILD)/nextpnr.log \
	      --json $< --write $@ \
	      --device "$(DEVICE)" \
	      --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) \
	      --report $(BUILD)/report.json

$(BUILD)/$(TOP).fs: $(BUILD)/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

# ---------- nạp (CHỈ SRAM, không ghi flash) ----------
load: $(BUILD)/$(TOP).fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a $(BUILD)/load.log

# ---------- đọc CRC từ kit và so với Python ----------
f3check:
	python3 ../../scripts/f3_check.py --log $(BUILD)/f3_check.log 2>&1 | tee $(BUILD)/f3_check_stdout.log

# ---------- thu kết quả + lưu toàn bộ vật phẩm ----------
check: $(BUILD)/$(TOP).fs
	@mkdir -p $(RESULTS)
	@echo "--- tài nguyên & Fmax ---"
	@python3 ../../scripts/pnr_report.py $(BUILD)/report.json | tee $(BUILD)/resources.txt
	@ls -l $(BUILD)/$(TOP).fs | awk '{print "bitstream: "$$NF" ("$$5" byte)"}' | tee $(BUILD)/bitstream_size.txt
	@python3 ../../scripts/gen_pattern.py --out $(BUILD)/pattern_check.hex > $(BUILD)/pattern_info.txt
	@cmp -s $(HEX) $(BUILD)/pattern_check.hex && echo "pattern.hex tái lập đúng" || echo "CẢNH BÁO: pattern.hex khác bản sinh lại"
	@sh ../../scripts/archive_gate.sh F3 $(BUILD) $(HEX)

clean:
	rm -rf $(BUILD)
